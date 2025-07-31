document.addEventListener('DOMContentLoaded', () => {
    // UI要素の取得
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

    // 状態変数
    let config = {};
    let currentQuestion = {};
    let sessionResults = []; // セッション全体の回答を保存
    let questionCount = 0; // 現在の問題番号
    let totalQuestions = 0; // 総問題数
    let startTime = 0; // 問題開始時間

    // --- キーパッド生成 ---
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

    // --- アプリケーションロジック ---

    async function fetchConfig() {
        const response = await fetch('/config');
        config = await response.json();
        totalQuestions = config.num_questions;
    }

    async function getNewQuestion() {
        const response = await fetch('/generate_question', { method: 'POST' });
        currentQuestion = await response.json();
        questionCount++;
        updateUiForNewQuestion();
        startTime = Date.now(); // 問題表示と同時に時間計測開始
    }

    function handleAnswer() {
        const elapsedTime = (Date.now() - startTime) / 1000; // 秒単位で計算
        const userAnswer = userAnswerEl.value;
        let isCorrect = false;
        let correctAnswerText = '';
        let resultForNotion = { ...currentQuestion, time: elapsedTime, question_number: questionCount };

        if (config.question_type === '割り算') {
            const parts = userAnswer.split('余り');
            const userQuotient = parts[0] ? parseInt(parts[0], 10) : 0;
            const userRemainder = parts[1] ? parseInt(parts[1], 10) : 0;
            const { correct_quotient, correct_remainder } = currentQuestion;
            
            isCorrect = (userQuotient === correct_quotient && userRemainder === correct_remainder);
            correctAnswerText = `${correct_quotient} 余り ${correct_remainder}`;
            
            resultForNotion.user_quotient = userQuotient;
            resultForNotion.user_remainder = userRemainder;

        } else { // 掛け算
            const userAnswerNum = parseInt(userAnswer, 10) || 0;
            isCorrect = (userAnswerNum === currentQuestion.correct_answer);
            correctAnswerText = currentQuestion.correct_answer;
            resultForNotion.user_answer = userAnswerNum;
        }

        resultForNotion.judge = isCorrect ? '正解' : '誤解';
        sessionResults.push(resultForNotion);

        if (!isCorrect && config.add_questions_on_mistake > 0) {
            resultMessageEl.textContent = `不正解... 正解は ${correctAnswerText} です。(${config.add_questions_on_mistake}問追加)`;
        } else {
            resultMessageEl.textContent = isCorrect ? '正解！' : `不正解... 正解は ${correctAnswerText} です`;
        }
        
        showResult();
    }

    async function finishSession() {
        showSummary();
        const payload = {
            question_type: config.question_type,
            questions: sessionResults
        };

        try {
            const response = await fetch('/submit_session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (result.success) {
                summaryTextEl.textContent += '\nNotionへのアップロードがスケジュールされました。';
            } else {
                summaryTextEl.textContent += '\nNotionへのアップロードに失敗しました。データはサーバーに保存され、次回再試行されます。';
            }
        } catch (error) {
            console.error('Error submitting session:', error);
            summaryTextEl.textContent += '\nサーバーとの通信に失敗しました。';
        }
    }

    // --- UI更新関数 ---

    function updateUiForNewQuestion() {
        quizArea.style.display = 'block';
        resultArea.style.display = 'none';
        summaryArea.style.display = 'none';
        questionEl.textContent = `第${questionCount}問 / 全${totalQuestions}問: ${currentQuestion.display_question}`;
        userAnswerEl.value = '';
    }

    function showResult() {
        quizArea.style.display = 'none';
        resultArea.style.display = 'block';
    }

    function showSummary() {
        quizArea.style.display = 'none';
        resultArea.style.display = 'none';
        summaryArea.style.display = 'block';

        const correctCount = sessionResults.filter(q => q.judge === '正解').length;
        const accuracy = (correctCount / sessionResults.length) * 100;
        const totalTime = sessionResults.reduce((sum, q) => sum + q.time, 0);
        const avgTime = totalTime / sessionResults.length;

        summaryTextEl.textContent = `全${sessionResults.length}問中、${correctCount}問正解でした。\n正答率: ${accuracy.toFixed(1)}%\n平均解答時間: ${avgTime.toFixed(2)}秒`;
    }

    // --- イベントリスナー ---

    submitBtn.addEventListener('click', handleAnswer);
    nextBtn.addEventListener('click', () => {
        if (questionCount < totalQuestions) {
            getNewQuestion();
        } else {
            finishSession();
        }
    });
    restartBtn.addEventListener('click', () => {
        // 状態をリセットして再開
        sessionResults = [];
        questionCount = 0;
        init();
    });

    // --- 初期化 ---
    async function init() {
        await fetchConfig();
        await getNewQuestion();
    }

    init();
});