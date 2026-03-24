// Quiz session logic
let currentQ = 0;
let answers = [];
let answered = false;

function init() {
    if (questions.length === 0) return;
    showQuestion(0);
}

function showQuestion(index) {
    const q = questions[index];
    answered = false;

    document.getElementById("quiz-question").textContent = q.question;
    document.getElementById("current-q").textContent = index + 1;
    document.getElementById("quiz-feedback").style.display = "none";

    const choicesEl = document.getElementById("quiz-choices");
    choicesEl.innerHTML = "";

    q.choices.forEach(function (choice, i) {
        const btn = document.createElement("button");
        btn.className = "quiz-choice";
        btn.textContent = choice;
        btn.onclick = function () { selectAnswer(i); };
        choicesEl.appendChild(btn);
    });
}

function selectAnswer(choiceIndex) {
    if (answered) return;
    answered = true;
    answers.push(choiceIndex);

    const q = questions[currentQ];
    const isCorrect = choiceIndex === q.answer;

    // Highlight choices
    const choices = document.querySelectorAll(".quiz-choice");
    choices.forEach(function (btn, i) {
        btn.disabled = true;
        if (i === q.answer) {
            btn.classList.add("correct");
        } else if (i === choiceIndex && !isCorrect) {
            btn.classList.add("incorrect");
        }
    });

    // Show feedback
    const feedbackEl = document.getElementById("quiz-feedback");
    const feedbackText = document.getElementById("feedback-text");
    const explanationEl = document.getElementById("quiz-explanation");

    feedbackText.textContent = isCorrect ? "Correct!" : "Incorrect";
    feedbackText.className = isCorrect ? "feedback-correct" : "feedback-incorrect";
    explanationEl.textContent = q.explanation || "";
    feedbackEl.style.display = "block";

    // Update button text for last question
    if (currentQ === questions.length - 1) {
        document.getElementById("next-btn").textContent = "See Results";
    }
}

function nextQuestion() {
    currentQ++;
    if (currentQ < questions.length) {
        showQuestion(currentQ);
    } else {
        submitQuiz();
    }
}

function submitQuiz() {
    fetch(`/lessons/${track}/${topicSlug}/quiz/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers: answers }),
    })
        .then(function (r) { return r.json(); })
        .then(function (data) { showResults(data); });
}

function showResults(data) {
    document.getElementById("quiz-session").style.display = "none";
    document.getElementById("quiz-results").style.display = "block";

    const passed = data.passed;
    document.getElementById("result-icon").textContent = passed ? "✓" : "✗";
    document.getElementById("result-title").textContent = passed ? "Quiz Passed!" : "Not quite...";
    document.getElementById("result-summary").textContent =
        `You got ${data.correct} out of ${data.total} correct.`;

    const actionBtn = document.getElementById("result-action");
    if (passed) {
        actionBtn.textContent = "Continue";
        actionBtn.href = `/lessons/${track}`;
    } else {
        actionBtn.textContent = "Review Lesson & Try Again";
        actionBtn.href = `/lessons/${track}/${topicSlug}`;
    }
}

init();
