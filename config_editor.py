
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import os

class ConfigEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("設定エディタ")
        self.geometry("500x450")

        # スクリプトの場所を基準に設定ファイルのパスを決定
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(script_dir, 'ログ・設定', 'config.json')

        self.vars = {
            "NOTION_API_KEY": tk.StringVar(),
            "DATABASE_ID": tk.StringVar(),
            "LOG_FILE": tk.StringVar(),
            "DEBUG": tk.BooleanVar(),
            "NUM_DIGITS": tk.IntVar(value=3),
            "ADD_QUESTIONS_ON_MISTAKE": tk.IntVar(value=1),
            "NUM_QUESTIONS": tk.IntVar(value=10),
            "MAX_QUESTIONS": tk.IntVar(value=100),
            "TYPE": tk.StringVar(value="掛け算")
        }

        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # 設定項目
        fields = [
            ("Notion APIキー", "NOTION_API_KEY", "entry"),
            ("データベースID", "DATABASE_ID", "entry"),
            ("ログファイルパス", "LOG_FILE", "entry"),
            ("デバッグモード", "DEBUG", "checkbutton"),
            ("問題の桁数", "NUM_DIGITS", "spinbox"),
            ("間違い時の追加問題数", "ADD_QUESTIONS_ON_MISTAKE", "spinbox"),
            ("初期問題数", "NUM_QUESTIONS", "spinbox"),
            ("最大問題数", "MAX_QUESTIONS", "spinbox"),
            ("問題種別", "TYPE", "combobox")
        ]

        for i, (label_text, key, widget_type) in enumerate(fields):
            label = ttk.Label(frame, text=label_text)
            label.grid(row=i, column=0, sticky=tk.W, pady=5, padx=5)

            if widget_type == "entry":
                widget = ttk.Entry(frame, textvariable=self.vars[key], width=40)
            elif widget_type == "checkbutton":
                widget = ttk.Checkbutton(frame, variable=self.vars[key])
            elif widget_type == "spinbox":
                widget = ttk.Spinbox(frame, from_=1, to=1000, textvariable=self.vars[key])
            elif widget_type == "combobox":
                widget = ttk.Combobox(frame, textvariable=self.vars[key], values=["掛け算", "割り算"], state="readonly")

            widget.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        # 保存ボタン
        save_button = ttk.Button(frame, text="保存", command=self.save_config)
        save_button.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        frame.columnconfigure(1, weight=1)

    def load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            for key, value in config.items():
                if key in self.vars:
                    self.vars[key].set(value)

        except FileNotFoundError:
            messagebox.showwarning("警告", "設定ファイルが見つかりません。デフォルト値で起動します。")
        except Exception as e:
            messagebox.showerror("エラー", f"設定ファイルの読み込みに失敗しました: {e}")

    def save_config(self):
        try:
            config = {}
            for key, var in self.vars.items():
                config[key] = var.get()

            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("成功", "設定を保存しました。")

        except Exception as e:
            messagebox.showerror("エラー", f"設定ファイルの保存に失敗しました: {e}")


if __name__ == "__main__":
    app = ConfigEditor()
    app.mainloop()
