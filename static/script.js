document.addEventListener('DOMContentLoaded', () => {
    const quizArea = document.getElementById('quiz-area');
    const questionEl = document.getElementById('question');
    const userAnswerEl = document.getElementById('user-answer');
    const keypad = document.getElementById('keypad');
    const submitBtn = document.getElementById('submit-btn');

    const resultArea = document.getElementById('result-area');
    const resultMessageEl = document.getElementById('result-message');
    const nextBtn = document.getElementById('next-btn');

    const summaryArea = document.getElementById('summary-area');
    const summaryTextEl = document.getElementById('summary-text');
    const restartBtn = document.getElementById('restart-btn');

    let config = {};
    let currentQuestion = {};
    let questions = [];
    let questionCount = 0;
    let totalQuestions = 0;

    // キーパッド生成
    const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '余り', '⌫'];
    keys.forEach(key => {
        const button = document.createElement('button');
        button.textContent = key;
        button.addEventListener('click', () => onKeyClick(key));
        keypad.appendChild(button);
    });

    function onKeyClick(key) {
        if (key === '⌫') {
            userAnswerEl.value = userAnswerEl.value.slice(0, -1);
        } else {
            userAnswerEl.value += key;
        }
    }

    async function fetchConfig() {
        const response = await fetch('/config');
        config = await response.json();
        totalQuestions = config.num_questions;
    }

    async function getNewQuestion() {
        const response = await fetch('/generate_question', { method: 'POST' });
        currentQuestion = await response.json();
        questionEl.textContent = currentQuestion.question;
        userAnswerEl.value = '';
        questionCount++;
        updateUiForNewQuestion();
    }

    function updateUiForNewQuestion() {
        quizArea.style.display = 'block';
        resultArea.style.display = 'none';
        summaryArea.style.display = 'none';
        questionEl.textContent = `第${questionCount}問: ${currentQuestion.question}`;
    }

    function showResult(isCorrect, correctAnswer) {
        quizArea.style.display = 'none';
        resultArea.style.display = 'block';
        let message = isCorrect ? '正解！' : `不正解... 正解は ${correctAnswer} です`;
        resultMessageEl.textContent = message;
    }

    function showSummary() {
        quizArea.style.display = 'none';
        resultArea.style.display = 'none';
        summaryArea.style.display = 'block';

        const correctCount = questions.filter(q => q.isCorrect).length;
        const accuracy = (correctCount / questions.length) * 100;
        summaryTextEl.textContent = `全${questions.length}問中、${correctCount}問正解でした。正答率: ${accuracy.toFixed(1)}%`;
    }

    submitBtn.addEventListener('click', () => {
        const userAnswer = userAnswerEl.value;
        let isCorrect = false;
        let correctAnswerText = '';

        if (config.question_type === '割り算') {
            const [quotient, remainder] = userAnswer.split('余り').map(Number);
            const { quotient: correctQuotient, remainder: correctRemainder } = currentQuestion.answer;
            isCorrect = (quotient === correctQuotient && remainder === correctRemainder);
            correctAnswerText = `${correctQuotient} 余り ${correctRemainder}`;
        } else {
            isCorrect = (Number(userAnswer) === currentQuestion.answer);
            correctAnswerText = currentQuestion.answer;
        }

        questions.push({ ...currentQuestion, userAnswer, isCorrect });
        showResult(isCorrect, correctAnswerText);
    });

    nextBtn.addEventListener('click', () => {
        if (questionCount < totalQuestions) {
            getNewQuestion();
        } else {
            showSummary();
        }
    });

    restartBtn.addEventListener('click', () => {
        questionCount = 0;
        questions = [];
        getNewQuestion();
    });

    // 初期化
    async function init() {
        await fetchConfig();
        await getNewQuestion();
    }

    init();
});
