import random
import requests
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import os
import json

# 設定
# スクリプトの場所を基準に設定ファイルを読み込む
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'ログ・設定', 'config.json')

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

NOTION_API_KEY = config['NOTION_API_KEY']
DATABASE_ID = config['DATABASE_ID']
DEBUG = config['DEBUG']
QUESTION_TYPE = config['TYPE']
# ログファイルのパスを絶対パスに変換
LOG_FILE = os.path.join(os.path.dirname(config_path), config['LOG_FILE'])

# Notion API設定
HEADERS = {
    'Notion-Version': '2022-06-28',
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Content-Type': 'application/json',
}
URL_PAGES = 'https://api.notion.com/v1/pages'
URL_DATABASE = 'https://api.notion.com/v1/databases'

class MultiplicationQuizApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.questions = []
        
    def safe_int(self, value):
        """安全な整数変換"""
        return int(value) if value and value.isdigit() else 0
    
    def calculate_stats(self):
        """統計情報を計算"""
        if not self.questions:
            return 0, 0, 0
        
        times = [q['time'] for q in self.questions]
        correct_count = len([q for q in self.questions if q['judge'] == '正解'])
        
        return (
            sum(times) / len(times),  # 平均時間
            correct_count / len(self.questions),  # 正答率
            sum(times)  # 総時間
        )

    def custom_keypad_dialog(self, title, question):
        """数値入力ダイアログ"""
        answer = []
        user_input = None

        def on_number_click(num):
            answer.append(num)
            entry_var.set(''.join(answer))

        def on_backspace():
            if answer:
                answer.pop()
                entry_var.set(''.join(answer))

        def on_submit():
            nonlocal user_input
            user_input = ''.join(answer)
            keypad.destroy()

        keypad = tk.Toplevel()
        keypad.title(title)
        keypad.geometry('500x600')
        keypad.attributes('-topmost', True)

        # UI要素
        tk.Label(keypad, text=question, font=('Helvetica', 14)).pack(pady=10)
        
        entry_var = tk.StringVar()
        tk.Entry(keypad, textvariable=entry_var, font=('Helvetica', 18), justify='right').pack(pady=10)

        # キーパッド
        btn_frame = tk.Frame(keypad)
        btn_frame.pack()
        
        buttons = [
            ('7', '8', '9'),
            ('4', '5', '6'),
            ('1', '2', '3'),
            ('0', '⌫', 'OK')
        ]
        
        for row_idx, row in enumerate(buttons):
            for col_idx, btn_text in enumerate(row):
                if btn_text == '⌫':
                    cmd = on_backspace
                elif btn_text == 'OK':
                    cmd = on_submit
                else:
                    cmd = lambda num=btn_text: on_number_click(num)
                
                tk.Button(btn_frame, text=btn_text, command=cmd, width=5, height=2, 
                         font=('Helvetica', 14)).grid(row=row_idx, column=col_idx, padx=5, pady=5)

        keypad.grab_set()
        self.root.wait_window(keypad)
        return user_input

    def file_operation(self, operation, data=None):
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

    def notion_request(self, url, data):
        """Notion API リクエストの統一処理"""
        try:
            response = requests.post(url, headers=HEADERS, json=data)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Notion API エラー: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Notion リクエストエラー: {e}")
            return None

    def create_database(self, parent_page_id):
        """子データベース作成"""
        database_data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "個別の問題"}}],
            "properties": {
                "問題番号": {"title": {}},
                "問題": {"rich_text": {}},
                "正答": {"number": {"format": "number"}},
                "回答": {"number": {"format": "number"}},
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
        
        result = self.notion_request(URL_DATABASE, database_data)
        return result['id'] if result else None

    def build_session_data(self, session_key):
        """セッションデータ構築"""
        avg_time, correct_rate, total_time = self.calculate_stats()
        type_name = "デバッグ用" if DEBUG else QUESTION_TYPE
        
        # メインページデータ
        main_page = {
            'parent': {'database_id': DATABASE_ID},
            'properties': {
                '名前': {'title': [{'text': {'content': session_key}}]},
                '経過時間': {'number': total_time},
                "正答率": {"number": correct_rate},
                "問題数": {"number": len(self.questions)},
                "問題種": {"select": {"name": type_name}}
            }
        }
        
        # 個別問題データ
        questions = []
        for idx, q in enumerate(self.questions):
            question_data = {
                'parent': {'database_id': 'PLACEHOLDER'},
                'properties': {
                    "問題番号": {'title': [{'text': {'content': str(idx + 1)}}]},
                    '問題': {'rich_text': [{'text': {'content': q['question']}}]},
                    '正答': {"number": q['Z']},
                    '回答': {"number": q['user_answer']},
                    "時間": {"number": q['time']},
                    "正誤判定": {"select": {"name": q['judge']}},
                }
            }
            questions.append(question_data)
        
        return {'main_page': main_page, 'questions': questions}

    def upload_session(self, session_data):
        """単一セッションをNotionにアップロード"""
        # メインページ作成
        main_page_result = self.notion_request(URL_PAGES, session_data['main_page'])
        if not main_page_result:
            return False
        
        # データベース作成
        database_id = self.create_database(main_page_result['id'])
        if not database_id:
            return False
        
        # 個別問題をアップロード
        for question_data in session_data['questions']:
            question_data['parent']['database_id'] = database_id
            if not self.notion_request(URL_PAGES, question_data):
                return False
        
        return True

    def process_buffer(self):
        """バッファ処理"""
        buffer_data = self.file_operation('load')
        if not buffer_data:
            print("バッファは空です")
            return True
        
        print(f"バッファ内のセッション数: {len(buffer_data)}")
        uploaded_sessions = []
        
        for session_key, session_data in buffer_data.items():
            print(f"アップロード中: {session_key}")
            
            if self.upload_session(session_data):
                uploaded_sessions.append(session_key)
                print(f"✓ 成功: {session_key}")
            else:
                print(f"✗ 失敗: {session_key}")
        
        # 成功したセッションを削除
        for session_key in uploaded_sessions:
            del buffer_data[session_key]
        
        # バッファ更新
        if buffer_data:
            self.file_operation('save', buffer_data)
        else:
            self.file_operation('delete')
            print("バッファファイルを削除しました")
        
        success_rate = len(uploaded_sessions) / len(buffer_data) if buffer_data else 1
        print(f"アップロード結果: {len(uploaded_sessions)}/{len(buffer_data)} セッション ({success_rate:.1%})")
        
        return len(buffer_data) == len(uploaded_sessions)

    def generate_problems(self, count=10, digits=3):
        """問題生成・実行"""
        self.questions = []
        i = 0
        
        while i < count:
            # 問題生成 - 既存のロジックを使用
            X = []
            Y = []
            for k in range(digits):
                X.append(random.randint(1, 9))
                Y.append(random.randint(1, 9))
            X = int(''.join(map(str, X)))
            Y = int(''.join(map(str, Y)))
            R= random.randint(1, X)
            Z = X * Y + R
            start_time = time.time()
            
            if DEBUG:
                print(f"デバッグ: {X,Y,Z, count-i,QUESTION_TYPE}問題")

            question = f"残り問題数：{count-i}問題: {X} × {Y} = ?"
            user_answer = self.custom_keypad_dialog("掛け算問題", question)

            if not user_answer:
                messagebox.showinfo("結果", "キャンセルされました。")
                return None
            
            elapsed_time = time.time() - start_time
            
            # 正誤判定
            is_correct = (int(Z) == self.safe_int(user_answer)) or DEBUG
            
            judge = "正解" if is_correct else "誤解"
            result_msg = f"{judge} {elapsed_time:.2f}秒"
            
            if not is_correct:
                result_msg += f"\n正解: {Z}"
            
            messagebox.showinfo("結果", result_msg)
            
            # 問題データ保存
            self.questions.append({
                'question': f'{X} × {Y}',
                'Z': Z,
                'user_answer': self.safe_int(user_answer),
                'time': elapsed_time,
                'judge': judge
            })
            
            if is_correct:
                i += 1
        
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def run(self):
        """メイン実行"""
        print("=== 計算問題アプリ開始 ===")
        
        # 1. 問題実行
        session_key = self.generate_problems()
        if not session_key:
            print("問題がキャンセルされました")
            self.root.destroy()
            return
        
        # 2. バッファ保存
        print("\n=== バッファ保存 ===")
        session_data = self.build_session_data(session_key)
        buffer_data = self.file_operation('load')
        buffer_data[session_key] = session_data
        
        if not self.file_operation('save', buffer_data):
            messagebox.showerror("エラー", "バッファ保存に失敗しました")
            self.root.destroy()
            return
        
        print(f"バッファに保存: {session_key}")
        
        # 3. バッファ処理
        print("\n=== Notionアップロード ===")
        upload_success = self.process_buffer()
        
        # 4. 結果表示
        avg_time, correct_rate, _ = self.calculate_stats()
        
        message = f"日付: {session_key}\n平均時間: {avg_time:.2f}秒\n正答率: {correct_rate:.1%}"
        
        if upload_success:
            messagebox.showinfo("完了", f"全ての処理が完了しました\n{message}")
        else:
            messagebox.showwarning("部分完了", 
                                 f"データはバッファに保存されました\n"
                                 f"一部のNotionアップロードが失敗しました\n"
                                 f"次回実行時に再試行されます\n\n{message}")
        
        self.root.destroy()

def main():
    app = MultiplicationQuizApp()
    app.run()

if __name__ == "__main__":
    main()