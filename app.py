from flask import Flask, render_template, jsonify, request
import random
import os
import json
import requests
import time
from datetime import datetime

app = Flask(__name__)

# --- 設定読み込み ---
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'ログ・設定', 'config.json')

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Notion APIキーやDB IDはサーバーサイドでのみ保持
NOTION_API_KEY = config.get('NOTION_API_KEY')
DATABASE_ID = config.get('DATABASE_ID')
LOG_FILE = os.path.join(script_dir, 'ログ・設定', config.get('LOG_FILE', 'log.json'))

# --- Notion API 設定 ---
HEADERS = {
    'Notion-Version': '2022-06-28',
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Content-Type': 'application/json',
}
URL_PAGES = 'https://api.notion.com/v1/pages'
URL_DATABASE = 'https://api.notion.com/v1/databases'

# --- ヘルパー関数 (Question.pyから移植・改良) ---

def file_operation(operation, data=None):
    """ファイル操作の統一処理"""
    try:
        if operation == 'load':
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r', encoding='utf-8') as file:
                    return json.load(file)
            return {}
        elif operation == 'save':
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            with open(LOG_FILE, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            return True
        elif operation == 'delete':
            if os.path.exists(LOG_FILE):
                os.remove(LOG_FILE)
            return True
    except Exception as e:
        print(f"ファイル操作エラー ({operation}): {e}")
        return {} if operation == 'load' else False

def notion_request(url, data):
    """Notion API リクエストの統一処理"""
    try:
        response = requests.post(url, headers=HEADERS, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Notion API エラー: {e}")
        if e.response:
            print(f"レスポンス: {e.response.text}")
        return None

# --- Flask ルート定義 ---

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
        return jsonify({
            'question': f'{X} × {Y}',
            'display_question': question_text,
            'correct_answer': Z,
            'type': question_type
        })
    elif question_type == "割り算":
        question_text = f"{Z} ÷ {X} = ? 余り ?"
        return jsonify({
            'question': f'{Z} ÷ {X}',
            'display_question': question_text,
            'correct_quotient': Y,
            'correct_remainder': R,
            'type': question_type
        })

@app.route('/submit_session', methods=['POST'])
def submit_session():
    """フロントエンドからセッションデータを受け取り、処理する"""
    session_data = request.json
    session_key = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # バッファに保存
    buffer_data = file_operation('load')
    buffer_data[session_key] = session_data
    if not file_operation('save', buffer_data):
        return jsonify({'success': False, 'message': 'バッファ保存に失敗しました'}), 500

    # バッファ処理（Notionへのアップロード）
    upload_success = process_buffer()

    return jsonify({'success': upload_success})

# --- Notion連携ロジック (Question.pyから移植) ---

def process_buffer():
    """バッファを処理してNotionにアップロード"""
    buffer_data = file_operation('load')
    if not buffer_data:
        print("バッファは空です")
        return True

    sessions_to_process = list(buffer_data.keys())
    uploaded_keys = []
    failed_keys = []

    for session_key, session_content in buffer_data.items():
        print(f"アップロード中: {session_key}")
        if upload_single_session(session_key, session_content):
            uploaded_keys.append(session_key)
            print(f"✓ 成功: {session_key}")
        else:
            failed_keys.append(session_key)
            print(f"✗ 失敗: {session_key}")

    # 成功したセッションをバッファから削除
    current_buffer = file_operation('load')
    for key in uploaded_keys:
        if key in current_buffer:
            del current_buffer[key]
    
    if current_buffer:
        file_operation('save', current_buffer)
    else:
        file_operation('delete')

    return not failed_keys

def upload_single_session(session_key, session_content):
    """単一セッションをNotionにアップロード"""
    main_page_data = build_main_page_data(session_key, session_content)
    main_page_result = notion_request(URL_PAGES, main_page_data)
    if not main_page_result:
        return False

    database_id = create_child_database(main_page_result['id'], session_content['question_type'])
    if not database_id:
        return False

    for question_result in session_content['questions']:
        question_page_data = build_question_page_data(database_id, question_result)
        if not notion_request(URL_PAGES, question_page_data):
            return False # 一つでも失敗したら中断
    return True

def build_main_page_data(session_key, session_content):
    """メインページ用のNotionデータを作成"""
    total_time = sum(q['time'] for q in session_content['questions'])
    correct_count = len([q for q in session_content['questions'] if q['judge'] == '正解'])
    correct_rate = correct_count / len(session_content['questions']) if session_content['questions'] else 0

    return {
        'parent': {'database_id': DATABASE_ID},
        'properties': {
            '名前': {'title': [{'text': {'content': session_key}}]}, 
            '経過時間': {'number': total_time},
            '正答率': {'number': correct_rate},
            '問題数': {'number': len(session_content['questions'])},
            '問題種': {'select': {'name': session_content['question_type']}}
        }
    }

def create_child_database(parent_page_id, question_type):
    """子データベース作成"""
    properties = {
        "問題番号": {"title": {}},
        "問題": {"rich_text": {}},
        "時間": {"number": {"format": "number"}},
        "正誤判定": {"select": {"options": [{"name": "正解", "color": "green"}, {"name": "誤解", "color": "red"}]}},
    }
    if question_type == "割り算":
        properties.update({
            "正答(商)": {"number": {"format": "number"}}, "正答(余)": {"number": {"format": "number"}},
            "回答(商)": {"number": {"format": "number"}}, "回答(余)": {"number": {"format": "number"}},
        })
    else:
        properties.update({
            "正答": {"number": {"format": "number"}}, "回答": {"number": {"format": "number"}},
        })
    
    db_data = {
        "parent": {"page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "個別の問題"}}],
        "properties": properties
    }
    result = notion_request(URL_DATABASE, db_data)
    return result['id'] if result else None

def build_question_page_data(database_id, q):
    """個別問題ページ用のNotionデータを作成"""
    properties = {
        "問題番号": {'title': [{'text': {'content': str(q['question_number'])}}]}, 
        '問題': {'rich_text': [{'text': {'content': q['question']}}]}, 
        "時間": {"number": q['time']},
        "正誤判定": {"select": {"name": q['judge']}},
    }
    if q['type'] == "割り算":
        properties.update({
            "正答(商)": {"number": q['correct_quotient']}, "正答(余)": {"number": q['correct_remainder']},
            "回答(商)": {"number": q['user_quotient']}, "回答(余)": {"number": q['user_remainder']},
        })
    else:
        properties.update({
            '正答': {"number": q['correct_answer']}, '回答': {"number": q['user_answer']},
        })
    return {'parent': {'database_id': database_id}, 'properties': properties}

# --- アプリケーション実行 ---
if __name__ == '__main__':
    # 起動時に一度バッファ処理を試みる
    print("サーバー起動時にバッファ処理を実行します...")
    process_buffer()
    print("バッファ処理完了。サーバーを起動します。")
    app.run(debug=True, port=5001)