

import random
import requests
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import os
import json

class QuizApp:
    def __init__(self, config):
        self.config = config
        self.root = tk.Tk()
        self.root.withdraw()
        self.questions = []
        self.question_type = self.select_question_type()

    def select_question_type(self):
        """GUI to select question type."""
        selection = tk.StringVar()

        def on_select():
            top.destroy()

        top = tk.Toplevel(self.root)
        top.title("問題種別選択")
        top.geometry("300x200")
        top.attributes('-topmost', True)

        tk.Label(top, text="どちらの問題を出題しますか？", font=('Helvetica', 14)).pack(pady=20)

        if self.config.get("generate_multiplication"):
            tk.Radiobutton(top, text="掛け算", variable=selection, value="multiplication", font=('Helvetica', 12)).pack(anchor=tk.W)
        if self.config.get("generate_division"):
            tk.Radiobutton(top, text="割り算", variable=selection, value="division", font=('Helvetica', 12)).pack(anchor=tk.W)

        tk.Button(top, text="決定", command=on_select, font=('Helvetica', 12)).pack(pady=20)

        top.grab_set()
        self.root.wait_window(top)
        return selection.get()

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
        remainder = []
        entry_focus = tk.StringVar(value="answer")
        user_input = None
        user_remainder = None

        def on_number_click(num):
            target = answer if entry_focus.get() == "answer" else remainder
            target.append(num)
            if entry_focus.get() == "answer":
                entry_var.set(''.join(answer))
            else:
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
            if self.question_type == 'division':
                user_remainder = ''.join(remainder)
            keypad.destroy()

        keypad = tk.Toplevel()
        keypad.title(title)
        keypad.attributes('-topmost', True)

        # UI要素
        tk.Label(keypad, text=question, font=('Helvetica', 14)).pack(pady=10)
        
        entry_var = tk.StringVar()
        tk.Entry(keypad, textvariable=entry_var, font=('Helvetica', 18), justify='right').pack(pady=10)

        if self.question_type == 'division':
            keypad.geometry('600x700')
            tk.Button(keypad, text="商を入力", command=lambda: entry_focus.set("answer"), font=('Helvetica', 12)).pack(pady=5)
            
            tk.Label(keypad, text="余り:", font=('Helvetica', 14)).pack(pady=5)
            remainder_var = tk.StringVar()
            tk.Entry(keypad, textvariable=remainder_var, font=('Helvetica', 18), justify='right').pack(pady=10)
            tk.Button(keypad, text="余りを入力", command=lambda: entry_focus.set("remainder"), font=('Helvetica', 12)).pack(pady=5)
        else:
            keypad.geometry('500x600')


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
        return user_input, user_remainder if self.question_type == 'division' else user_input


    def file_operation(self, operation, data=None):
        """ファイル操作の統一処理"""
        log_file = "Project/問題生成/計算/ログ/log.json"
        try:
            if operation == 'load':
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as file:
                        return json.load(file)
                return {}
            
            elif operation == 'save':
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                with open(log_file, 'w', encoding='utf-8') as file:
                    json.dump(data, file, indent=4, ensure_ascii=False)
                return True
            
            elif operation == 'delete':
                if os.path.exists(log_file):
                    os.remove(log_file)
                return True
                
        except Exception as e:
            print(f"ファイル操作エラー ({operation}): {e}")
            return {} if operation == 'load' else False

    def notion_request(self, url, data):
        """Notion API リクエストの統一処理"""
        headers = {
            'Notion-Version': '2022-06-28',
            'Authorization': f'Bearer {self.config["notion_api_key"]}',
            'Content-Type': 'application/json',
        }
        try:
            response = requests.post(url, headers=headers, json=data)
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
        properties = {
                "問題番号": {"title": {}},
                "問題": {"rich_text": {}},
                "正答": {"number": {"format": "number"}},
                "回答": {"number": {"format": "number"}},
                "時間": {"number": {"format": "number"}},
                "正誤判定": {
                    "select": {
                        "options": [
                            {"name": "正解", "color": "green"},
                            {"name": "誤解", "color": "red"}
                        ]
                    }
                }
            }
        if self.question_type == 'division':
            properties["余り正答"] = {"number": {"format": "number"}}
            properties["余り回答"] = {"number": {"format": "number"}}

        database_data = {
            "parent": {"page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "個別の問題"}}],
            "properties": properties
        }
        
        result = self.notion_request('https://api.notion.com/v1/databases', database_data)
        return result['id'] if result else None

    def build_session_data(self, session_key):
        """セッションデータ構築"""
        avg_time, correct_rate, total_time = self.calculate_stats()
        type_name = "掛け算" if self.question_type == "multiplication" else "割り算"
        
        # メインページデータ
        main_page = {
            'parent': {'database_id': self.config["notion_db_id"]},
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
                    '正答': {"number": q['correct_answer']},
                    '回答': {"number": q['user_answer']},
                    "時間": {"number": q['time']},
                    "正誤判定": {"select": {"name": q['judge']}}
                }
            }
            if self.question_type == 'division':
                question_data['properties']['余り正答'] = {"number": q['correct_remainder']}
                question_data['properties']['余り回答'] = {"number": q['user_remainder']}
            questions.append(question_data)
        
        return {'main_page': main_page, 'questions': questions}

    def upload_session(self, session_data):
        """単一セッションをNotionにアップロード"""
        # メインページ作成
        main_page_result = self.notion_request('https://api.notion.com/v1/pages', session_data['main_page'])
        if not main_page_result:
            return False
        
        # データベース作成
        database_id = self.create_database(main_page_result['id'])
        if not database_id:
            return False
        
        # 個別問題をアップロード
        for question_data in session_data['questions']:
            question_data['parent']['database_id'] = database_id
            if not self.notion_request('https://api.notion.com/v1/pages', question_data):
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
        buffer_data = {k: v for k, v in buffer_data.items() if k not in uploaded_sessions}
        
        # バッファ更新
        if buffer_data:
            self.file_operation('save', buffer_data)
        else:
            self.file_operation('delete')
            print("バッファファイルを削除しました")
        
        success_rate = len(uploaded_sessions) / (len(buffer_data) + len(uploaded_sessions)) if (len(buffer_data) + len(uploaded_sessions)) > 0 else 1
        print(f"アップロード結果: {len(uploaded_sessions)}/{len(buffer_data) + len(uploaded_sessions)} セッション ({success_rate:.1%})")
        
        return not buffer_data

    def generate_problems(self):
        """問題生成・実行"""
        self.questions = []
        i = 0
        count = self.config.get("initial_problem_count", 10)
        
        while i < count:
            if self.question_type == 'multiplication':
                X = random.randint(10, 99)
                Y = random.randint(10, 99)
                correct_answer = X * Y
                question_text = f"{X} × {Y} = ?"
                user_input = self.custom_keypad_dialog("掛け算問題", f"残り問題数：{count-i}問題: {question_text}")
                user_answer, _ = user_input
            elif self.question_type == 'division':
                digits = 3
                X = int(''.join([str(random.randint(1, 9)) for _ in range(digits)]))
                correct_answer = int(''.join([str(random.randint(1, 9)) for _ in range(digits)]))
                R = random.randint(0, X - 1)
                Y = X * correct_answer + R
                question_text = f"{Y} ÷ {X} = ?"
                user_answer, user_remainder = self.custom_keypad_dialog("割り算問題", f"残り問題数：{count-i}問題: {question_text}")

            start_time = time.time()

            if not user_answer:
                messagebox.showinfo("結果", "キャンセルされました。")
                return None
            
            elapsed_time = time.time() - start_time
            
            # 正誤判定
            if self.question_type == 'multiplication':
                is_correct = (int(correct_answer) == self.safe_int(user_answer))
                judge = "正解" if is_correct else "誤解"
                result_msg = f"{judge} {elapsed_time:.2f}秒"
                if not is_correct:
                    result_msg += f"\n正解: {correct_answer}"
            else: # division
                is_correct = (int(correct_answer) == self.safe_int(user_answer) and int(R) == self.safe_int(user_remainder))
                judge = "正解" if is_correct else "誤解"
                result_msg = f"{judge} {elapsed_time:.2f}秒"
                if not is_correct:
                    result_msg += f"\n正解: 商={correct_answer}, 余り={R}"

            messagebox.showinfo("結果", result_msg)
            
            # 問題データ保存
            q_data = {
                'question': question_text,
                'correct_answer': correct_answer,
                'user_answer': self.safe_int(user_answer),
                'time': elapsed_time,
                'judge': judge
            }
            if self.question_type == 'division':
                q_data['correct_remainder'] = R
                q_data['user_remainder'] = self.safe_int(user_remainder)
            self.questions.append(q_data)
            
            if is_correct:
                i += 1
            elif self.config.get("increase_on_mistake"):
                count += 1

        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def run(self):
        """メイン実行"""
        if not self.question_type:
            print("問題種別が選択されませんでした。")
            self.root.destroy()
            return

        print(f"=== {self.question_type}問題アプリ開始 ===")
        
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
    config_path = '/home/kuronos357/programming/Project/問題生成/設定・ログ/config.json'
    
    # 設定ファイル読み込み
    try:
        if not os.path.exists(config_path):
            print(f"設定ファイル '{config_path}' が見つかりません。")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            default_config = {
                "generate_division": True,
                "generate_multiplication": True,
                "initial_problem_count": 20,
                "increase_on_mistake": True,
                "notion_api_key": "YOUR_NOTION_API_KEY_HERE",
                "notion_db_id": "YOUR_NOTION_DATABASE_ID_HERE"
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            
            print(f"デフォルト設定ファイルを '{config_path}' に作成しました。")
            config = default_config
        else:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

    except json.JSONDecodeError:
        print(f"設定ファイル '{config_path}' の形式が正しくありません。")
        return
    except Exception as e:
        print(f"設定ファイルの読み込み中にエラーが発生しました: {e}")
        return

    app = QuizApp(config)
    app.run()

if __name__ == "__main__":
    main()
