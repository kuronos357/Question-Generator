const NOTION_API_KEY = "ここにあなたのAPIキー";
const DATABASE_ID = "ここにあなたのDB ID";

let questions = [];
let currentQuestion = 0;
let startTime = 0;
let totalQuestions = 10;
let totalAttempts = 0;
let results = [];

function generateQuestion() {
    const X = randomNum();
    const Y = randomNum();
    return {X, Y, correct: X * Y};
}

function randomNum() {
    return parseInt([...Array(3)].map(() => Math.floor(Math.random() * 9) + 1).join(''), 10);
}

function showQuestion() {
    if (currentQuestion >= totalQuestions) {
        finishTest();
        return;
    }
    const q = generateQuestion();
    questions.push(q);
    document.getElementById('question').innerText = `問題 ${currentQuestion + 1} / ${totalQuestions}: ${q.X} × ${q.Y}`;
    document.getElementById('answer').value = "";
    startTime = Date.now();
}

function setupKeypad() {
    const keypad = document.getElementById('keypad');
    keypad.innerHTML = "";
    ["7","8","9","4","5","6","1","2","3","0","⌫"].forEach(key => {
        const btn = document.createElement('button');
        btn.textContent = key;
        btn.style.fontSize = "20px";
        btn.onclick = () => {
            if (key === "⌫") {
                document.getElementById('answer').value = document.getElementById('answer').value.slice(0, -1);
            } else {
                document.getElementById('answer').value += key;
            }
        };
        keypad.appendChild(btn);
    });
}

function submitAnswer() {
    const userAns = document.getElementById('answer').value;
    const q = questions[currentQuestion];
    const correct = q.correct;
    const timeTaken = (Date.now() - startTime) / 1000;

    let judge = (parseInt(userAns) === correct) ? "正答" : "誤答";
    alert(judge + (judge === "誤答" ? ` 正解は ${correct}` : ""));

    results.push({
        question: `${q.X} × ${q.Y}`,
        correct: correct,
        user: parseInt(userAns),
        time: timeTaken,
        judge: judge
    });

    totalAttempts++;
    if (judge === "正答") {
        currentQuestion++;
    } else {
        currentQuestion = Math.max(0, currentQuestion - 1);
    }

    showQuestion();
}

async function finishTest() {
    const avgTime = results.reduce((sum, r) => sum + r.time, 0) / results.length;
    alert(`終了！ 平均時間: ${avgTime.toFixed(2)}秒`);

    // Notionへ送信
    await sendSummaryToNotion(avgTime);
    await sendDetailsToNotion();

    window.location.reload();
}

async function sendSummaryToNotion(avgTime) {
    await fetch("https://api.notion.com/v1/pages", {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${NOTION_API_KEY}`,
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        },
        body: JSON.stringify({
            parent: { database_id: DATABASE_ID },
            properties: {
                名前: {
                    title: [{ text: { content: new Date().toISOString() } }]
                },
                経過時間: { number: avgTime },
                問題数: { number: totalQuestions },
                正答率: { number: results.filter(r => r.judge === "正答").length / totalQuestions }
            }
        })
    });
}

async function sendDetailsToNotion() {
    for (const [i, r] of results.entries()) {
        await fetch("https://api.notion.com/v1/pages", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${NOTION_API_KEY}`,
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            },
            body: JSON.stringify({
                parent: { database_id: DATABASE_ID },
                properties: {
                    問題番号: { title: [{ text: { content: (i+1).toString() } }] },
                    問題: { rich_text: [{ text: { content: r.question } }] },
                    正答: { number: r.correct },
                    回答: { number: r.user },
                    時間: { number: r.time },
                    正誤判定: { select: { name: r.judge } }
                }
            })
        });
    }
}

setupKeypad();
showQuestion();
