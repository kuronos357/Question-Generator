import random
import requests
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import os
from notion_client import Client
import json

# Tkinterウィンドウを非表示にしておく
root = tk.Tk()
root.withdraw()

current_date = datetime.now().strftime('%Y-%m-%d')

NOTION_API_KEY = 'secret_MBZIR3ot9FCM0oZycKCpb2TKB5pyZuIOtZGL2rEhvSM'
DATABASE_ID = '10f5e314fd47808384fdfb936d00001b'

log_file = "python/問題生成/計算/ログ/log.json"
debug = False  # デバッグモードを有効にするかどうか
totalNumber = 0
Question = []

url = 'https://api.notion.com/v1/pages'
url_create_db = 'https://api.notion.com/v1/databases'

headers = {
    'Notion-Version': '2022-06-28',
    'Authorization': 'Bearer ' + NOTION_API_KEY,
    'Content-Type': 'application/json',
}

def custom_keypad_dialog(title, question):
    answer = []
    remainder = []

    def on_number_click(num):
        if entry_focus.get() == "answer":
            answer.append(num)
            entry_var.set(''.join(answer))
        elif entry_focus.get() == "remainder":
            remainder.append(num)
            remainder_var.set(''.join(remainder))

    def on_backspace():
        if entry_focus.get() == "answer" and answer:
            answer.pop()
            entry_var.set(''.join(answer))
        elif entry_focus.get() == "remainder" and remainder:
            remainder.pop()
            remainder_var.set(''.join(remainder))

    def on_submit():
        nonlocal user_input, user_remainder
        user_input = ''.join(answer)
        user_remainder = ''.join(remainder)
        keypad.destroy()

    def switch_focus_to_answer():
        entry_focus.set("answer")

    def switch_focus_to_remainder():
        entry_focus.set("remainder")

    user_input = None
    user_remainder = None

    keypad = tk.Toplevel()
    keypad.title(title)
    keypad.geometry('600x700')
    keypad.attributes('-topmost', True)

    question_label = tk.Label(keypad, text=question, font=('Helvetica', 14))
    question_label.pack(pady=10)

    entry_focus = tk.StringVar(value="answer")

    entry_var = tk.StringVar()
    entry = tk.Entry(keypad, textvariable=entry_var, font=('Helvetica', 18), justify='right')
    entry.pack(pady=10)

    answer_focus_button = tk.Button(keypad, text="商を入力", command=switch_focus_to_answer, font=('Helvetica', 12))
    answer_focus_button.pack(pady=5)

    remainder_label = tk.Label(keypad, text="余り:", font=('Helvetica', 14))
    remainder_label.pack(pady=5)

    remainder_var = tk.StringVar()
    remainder_entry = tk.Entry(keypad, textvariable=remainder_var, font=('Helvetica', 18), justify='right')
    remainder_entry.pack(pady=10)

    remainder_focus_button = tk.Button(keypad, text="余りを入力", command=switch_focus_to_remainder, font=('Helvetica', 12))
    remainder_focus_button.pack(pady=5)

    btn_frame = tk.Frame(keypad)
    btn_frame.pack()

    buttons = [
        ('7', lambda: on_number_click('7')),
        ('8', lambda: on_number_click('8')),
        ('9', lambda: on_number_click('9')),
        ('4', lambda: on_number_click('4')),
        ('5', lambda: on_number_click('5')),
        ('6', lambda: on_number_click('6')),
        ('1', lambda: on_number_click('1')),
        ('2', lambda: on_number_click('2')),
        ('3', lambda: on_number_click('3')),
        ('0', lambda: on_number_click('0')),
        ('⌫', on_backspace),
        ('OK', on_submit)
    ]

    for idx, (text, command) in enumerate(buttons):
        btn = tk.Button(btn_frame, text=text, command=command, width=5, height=2, font=('Helvetica', 14))
        btn.grid(row=idx // 3, column=idx % 3, padx=5, pady=5)

    keypad.grab_set()
    root.wait_window(keypad)

    return user_input, user_remainder

def load_buffer_data():
    """バッファ（JSON）データを読み込む"""
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        else:
            return {}
    except Exception as e:
        print(f"バッファ読み込みエラー: {e}")
        return {}

def save_to_buffer(session_key, session_data):
    """セッションデータをバッファ（JSON）に保存"""
    try:
        # 既存データを読み込み
        buffer_data = load_buffer_data()
        
        # 新しいセッションデータを追加
        buffer_data[session_key] = session_data
        
        # ファイルに保存
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'w', encoding='utf-8') as file:
            json.dump(buffer_data, file, indent=4, ensure_ascii=False)
        
        print(f"バッファに保存: {session_key}")
        return True
    except Exception as e:
        print(f"バッファ保存エラー: {e}")
        return False

def create_database_in_notion(parent_page_id):
    """Notionに子データベースを作成"""
    database_data = {
        "parent": {"page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "個別の問題"}}],
        "properties": {
            "問題番号": {"title": {}},
            "問題": {"rich_text": {}},
            "正答": {"number": {"format": "number"}},
            "回答": {"number": {"format": "number"}},
            "余り正答": {"number": {"format": "number"}},
            "余り回答": {"number": {"format": "number"}},
            "時間": {"number": {"format": "number"}},
            "正誤判定": {
                "select": {
                    "options": [
                        {"name": "正解", "color": "green"},
                        {"name": "誤解", "color": "red"},
                    ]
                }
            },
        }
    }

    try:
        response = requests.post(url_create_db, headers=headers, json=database_data)
        
        if response.status_code == 200:
            database_id = response.json()['id']
            print(f"データベース作成成功: {database_id}")
            return database_id
        else:
            print(f"データベース作成失敗: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"データベース作成エラー: {e}")
        return None

def upload_session_to_notion(session_key, session_data):
    """セッションデータをNotionにアップロード"""
    try:
        print(f"Notionアップロード開始: {session_key}")
        
        # メインページを作成
        main_page_data = session_data['main_page']
        response = requests.post(url, headers=headers, json=main_page_data)
        
        if response.status_code != 200:
            print(f"メインページ作成失敗: {response.status_code} - {response.text}")
            return False
        
        main_page_id = response.json()['id']
        print(f"メインページ作成成功: {main_page_id}")
        
        # 子データベースを作成
        database_id = create_database_in_notion(main_page_id)
        if not database_id:
            return False
        
        # 個別問題データをアップロード
        questions_data = session_data['questions']
        success_count = 0
        
        for i, question_data in enumerate(questions_data):
            # データベースIDを設定
            question_data['parent']['database_id'] = database_id
            
            try:
                response = requests.post(url, headers=headers, json=question_data)
                if response.status_code == 200:
                    success_count += 1
                    print(f"問題 {i+1}/{len(questions_data)} アップロード完了")
                else:
                    print(f"問題 {i+1} アップロード失敗: {response.status_code}")
                    return False
            except Exception as e:
                print(f"問題 {i+1} アップロードエラー: {e}")
                return False
        
        print(f"全問題アップロード完了: {success_count}/{len(questions_data)}")
        return True
        
    except Exception as e:
        print(f"セッションアップロードエラー: {e}")
        return False

def remove_from_buffer(session_key):
    """アップロード済みセッションをバッファから削除"""
    try:
        buffer_data = load_buffer_data()
        if session_key in buffer_data:
            del buffer_data[session_key]
            with open(log_file, 'w', encoding='utf-8') as file:
                json.dump(buffer_data, file, indent=4, ensure_ascii=False)
            print(f"バッファから削除: {session_key}")
            return True
        return False
    except Exception as e:
        print(f"バッファ削除エラー: {e}")
        return False

def upload_all_from_buffer():
    """バッファ内の全データをNotionにアップロード"""
    buffer_data = load_buffer_data()
    
    if not buffer_data:
        print("バッファにデータがありません")
        return True
    
    print(f"バッファ内のセッション数: {len(buffer_data)}")
    
    upload_success_count = 0
    
    for session_key, session_data in list(buffer_data.items()):
        if session_data is None:
            # 無効なデータは削除
            remove_from_buffer(session_key)
            continue
            
        print(f"\n--- セッション {session_key} アップロード中 ---")
        
        if upload_session_to_notion(session_key, session_data):
            # アップロード成功時にバッファから削除
            if remove_from_buffer(session_key):
                upload_success_count += 1
                print(f"✓ セッション {session_key} 完了")
            else:
                print(f"✗ セッション {session_key} バッファ削除失敗")
        else:
            print(f"✗ セッション {session_key} アップロード失敗 - バッファに保持")
    
    total_sessions = len([k for k, v in buffer_data.items() if v is not None])
    print(f"\n=== アップロード結果 ===")
    print(f"成功: {upload_success_count}/{total_sessions} セッション")
    
    return upload_success_count == total_sessions

def generate_and_process_quiz():
    """問題生成 → バッファ保存 → Notionアップロード → 削除の一連処理"""
    global totalNumber, Question
    
    count = 10
    i = 0
    n = 3
    execution_time = []
    type_name = "割り算"
    done_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    totalNumber = 0
    Question = []

    # 問題実行フェーズ
    while i < count:
        totalNumber += 1
        X = []
        correct_answer = []

        for k in range(n):
            X.append(random.randint(1, 9))
            correct_answer.append(random.randint(1, 9))
        
        X = int(''.join(map(str, X)))
        correct_answer = int(''.join(map(str, correct_answer)))
        R = random.randint(0, X - 1)
        Y = X * correct_answer + R

        print(X, Y, i, totalNumber)
        start_time = time.time()

        if debug:
            type_name = "デバッグ用"
            print(correct_answer, R, "答え、デバッグ用")

        question = f"残り問題数：{count-i}問題: {Y} ÷ {X} = ?"
        user_answer, user_remainder = custom_keypad_dialog("問題", question)

        if user_answer is None or user_answer == '' or user_remainder is None or user_remainder == '':
            messagebox.showinfo("結果", "キャンセルされました。")
            return
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        execution_time.append(elapsed_time)

        if int(correct_answer) == int(user_answer) and int(R) == int(user_remainder) or debug:
            messagebox.showinfo("結果", f"正解 {elapsed_time:.2f}秒")
            judge = "正解"
            i += 1
        else:
            messagebox.showinfo("結果", f"不正解！正解は 商: {correct_answer}, 余り: {R} \n{elapsed_time:.2f}秒")
            judge = "誤解"
        
        Question.append({
            'question': f'{Y} ÷ {X}',
            'correct_answer': correct_answer,
            'user_answer': int(user_answer) if user_answer else 0,
            'correct_remainder': R,
            'user_remainder': int(user_remainder) if user_remainder else 0,
            'time': elapsed_time,
            'judge': judge
        })

    # セッションデータ構築
    session_data = {
        'main_page': {
            'parent': {'database_id': DATABASE_ID},
            'properties': {
                '名前': {
                    'title': [{'text': {'content': done_time}}]
                },
                '経過時間': {
                    'number': sum(execution_time)
                },
                "正答率": {
                    "number": len([q for q in Question if q['judge'] == '正解']) / len(Question)
                },
                "問題数": {
                    "number": len(Question)
                },
                "問題種": {
                    "select": { 
                        "name": type_name
                    }
                }
            }
        },
        'questions': []
    }
    
    # 個別問題データを構築
    for idx, q in enumerate(Question):
        question_data = {
            'parent': {'database_id': 'PLACEHOLDER'},  # 後で置き換える
            'properties': {
                "問題番号": {
                    'title': [{'text': {'content': str(idx + 1)}}]
                },
                '問題': {
                    'rich_text': [{'text': {'content': q['question']}}]
                },
                '正答': {
                    "number": q['correct_answer']
                },
                '回答': {
                    "number": q['user_answer']
                },
                '余り正答': {
                    "number": q['correct_remainder']
                },
                '余り回答': {
                    "number": q['user_remainder']
                },
                "時間": {
                    "number": q['time']
                },
                "正誤判定": {
                    "select": {"name": q['judge']}
                },
            }
        }
        session_data['questions'].append(question_data)
    
    # 結果表示
    average_time = sum(execution_time) / len(execution_time)
    correct_rate = len([q for q in Question if q['judge'] == '正解']) / len(Question)
    
    # 1. バッファ（JSON）に保存
    print("\n=== バッファ保存 ===")
    if not save_to_buffer(done_time, session_data):
        messagebox.showerror("エラー", "バッファ保存に失敗しました")
        return
    
    # 2. バッファ内の全データをNotionにアップロード
    print("\n=== Notionアップロード ===")
    upload_success = upload_all_from_buffer()
    
    # 3. 結果表示
    if upload_success:
        messagebox.showinfo("完了", 
                          f"全ての処理が完了しました\n"
                          f"日付: {done_time}\n"
                          f"平均時間: {average_time:.2f}秒\n"
                          f"正答率: {correct_rate:.1%}")
    else:
        messagebox.showwarning("部分完了", 
                             f"データはバッファに保存されました\n"
                             f"一部のNotionアップロードが失敗しました\n"
                             f"次回実行時に再試行されます\n\n"
                             f"日付: {done_time}\n"
                             f"平均時間: {average_time:.2f}秒\n"
                             f"正答率: {correct_rate:.1%}")

def main():
    """メイン処理"""
    # 最初にバッファ内の未アップロードデータを処理
    print("=== バッファチェック ===")
    buffer_data = load_buffer_data()
    if buffer_data:
        print(f"未アップロードデータ: {len(buffer_data)} セッション")
        print("既存データのアップロードを試行します...")
        upload_all_from_buffer()
    
    # 新しい問題セッションを実行
    print("\n=== 新しい問題セッション ===")
    generate_and_process_quiz()
    
    root.destroy()

if __name__ == "__main__":
    main()