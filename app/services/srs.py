"""
Spaced Repetition Scheduler — FSRS-inspired algorithm.

Based on the Free Spaced Repetition Scheduler (FSRS) by Jarrett Ye,
which replaced SM-2 in Anki v23+. FSRS uses a stability/difficulty model
that better predicts memory decay than SM-2's ease factor approach.

Key concepts:
- Stability: number of days at which recall probability = 90%
- Difficulty: how hard this card is (0.0 = easy, 1.0 = hard)
- State: new → learning → review → relearning

Research backing:
- FSRS outperforms SM-2 by ~15-20% in prediction accuracy (Ye et al.)
- Stability-based scheduling adapts better to individual card difficulty
- Rating system: 1=Again, 2=Hard, 3=Good, 4=Easy
"""

from datetime import date, timedelta
from math import exp, log

# Card states
NEW = 0
LEARNING = 1
REVIEW = 2
RELEARNING = 3

# Default parameters (tuned from research)
# Initial stability values for each rating on a new card (in days)
INITIAL_STABILITY = {
    1: 0.25,   # Again → review in 6 hours
    2: 0.5,    # Hard → review in 12 hours
    3: 1.0,    # Good → review tomorrow
    4: 4.0,    # Easy → review in 4 days
}

# How much stability grows after a successful review
STABILITY_GROWTH = 1.9  # ~1.9x growth per successful review (research-based)

# Difficulty adjustment factors
DIFFICULTY_DECAY = 0.1
DIFFICULTY_DEFAULT = 0.3


def schedule_review(card, rating: int) -> None:
    """Update a card's scheduling after a review.

    Args:
        card: Card model instance (mutated in place)
        rating: 1=Again, 2=Hard, 3=Good, 4=Easy
    """
    if card.state == NEW:
        _schedule_new(card, rating)
    elif card.state == LEARNING:
        _schedule_learning(card, rating)
    elif card.state == REVIEW:
        _schedule_review(card, rating)
    elif card.state == RELEARNING:
        _schedule_relearning(card, rating)

    card.reps += 1
    from datetime import datetime
    card.last_review = datetime.utcnow()


def _schedule_new(card, rating: int) -> None:
    """Schedule a card being seen for the first time."""
    card.stability = INITIAL_STABILITY[rating]
    card.difficulty = _initial_difficulty(rating)

    if rating == 1:
        card.state = LEARNING
    else:
        card.state = REVIEW

    card.due_date = _next_due(card.stability)


def _schedule_learning(card, rating: int) -> None:
    """Schedule a card that's still in the learning phase."""
    if rating == 1:
        # Failed again — reset stability
        card.stability = INITIAL_STABILITY[1]
        card.state = LEARNING
    elif rating == 2:
        card.stability = max(card.stability, INITIAL_STABILITY[2])
        card.state = LEARNING
    else:
        # Graduated to review
        card.stability = INITIAL_STABILITY[rating]
        card.state = REVIEW

    card.difficulty = _update_difficulty(card.difficulty, rating)
    card.due_date = _next_due(card.stability)


def _schedule_review(card, rating: int) -> None:
    """Schedule a card that's in the review phase."""
    if rating == 1:
        # Lapsed — enter relearning
        card.stability = max(card.stability * 0.2, 0.25)  # Major stability loss
        card.difficulty = _update_difficulty(card.difficulty, rating)
        card.state = RELEARNING
    else:
        # Successful review — grow stability
        growth = _stability_growth(card.stability, card.difficulty, rating)
        card.stability = growth
        card.difficulty = _update_difficulty(card.difficulty, rating)
        card.state = REVIEW

    card.due_date = _next_due(card.stability)


def _schedule_relearning(card, rating: int) -> None:
    """Schedule a card that lapsed and is being relearned."""
    if rating == 1:
        card.stability = INITIAL_STABILITY[1]
        card.state = RELEARNING
    elif rating == 2:
        card.stability = max(card.stability, INITIAL_STABILITY[2])
        card.state = RELEARNING
    else:
        # Graduated back to review
        card.stability = INITIAL_STABILITY[rating]
        card.state = REVIEW

    card.difficulty = _update_difficulty(card.difficulty, rating)
    card.due_date = _next_due(card.stability)


def _initial_difficulty(rating: int) -> float:
    """Set initial difficulty based on first rating."""
    # Higher rating → lower difficulty
    d = DIFFICULTY_DEFAULT - (rating - 3) * 0.15
    return max(0.0, min(1.0, d))


def _update_difficulty(current: float, rating: int) -> float:
    """Adjust difficulty based on review rating.

    Difficulty moves toward what the rating suggests, with decay to prevent
    it from getting stuck at extremes (mean reversion).
    """
    target = _initial_difficulty(rating)
    new_d = current + DIFFICULTY_DECAY * (target - current)
    return max(0.0, min(1.0, new_d))


def _stability_growth(stability: float, difficulty: float, rating: int) -> float:
    """Calculate new stability after a successful review.

    Higher stability cards grow slower (diminishing returns).
    Harder cards grow slower. Easy rating gives bonus growth.
    """
    # Base growth factor decreases as stability increases (log scaling)
    base = STABILITY_GROWTH * (1 + log(1 + stability) * 0.1)

    # Difficulty penalty: harder cards grow stability slower
    difficulty_factor = 1.0 - (difficulty * 0.5)

    # Rating bonus
    rating_factor = {2: 0.8, 3: 1.0, 4: 1.3}[rating]

    new_stability = stability * base * difficulty_factor * rating_factor

    # Cap growth to prevent runaway intervals (max ~365 days)
    return min(new_stability, 365.0)


def _next_due(stability: float) -> date:
    """Convert stability (days) to next due date."""
    days = max(1, round(stability))
    return date.today() + timedelta(days=days)


def get_recall_probability(stability: float, days_elapsed: float) -> float:
    """Estimate probability of recall after days_elapsed since last review.

    Uses the forgetting curve: P(recall) = e^(-t/S)
    where t = time elapsed, S = stability
    """
    if stability <= 0:
        return 0.0
    return exp(-days_elapsed / stability)
