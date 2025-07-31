from flask import Flask, render_template, jsonify, request
import random
import os
import json

app = Flask(__name__)

# スクリプトの場所を基準に設定ファイルを読み込む
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'ログ・設定', 'config.json')

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Notion APIキーはサーバーサイドでのみ使用
NOTION_API_KEY = config.get('NOTION_API_KEY')
DATABASE_ID = config.get('DATABASE_ID')
DEBUG = config.get('DEBUG', False)

@app.route('/')
def index():
    """メインページを表示"""
    return render_template('index.html')

@app.route('/config')
def get_config():
    """フロントエンドに必要な設定を渡す"""
    return jsonify({
        'question_type': config.get('TYPE', '掛け算'),
        'num_digits': config.get('NUM_DIGITS', 3),
        'add_questions_on_mistake': config.get('ADD_QUESTIONS_ON_MISTAKE', 1),
        'num_questions': config.get('NUM_QUESTIONS', 10),
    })

@app.route('/generate_question', methods=['POST'])
def generate_question():
    """新しい問題を生成して返す"""
    num_digits = config.get('NUM_DIGITS', 3)
    question_type = config.get('TYPE', '掛け算')

    X = int(''.join([str(random.randint(1, 9)) for _ in range(num_digits)]))
    Y = int(''.join([str(random.randint(1, 9)) for _ in range(num_digits)]))
    R = random.randint(1, X - 1)
    Z = X * Y + R

    if question_type == "掛け算":
        question_text = f"{X} × {Y} + {R} = ?"
        correct_answer = Z
        return jsonify({
            'question': question_text,
            'answer': correct_answer
        })
    elif question_type == "割り算":
        question_text = f"{Z} ÷ {X} = ? 余り ?"
        return jsonify({
            'question': question_text,
            'answer': {'quotient': Y, 'remainder': R}
        })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
