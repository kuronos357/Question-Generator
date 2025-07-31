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
DEBUG = config.get('DEBUG', False)
QUESTION_TYPE = config.get('TYPE', '掛け算')
LOG_FILE = os.path.join(os.path.dirname(config_path), config.get('LOG_FILE', 'activity_log.json'))
NUM_DIGITS = config.get('NUM_DIGITS', 3)
ADD_QUESTIONS_ON_MISTAKE = config.get('ADD_QUESTIONS_ON_MISTAKE', 1)
NUM_QUESTIONS = config.get('NUM_QUESTIONS', 10)
MAX_QUESTIONS = config.get('MAX_QUESTIONS', 100)

# Notion API設定
HEADERS = {
    'Notion-Version': '2022-06-28',
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Content-Type': 'application/json',
}
URL_PAGES = 'https://api.notion.com/v1/pages'
URL_DATABASE = 'https://api.notion.com/v1/databases'

class QuizApp:
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

    def custom_keypad_dialog(self, title, question, show_r_button=False):
        """数値入力ダイアログ"""
        answer = []
        user_input = None

        def on_char_click(char):
            answer.append(char)
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
        # 最後の行を動的に設定
        last_row = ['余り'] if show_r_button else []
        buttons.append(tuple(last_row))
        
        for row_idx, row in enumerate(buttons):
            # カラム数を動的に取得して中央揃えにする
            frame = tk.Frame(btn_frame)
            frame.grid(row=row_idx, column=0, columnspan=4) # columnspanは最大ボタン数に合わせる

            for col_idx, btn_text in enumerate(row):
                cmd = None
                if btn_text == '⌫':
                    cmd = on_backspace
                elif btn_text == 'OK':
                    cmd = on_submit
                else: # 数字または'R'
                    cmd = lambda char=btn_text: on_char_click(char)
                
                tk.Button(frame, text=btn_text, command=cmd, width=5, height=2, 
                         font=('Helvetica', 14)).grid(row=0, column=col_idx, padx=5, pady=5)

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
            response.raise_for_status() # エラーがあれば例外を発生させる
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Notion API エラー: {e}")
            if e.response:
                print(f"レスポンス: {e.response.text}")
            return None
        except Exception as e:
            print(f"Notion リクエストエラー: {e}")
            return None

    def create_database(self, parent_page_id, question_type):
        """子データベース作成"""
        properties = {
            "問題番号": {"title": {}},
            "問題": {"rich_text": {}},
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

        if question_type == "割り算":
            properties.update({
                "正答(商)": {"number": {"format": "number"}},
                "正答(余)": {"number": {"format": "number"}},
                "回答(商)": {"number": {"format": "number"}},
                "回答(余)": {"number": {"format": "number"}},
            })
        else: # 掛け算
            properties.update({
                "正答": {"number": {"format": "number"}},
                "回答": {"number": {"format": "number"}},
            })

        database_data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "個別の問題"}}],
            "properties": properties
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
            properties = {
                "問題番号": {'title': [{'text': {'content': str(idx + 1)}}]},
                '問題': {'rich_text': [{'text': {'content': q['question']}}]},
                "時間": {"number": q['time']},
                "正誤判定": {"select": {"name": q['judge']}},
            }

            if q['type'] == "割り算":
                properties.update({
                    "正答(商)": {"number": q['correct_quotient']},
                    "正答(余)": {"number": q['correct_remainder']},
                    "回答(商)": {"number": q['user_quotient']},
                    "回答(余)": {"number": q['user_remainder']},
                })
            else: # 掛け算
                properties.update({
                    '正答': {"number": q['correct_answer']},
                    '回答': {"number": q['user_answer']},
                })

            question_data = {
                'parent': {'database_id': 'PLACEHOLDER'},
                'properties': properties
            }
            questions.append(question_data)
        
        return {
            'main_page': main_page, 
            'questions': questions,
            'question_type': QUESTION_TYPE
        }

    def upload_session(self, session_data):
        """単一セッションをNotionにアップロード"""
        # メインページ作成
        main_page_result = self.notion_request(URL_PAGES, session_data['main_page'])
        if not main_page_result:
            return False
        
        # データベース作成
        database_id = self.create_database(main_page_result['id'], session_data['question_type'])
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
        
        sessions_to_process = list(buffer_data.keys())
        uploaded_keys = []
        failed_keys = []

        for session_key in sessions_to_process:
            session_data = buffer_data[session_key]
            print(f"アップロード中: {session_key}")
            if self.upload_session(session_data):
                uploaded_keys.append(session_key)
                print(f"✓ 成功: {session_key}")
            else:
                failed_keys.append(session_key)
                print(f"✗ 失敗: {session_key}")
        
        # 成功したセッションをバッファから削除
        current_buffer = self.file_operation('load')
        for key in uploaded_keys:
            if key in current_buffer:
                del current_buffer[key]
        
        # バッファ更新
        if current_buffer:
            self.file_operation('save', current_buffer)
        else:
            self.file_operation('delete')
            print("バッファファイルを削除しました")
        
        total_sessions = len(sessions_to_process)
        if total_sessions > 0:
            success_rate = len(uploaded_keys) / total_sessions
            print(f"アップロード結果: {len(uploaded_keys)}/{total_sessions} セッション ({success_rate:.1%})")
        
        return not failed_keys

    def generate_problems(self, count=NUM_QUESTIONS):
        """問題生成・実行"""
        self.questions = []
        i = 0
        
        while i < count:
            # 問題生成
            X = int(''.join([str(random.randint(1, 9)) for _ in range(NUM_DIGITS)]))
            Y = int(''.join([str(random.randint(1, 9)) for _ in range(NUM_DIGITS)]))
            R = random.randint(1, X - 1)
            Z = X * Y + R
            start_time = time.time()
            
            if DEBUG:
                print(f"デバッグ: X={X}, Y={Y}, R={R}, 残り={count-i}, タイプ={QUESTION_TYPE}")

            is_correct = False
            question_data = {'type': QUESTION_TYPE}
            display_correct_answer = ""

            if QUESTION_TYPE == "掛け算":
                question = f"残り問題数：{count-i}問題: {X} × {Y}+{R} = ?"
                user_answer_str = self.custom_keypad_dialog("掛け算問題", question)
                user_answer = self.safe_int(user_answer_str)
                
                is_correct = (Z == user_answer)
                
                question_data.update({
                    'question': f'{X} × {Y}',
                    'correct_answer': Z,
                    'user_answer': user_answer,
                })
                display_correct_answer = Z

            elif QUESTION_TYPE == "割り算":
                
                question = f"残り問題数：{count-i}問題: {Z} ÷ {X} = ? 余り ?"
                user_input_str = self.custom_keypad_dialog("割り算問題", question, show_r_button=True)
                
                user_quotient, user_remainder = 0, 0
                if user_input_str:
                    if '余り' in user_input_str:
                        parts = user_input_str.split('余り', 1)
                        user_quotient = self.safe_int(parts[0])
                        user_remainder = self.safe_int(parts[1]) if len(parts) > 1 and parts[1] else 0
                    else:
                        user_quotient = self.safe_int(user_input_str)

                is_correct = (Y == user_quotient and R == user_remainder)

                question_data.update({
                    'question': f'{Z} ÷ {X}',
                    'correct_quotient': Y,
                    'correct_remainder': R,
                    'user_quotient': user_quotient,
                    'user_remainder': user_remainder,
                })
                display_correct_answer = f"{Y} 余り {R}"

            elapsed_time = time.time() - start_time
            judge = "正解" if is_correct else "誤解"
            result_msg = f"{judge} {elapsed_time:.2f}秒"
            
            if not is_correct:
                result_msg += f"\n正解: {display_correct_answer}"
                if ADD_QUESTIONS_ON_MISTAKE > 0:
                    count += ADD_QUESTIONS_ON_MISTAKE
                    result_msg += f"\n({ADD_QUESTIONS_ON_MISTAKE}問追加されました)"

            messagebox.showinfo("結果", result_msg)
            
            question_data['time'] = elapsed_time
            question_data['judge'] = judge
            self.questions.append(question_data)
            
            if is_correct:
                i += 1
        
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def run(self):
        """メイン実行"""
        print("=== 計算問題アプリ開始 ===")
        if DEBUG:
            print("デバッグモード: 有効")
            print(f"問題種: {QUESTION_TYPE}")
            print(f"桁数: {NUM_DIGITS}")
            print(f"間違い時の追加問題数: {ADD_QUESTIONS_ON_MISTAKE}")
            print(f"ログファイル: {LOG_FILE}")
            print(f"Notion APIキー: {'*' * 8}")
            print(f"データベースID: {DATABASE_ID}")
            print("設定ファイル:", config_path)
        
        # 1. 問題実行
        session_key = self.generate_problems()
        if not self.questions: # 問題が生成されなかった場合
            print("問題がキャンセルされたか、生成されませんでした")
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
    app = QuizApp()
    app.run()

if __name__ == "__main__":
    main()