"""Tests for the FSRS-inspired spaced repetition scheduler."""

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.srs import (
    LEARNING,
    NEW,
    RELEARNING,
    REVIEW,
    _initial_difficulty,
    _stability_growth,
    _update_difficulty,
    get_recall_probability,
    schedule_review,
)


def make_card(**kwargs):
    """Create a mock card with SRS fields."""
    card = MagicMock()
    card.stability = kwargs.get("stability", 0.0)
    card.difficulty = kwargs.get("difficulty", 0.3)
    card.due_date = kwargs.get("due_date", date.today())
    card.last_review = kwargs.get("last_review", None)
    card.reps = kwargs.get("reps", 0)
    card.state = kwargs.get("state", NEW)
    return card


class TestNewCardScheduling:
    def test_good_rating_moves_to_review(self):
        card = make_card()
        schedule_review(card, 3)  # Good
        assert card.state == REVIEW
        assert card.stability == 1.0
        assert card.due_date == date.today() + timedelta(days=1)
        assert card.reps == 1

    def test_again_rating_moves_to_learning(self):
        card = make_card()
        schedule_review(card, 1)  # Again
        assert card.state == LEARNING
        assert card.stability == 0.25
        assert card.reps == 1

    def test_easy_rating_gives_longer_interval(self):
        card = make_card()
        schedule_review(card, 4)  # Easy
        assert card.state == REVIEW
        assert card.stability == 4.0
        assert card.due_date == date.today() + timedelta(days=4)

    def test_hard_rating_moves_to_review(self):
        card = make_card()
        schedule_review(card, 2)  # Hard
        assert card.state == REVIEW
        assert card.stability == 0.5


class TestReviewCardScheduling:
    def test_good_rating_grows_stability(self):
        card = make_card(state=REVIEW, stability=1.0, difficulty=0.3)
        schedule_review(card, 3)
        assert card.stability > 1.0
        assert card.state == REVIEW

    def test_again_rating_causes_lapse(self):
        card = make_card(state=REVIEW, stability=10.0, difficulty=0.3)
        schedule_review(card, 1)
        assert card.state == RELEARNING
        assert card.stability < 10.0  # Major stability loss

    def test_easy_rating_grows_more_than_good(self):
        card_good = make_card(state=REVIEW, stability=5.0, difficulty=0.3)
        card_easy = make_card(state=REVIEW, stability=5.0, difficulty=0.3)
        schedule_review(card_good, 3)
        schedule_review(card_easy, 4)
        assert card_easy.stability > card_good.stability

    def test_hard_cards_grow_slower(self):
        card_easy_d = make_card(state=REVIEW, stability=5.0, difficulty=0.1)
        card_hard_d = make_card(state=REVIEW, stability=5.0, difficulty=0.8)
        schedule_review(card_easy_d, 3)
        schedule_review(card_hard_d, 3)
        assert card_easy_d.stability > card_hard_d.stability

    def test_stability_caps_at_365(self):
        card = make_card(state=REVIEW, stability=300.0, difficulty=0.0)
        schedule_review(card, 4)
        assert card.stability <= 365.0


class TestLearningCardScheduling:
    def test_good_graduates_to_review(self):
        card = make_card(state=LEARNING, stability=0.25)
        schedule_review(card, 3)
        assert card.state == REVIEW

    def test_again_stays_in_learning(self):
        card = make_card(state=LEARNING, stability=0.5)
        schedule_review(card, 1)
        assert card.state == LEARNING
        assert card.stability == 0.25


class TestRelearningCardScheduling:
    def test_good_graduates_back_to_review(self):
        card = make_card(state=RELEARNING, stability=0.5)
        schedule_review(card, 3)
        assert card.state == REVIEW

    def test_again_stays_in_relearning(self):
        card = make_card(state=RELEARNING, stability=0.5)
        schedule_review(card, 1)
        assert card.state == RELEARNING


class TestDifficulty:
    def test_initial_difficulty_easy_is_lower(self):
        assert _initial_difficulty(4) < _initial_difficulty(1)

    def test_difficulty_bounded_0_to_1(self):
        for rating in range(1, 5):
            d = _initial_difficulty(rating)
            assert 0.0 <= d <= 1.0

    def test_update_difficulty_mean_reverts(self):
        # Very hard card getting an easy rating should decrease difficulty
        new_d = _update_difficulty(0.9, 4)
        assert new_d < 0.9

        # Very easy card getting a hard rating should increase difficulty
        new_d = _update_difficulty(0.1, 1)
        assert new_d > 0.1


class TestRecallProbability:
    def test_recall_at_zero_days_is_one(self):
        assert get_recall_probability(10.0, 0.0) == pytest.approx(1.0)

    def test_recall_decreases_over_time(self):
        p_early = get_recall_probability(10.0, 1.0)
        p_late = get_recall_probability(10.0, 20.0)
        assert p_early > p_late

    def test_higher_stability_means_better_recall(self):
        p_low = get_recall_probability(1.0, 5.0)
        p_high = get_recall_probability(10.0, 5.0)
        assert p_high > p_low

    def test_zero_stability_returns_zero(self):
        assert get_recall_probability(0.0, 5.0) == 0.0


class TestStabilityGrowth:
    def test_growth_increases_stability(self):
        new_s = _stability_growth(5.0, 0.3, 3)
        assert new_s > 5.0

    def test_easy_grows_more_than_hard(self):
        easy = _stability_growth(5.0, 0.3, 4)
        hard = _stability_growth(5.0, 0.3, 2)
        assert easy > hard
