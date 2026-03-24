// Flashcard review session logic
let currentIndex = 0;
let isFlipped = false;
let startTime = null;
let sessionStartTime = Date.now();
let results = { again: 0, hard: 0, good: 0, easy: 0 };

const ratingNames = { 1: "again", 2: "hard", 3: "good", 4: "easy" };

function init() {
    if (cards.length === 0) return;
    showCard(0);
}

function showCard(index) {
    const card = cards[index];
    isFlipped = false;
    startTime = Date.now();

    document.getElementById("card-front").textContent = card.front;
    document.getElementById("card-back").textContent = card.back;
    document.getElementById("card-front").style.display = "block";
    document.getElementById("card-back").style.display = "none";
    document.getElementById("rating-buttons").style.display = "none";
    document.getElementById("tap-hint").style.display = "block";
    document.getElementById("current-card").textContent = index + 1;
}

function flipCard() {
    if (isFlipped) return;
    isFlipped = true;

    document.getElementById("card-front").style.display = "none";
    document.getElementById("card-back").style.display = "block";
    document.getElementById("rating-buttons").style.display = "flex";
    document.getElementById("tap-hint").style.display = "none";
}

function rateCard(rating) {
    const card = cards[currentIndex];
    const responseTime = Date.now() - startTime;

    results[ratingNames[rating]]++;

    // Send rating to server
    fetch(`/flashcards/review/${card.id}/rate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            rating: rating,
            response_time_ms: responseTime,
        }),
    });

    currentIndex++;
    if (currentIndex < cards.length) {
        showCard(currentIndex);
    } else {
        showComplete();
    }
}

function showComplete() {
    document.getElementById("review-session").style.display = "none";
    document.getElementById("review-complete").style.display = "block";

    const total = cards.length;
    const durationSec = Math.round((Date.now() - sessionStartTime) / 1000);
    const durationMin = Math.max(1, Math.round(durationSec / 60));
    const summary = `Reviewed ${total} cards in ${durationMin} min: ${results.easy} easy, ${results.good} good, ${results.hard} hard, ${results.again} again`;
    document.getElementById("review-summary").textContent = summary;

    // Record session on server
    fetch(`/flashcards/review/${track}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            cards_reviewed: total,
            duration_sec: durationSec,
        }),
    });
}

// Initialize on load
init();
