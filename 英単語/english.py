import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import random
import os
from typing import List, Dict, Optional

class EnglishVocabQuiz:
    def __init__(self):
        # メインウィンドウの設定
        self.root = tk.Tk()
        self.root.title("英単語クイズ")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f4f8')
        
        # 状態変数
        self.vocabulary_data = []
        self.questions = []
        self.current_question = 0
        self.score = 0
        self.selected_answer = None
        self.show_result = False
        self.quiz_started = False
        self.quiz_complete = False
        self.show_etymology = False
        
        # 語源データベース
        self.etymology_database = {
            # 接頭辞
            'ab-': '離れて、から', 'ac-': 'に向かって', 'ad-': 'に向かって',
            'ambi-': '両方', 'ana-': '上に、再び', 'anti-': '反対の',
            'auto-': '自己の', 'bi-': '2つの', 'co-': '共に', 'com-': '完全に',
            'con-': '共に', 'de-': '下に、除去', 'dis-': '離れて、否定',
            'ex-': '外に', 'in-': '中に、否定', 'inter-': '間の',
            'pre-': '前の', 'pro-': '前に', 're-': '再び', 'sub-': '下に',
            'super-': '上に', 'trans-': '横切って', 'un-': '否定',
            
            # 語根
            'act': '行動', 'duc': '導く', 'fac': '作る', 'form': '形',
            'graph': '書く', 'log': '言葉', 'mit': '送る', 'port': '運ぶ',
            'scrib': '書く', 'spec': '見る', 'struct': '建てる',
            'tract': '引く', 'vert': '回る', 'vid': '見る',
            
            # 接尾辞
            '-able': 'できる', '-ance': '状態', '-ent': '～する',
            '-er': '～する人', '-ful': '満ちた', '-ion': '動作・状態',
            '-ity': '性質', '-ive': '～の性質', '-less': '～のない',
            '-ment': '結果・手段', '-ness': '状態', '-ous': '～の性質'
        }
        
        self.setup_ui()
        self.load_default_vocabulary()
        
    def setup_ui(self):
        """UIをセットアップ"""
        # メインフレーム
        self.main_frame = tk.Frame(self.root, bg='#f0f4f8')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.show_menu()
        
    def show_menu(self):
        """メニュー画面を表示"""
        self.clear_frame()
        
        # タイトル
        title_frame = tk.Frame(self.main_frame, bg='#ffffff', relief=tk.RAISED, bd=2)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(title_frame, text="英単語クイズ", font=("Arial", 24, "bold"), 
                bg='#ffffff', fg='#2563eb', pady=20).pack()
        
        tk.Label(title_frame, text="大学受験レベルの英単語を4択で学習", 
                font=("Arial", 12), bg='#ffffff', fg='#666666', pady=(0, 20)).pack()
        
        # データ情報
        info_frame = tk.Frame(self.main_frame, bg='#ffffff', relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(info_frame, text=f"📚 {len(self.vocabulary_data)}語の英単語を準備済み", 
                font=("Arial", 12), bg='#ffffff', fg='#059669', pady=10).pack()
        
        # 機能説明
        features_frame = tk.Frame(self.main_frame, bg='#ffffff', relief=tk.RAISED, bd=2)
        features_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(features_frame, text="クイズの特徴", font=("Arial", 14, "bold"), 
                bg='#ffffff', fg='#1f2937', pady=(10, 5)).pack()
        
        features = [
            "• CSVファイルから実際の単語を出題",
            "• 語源解説付きで深く学習", 
            "• 類義語を考慮した4択問題",
            "• 全10問のチャレンジ"
        ]
        
        for feature in features:
            tk.Label(features_frame, text=feature, font=("Arial", 10), 
                    bg='#ffffff', fg='#374151', pady=2).pack(anchor=tk.W, padx=20)
        
        tk.Label(features_frame, text="", pady=5).pack()  # スペーサー
        
        # ボタンフレーム
        button_frame = tk.Frame(self.main_frame, bg='#f0f4f8')
        button_frame.pack(fill=tk.X)
        
        # CSVファイル読み込みボタン
        load_btn = tk.Button(button_frame, text="📁 CSVファイルを読み込み", 
                           font=("Arial", 12), bg='#10b981', fg='white',
                           padx=20, pady=10, command=self.load_csv_file)
        load_btn.pack(pady=(0, 10), fill=tk.X)
        
        # クイズ開始ボタン
        start_btn = tk.Button(button_frame, text="🎯 クイズを始める", 
                            font=("Arial", 14, "bold"), bg='#2563eb', fg='white',
                            padx=20, pady=15, command=self.start_quiz)
        start_btn.pack(fill=tk.X)
        
    def load_csv_file(self):
        """CSVファイルを読み込み"""
        file_path = filedialog.askopenfilename(
            title="英単語CSVファイルを選択",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # CSVファイルを読み込み
                df = pd.read_csv(file_path, encoding='utf-8')
                
                # 必要な列があるかチェック
                if '英語' not in df.columns or '日本語' not in df.columns:
                    messagebox.showerror("エラー", "CSVファイルに '英語' と '日本語' の列が必要です。")
                    return
                
                # データをクリーンアップして変換
                valid_entries = []
                for _, row in df.iterrows():
                    if pd.notna(row['英語']) and pd.notna(row['日本語']):
                        word = str(row['英語']).strip()
                        meaning = str(row['日本語']).strip()
                        
                        if word and meaning:
                            # 日本語から品詞情報を除去
                            clean_meaning = meaning
                            if '(' in meaning:
                                clean_meaning = meaning.split('(')[0].strip()
                            if '，' in clean_meaning:
                                clean_meaning = clean_meaning.split('，')[0].strip()
                            
                            valid_entries.append({
                                'word': word,
                                'meaning': clean_meaning or meaning,
                                'etymology': self.generate_etymology(word)
                            })
                
                if valid_entries:
                    self.vocabulary_data = valid_entries
                    messagebox.showinfo("成功", f"{len(valid_entries)}語の英単語を読み込みました。")
                    self.show_menu()  # メニューを更新
                else:
                    messagebox.showerror("エラー", "有効な単語データが見つかりませんでした。")
                    
            except Exception as e:
                messagebox.showerror("エラー", f"ファイルの読み込みに失敗しました: {str(e)}")
    
    def load_default_vocabulary(self):
        """デフォルトの語彙データを読み込み"""
        default_vocab = [
            {
                'word': "important",
                'meaning': "重要な",
                'etymology': "ラテン語 importare (持ち込む) から。in- (中に) + portare (運ぶ) = 中に運び込む重要なもの"
            },
            {
                'word': "through",
                'meaning': "～を通って",
                'etymology': "古英語 thurh から。ゲルマン語族共通の語根で「貫通する」という意味"
            },
            {
                'word': "language",
                'meaning': "言語",
                'etymology': "ラテン語 lingua (舌) から。フランス語を経て英語に。舌で話すもの = 言語"
            },
            {
                'word': "international",
                'meaning': "国際的な",
                'etymology': "ラテン語 inter (間) + natio (国) + -al (形容詞語尾) = 国と国の間の"
            },
            {
                'word': "possible",
                'meaning': "可能な",
                'etymology': "ラテン語 posse (できる) から。pos- (力) + -ible (可能) = 力があってできる"
            }
        ]
        
        # CSVファイルが存在する場合は読み込みを試行
        csv_path = "英単語.csv"
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path, encoding='utf-8')
                if '英語' in df.columns and '日本語' in df.columns:
                    vocab_data = []
                    for _, row in df.iterrows():
                        if pd.notna(row['英語']) and pd.notna(row['日本語']):
                            word = str(row['英語']).strip()
                            meaning = str(row['日本語']).strip()
                            if word and meaning:
                                vocab_data.append({
                                    'word': word,
                                    'meaning': meaning,
                                    'etymology': self.generate_etymology(word)
                                })
                    if vocab_data:
                        self.vocabulary_data = vocab_data
                        return
            except:
                pass
        
        self.vocabulary_data = default_vocab
    
    def generate_etymology(self, word: str) -> str:
        """語源を生成"""
        specific_etymologies = {
            'important': 'ラテン語 importare (持ち込む) から。in- (中に) + portare (運ぶ) = 中に運び込む重要なもの',
            'through': '古英語 thurh から。ゲルマン語族共通の語根で「貫通する」という意味',
            'language': 'ラテン語 lingua (舌) から。フランス語を経て英語に。舌で話すもの = 言語',
            'international': 'ラテン語 inter (間) + natio (国) + -al (形容詞語尾) = 国と国の間の',
            'possible': 'ラテン語 posse (できる) から。pos- (力) + -ible (可能) = 力があってできる'
        }
        
        if word.lower() in specific_etymologies:
            return specific_etymologies[word.lower()]
        
        # 語根分析による自動生成
        etymology = ''
        lower_word = word.lower()
        
        # 接頭辞チェック
        for prefix, meaning in self.etymology_database.items():
            if prefix.endswith('-') and lower_word.startswith(prefix.replace('-', '')):
                etymology += f"接頭辞 {prefix} ({meaning}) + "
                break
        
        # 語根チェック
        for root, meaning in self.etymology_database.items():
            if '-' not in root and root in lower_word:
                etymology += f"語根 {root} ({meaning}) + "
                break
        
        # 接尾辞チェック
        for suffix, meaning in self.etymology_database.items():
            if suffix.startswith('-') and lower_word.endswith(suffix.replace('-', '')):
                etymology += f"接尾辞 {suffix} ({meaning})"
                break
        
        return etymology or '語源情報を準備中です。一般的な英語の語源は、ラテン語、ゲルマン語、フランス語などに由来します。'
    
    def generate_options(self, correct_word: str) -> List[str]:
        """選択肢を生成"""
        word_data = next((item for item in self.vocabulary_data if item['word'] == correct_word), None)
        if not word_data:
            return [correct_word]
        
        correct_meaning = word_data['meaning']
        other_meanings = [item['meaning'] for item in self.vocabulary_data 
                         if item['word'] != correct_word and item['meaning'] != correct_meaning]
        
        # 類似した意味の長さを持つ選択肢を優先
        similar_meanings = [m for m in other_meanings 
                          if abs(len(m) - len(correct_meaning)) <= 3]
        random.shuffle(similar_meanings)
        
        # 3つの不正解選択肢を選択
        wrong_options = similar_meanings[:3]
        
        # 足りない場合は他の選択肢を追加
        if len(wrong_options) < 3:
            remaining = [m for m in other_meanings if m not in wrong_options]
            random.shuffle(remaining)
            wrong_options.extend(remaining[:3-len(wrong_options)])
        
        # 正解を含めた4つの選択肢をシャッフル
        all_options = [correct_meaning] + wrong_options[:3]
        random.shuffle(all_options)
        
        return all_options
    
    def generate_questions(self, num_questions: int = 10) -> List[Dict]:
        """クイズ問題を生成"""
        if not self.vocabulary_data:
            return []
        
        shuffled_vocab = self.vocabulary_data.copy()
        random.shuffle(shuffled_vocab)
        selected_words = shuffled_vocab[:min(num_questions, len(self.vocabulary_data))]
        
        questions = []
        for word_data in selected_words:
            questions.append({
                'word': word_data['word'],
                'correct_answer': word_data['meaning'],
                'options': self.generate_options(word_data['word']),
                'etymology': word_data['etymology']
            })
        
        return questions
    
    def start_quiz(self):
        """クイズを開始"""
        if not self.vocabulary_data:
            messagebox.showwarning("警告", "単語データがありません。CSVファイルを読み込んでください。")
            return
        
        self.questions = self.generate_questions(10)
        self.current_question = 0
        self.score = 0
        self.selected_answer = None
        self.show_result = False
        self.quiz_started = True
        self.quiz_complete = False
        self.show_etymology = False
        
        self.show_question()
    
    def show_question(self):
        """問題を表示"""
        self.clear_frame()
        
        current_q = self.questions[self.current_question]
        
        # ヘッダーフレーム
        header_frame = tk.Frame(self.main_frame, bg='#ffffff', relief=tk.RAISED, bd=2)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # タイトルと進捗
        title_frame = tk.Frame(header_frame, bg='#ffffff')
        title_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(title_frame, text="英単語クイズ", font=("Arial", 18, "bold"), 
                bg='#ffffff', fg='#1f2937').pack(side=tk.LEFT)
        
        tk.Label(title_frame, text=f"{self.current_question + 1}/{len(self.questions)}", 
                font=("Arial", 14, "bold"), bg='#ffffff', fg='#2563eb').pack(side=tk.RIGHT)
        
        # プログレスバー
        progress_frame = tk.Frame(header_frame, bg='#ffffff')
        progress_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        progress_bar['value'] = ((self.current_question + 1) / len(self.questions)) * 100
        
        # スコア表示
        score_text = f"スコア: {self.score}/{self.current_question + (1 if self.show_result else 0)}"
        tk.Label(progress_frame, text=score_text, font=("Arial", 10), 
                bg='#ffffff', fg='#666666').pack(side=tk.RIGHT, padx=(10, 0))
        
        # 問題フレーム
        question_frame = tk.Frame(self.main_frame, bg='#ffffff', relief=tk.RAISED, bd=2)
        question_frame.pack(fill=tk.BOTH, expand=True)
        
        # 問題文
        tk.Label(question_frame, text="次の英単語の意味を選んでください", 
                font=("Arial", 12), bg='#ffffff', fg='#666666', pady=20).pack()
        
        tk.Label(question_frame, text=current_q['word'], font=("Arial", 28, "bold"), 
                bg='#ffffff', fg='#1f2937', pady=20).pack()
        
        # 選択肢フレーム
        options_frame = tk.Frame(question_frame, bg='#ffffff')
        options_frame.pack(fill=tk.X, padx=40, pady=20)
        
        self.option_buttons = []
        for i, option in enumerate(current_q['options']):
            btn = tk.Button(options_frame, text=option, font=("Arial", 12), 
                          pady=15, wraplength=300, justify=tk.LEFT,
                          command=lambda opt=option: self.select_answer(opt))
            btn.pack(fill=tk.X, pady=5)
            self.option_buttons.append(btn)
        
        self.update_button_colors()
        
        # 結果表示エリア
        self.result_frame = tk.Frame(question_frame, bg='#ffffff')
        self.result_frame.pack(fill=tk.X, padx=40, pady=20)
        
        if self.show_result:
            self.show_question_result()
    
    def update_button_colors(self):
        """ボタンの色を更新"""
        current_q = self.questions[self.current_question]
        
        for i, btn in enumerate(self.option_buttons):
            option = current_q['options'][i]
            
            if not self.show_result:
                if option == self.selected_answer:
                    btn.configure(bg='#dbeafe', fg='#1d4ed8', relief=tk.RAISED)
                else:
                    btn.configure(bg='#f9fafb', fg='#374151', relief=tk.FLAT)
            else:
                if option == current_q['correct_answer']:
                    btn.configure(bg='#dcfce7', fg='#166534', relief=tk.RAISED)
                elif option == self.selected_answer and option != current_q['correct_answer']:
                    btn.configure(bg='#fee2e2', fg='#dc2626', relief=tk.RAISED)
                else:
                    btn.configure(bg='#f3f4f6', fg='#9ca3af', relief=tk.FLAT)
    
    def select_answer(self, answer: str):
        """答えを選択"""
        if self.show_result:
            return
        
        self.selected_answer = answer
        self.show_result = True
        
        current_q = self.questions[self.current_question]
        if answer == current_q['correct_answer']:
            self.score += 1
        
        self.update_button_colors()
        self.show_question_result()
    
    def show_question_result(self):
        """問題の結果を表示"""
        current_q = self.questions[self.current_question]
        
        # 結果メッセージ
        if self.selected_answer == current_q['correct_answer']:
            result_text = "🎉 正解！"
            result_color = '#059669'
        else:
            result_text = f"❌ 不正解 - 正解は「{current_q['correct_answer']}」です"
            result_color = '#dc2626'
        
        tk.Label(self.result_frame, text=result_text, font=("Arial", 14, "bold"), 
                bg='#ffffff', fg=result_color, pady=10).pack()
        
        # 語源表示ボタン
        etymology_btn = tk.Button(self.result_frame, 
                                text="📚 語源を表示" if not self.show_etymology else "📚 語源を隠す",
                                font=("Arial", 10), bg='#f3e8ff', fg='#7c3aed',
                                pady=5, command=self.toggle_etymology)
        etymology_btn.pack(pady=10)
        
        # 語源表示エリア
        if self.show_etymology:
            etymology_frame = tk.Frame(self.result_frame, bg='#f3e8ff', relief=tk.RAISED, bd=1)
            etymology_frame.pack(fill=tk.X, pady=10)
            
            tk.Label(etymology_frame, text=f"📖 語源解説: {current_q['word']}", 
                    font=("Arial", 11, "bold"), bg='#f3e8ff', fg='#7c3aed', pady=5).pack()
            
            tk.Label(etymology_frame, text=current_q['etymology'], 
                    font=("Arial", 10), bg='#f3e8ff', fg='#6b46c1', 
                    wraplength=400, justify=tk.LEFT, pady=10).pack()
        
        # 次へボタン
        next_text = "次の問題" if self.current_question + 1 < len(self.questions) else "結果を見る"
        next_btn = tk.Button(self.result_frame, text=next_text, font=("Arial", 12, "bold"), 
                           bg='#2563eb', fg='white', pady=10, padx=30, 
                           command=self.next_question)
        next_btn.pack(pady=20)
    
    def toggle_etymology(self):
        """語源表示を切り替え"""
        self.show_etymology = not self.show_etymology
        self.show_question()
    
    def next_question(self):
        """次の問題へ"""
        if self.current_question + 1 < len(self.questions):
            self.current_question += 1
            self.selected_answer = None
            self.show_result = False
            self.show_etymology = False
            self.show_question()
        else:
            self.quiz_complete = True
            self.show_results()
    
    def show_results(self):
        """最終結果を表示"""
        self.clear_frame()
        
        # 結果フレーム
        result_frame = tk.Frame(self.main_frame, bg='#ffffff', relief=tk.RAISED, bd=2)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # トロフィーアイコン（テキストで代替）
        tk.Label(result_frame, text="🏆", font=("Arial", 48), 
                bg='#ffffff', pady=20).pack()
        
        tk.Label(result_frame, text="クイズ完了！", font=("Arial", 24, "bold"), 
                bg='#ffffff', fg='#1f2937', pady=10).pack()
        
        # スコア表示
        score_text = f"{self.score}/{len(self.questions)}"
        tk.Label(result_frame, text=score_text, font=("Arial", 36, "bold"), 
                bg='#ffffff', fg='#2563eb', pady=10).pack()
        
        percentage = round((self.score / len(self.questions)) * 100)
        tk.Label(result_frame, text=f"正答率: {percentage}%", font=("Arial", 18), 
                bg='#ffffff', fg='#666666', pady=10).pack()
        
        # 評価メッセージ
        message = self.get_score_message()
        tk.Label(result_frame, text=message, font=("Arial", 14), 
                bg='#ffffff', fg='#374151', pady=20).pack()
        
        # ボタンフレーム
        button_frame = tk.Frame(result_frame, bg='#ffffff')
        button_frame.pack(pady=30)
        
        # もう一度挑戦ボタン
        retry_btn = tk.Button(button_frame, text="🔄 もう一度挑戦", 
                            font=("Arial", 12, "bold"), bg='#2563eb', fg='white',
                            padx=20, pady=10, command=self.start_quiz)
        retry_btn.pack(pady=5, fill=tk.X)
        
        # メニューに戻るボタン
        menu_btn = tk.Button(button_frame, text="📋 メニューに戻る", 
                           font=("Arial", 12), bg='#6b7280', fg='white',
                           padx=20, pady=10, command=self.return_to_menu)
        menu_btn.pack(pady=5, fill=tk.X)
    
    def get_score_message(self) -> str:
        """スコアに基づく評価メッセージを取得"""
        percentage = (self.score / len(self.questions)) * 100
        if percentage >= 90:
            return "素晴らしい！完璧に近い成績です！"
        elif percentage >= 80:
            return "とても良くできました！"
        elif percentage >= 70:
            return "良い成績です！"
        elif percentage >= 60:
            return "もう少し頑張りましょう。"
        else:
            return "復習が必要ですね。頑張りましょう！"
    
    def return_to_menu(self):
        """メニューに戻る"""
        self.quiz_started = False
        self.quiz_complete = False
        self.show_menu()
    
    def clear_frame(self):
        """フレームをクリア"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def run(self):
        """アプリケーションを実行"""
        self.root.mainloop()

def main():
    app = EnglishVocabQuiz()
    app.run()

if __name__ == "__main__":
    main()