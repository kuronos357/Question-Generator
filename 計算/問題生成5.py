import random
import requests
import time
from  datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog
import os
from notion_client import Client


# Tkinterウィンドウを非表示にしておく
root = tk.Tk()
root.withdraw()  # Tkinterのメインウィンドウを隠す

current_date = datetime.now().strftime('%Y-%m-%d')

NOTION_API_KEY = 'secret_MBZIR3ot9FCM0oZycKCpb2TKB5pyZuIOtZGL2rEhvSM'
DATABASE_ID = '10f5e314fd47808384fdfb936d00001b'

url = 'https://api.notion.com/v1/pages'

headers = {
    'Notion-Version': '2022-06-28',
    'Authorization': 'Bearer ' + NOTION_API_KEY,
    'Content-Type': 'application/json',
}


# ログファイルから最後の整数乱数を読み込む関数
def read_last_random_int(file_path):
    last_random_int = None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in reversed(lines):
                if "乱数（整数）" in line:
                    last_random_int = int(line.split(': ')[1])
                    break
    except FileNotFoundError:
        print("ログファイルが見つかりません。新しい乱数を生成します。")
    return last_random_int

# 乱数を生成し問題を出題し、結果をログに書き込む
def generate_and_add_random_int(file_path):
    count = 10  # 出題数
    i = 0  # 現在の問題数
    j = 0  # 総回答問題数
    execution_time = []
        
     # 実行開始時間
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write('----------------------------------------------------\n')
    
    # 問題を出題するループ
    while i < count:
        X = random.randint(1, 999)
        Y = random.randint(1, 999)
        
        
        # 正解を計算
        correct_answer = X * Y
        #print(correct_answer)
        start_time = time.time() 
        # 問題をポップアップで表示し、ユーザーの入力を受け取る
        question = f"残り問題数：{count-i}問題: {X} × {Y} = ?"
        user_answer = simpledialog.askstring("掛け算問題", question)
        
        
        if user_answer is None:
            messagebox.showinfo("結果", "キャンセルされました。")
            return  # 関数を終了してポップアップも閉じる
        
        # 正解・不正解の判定
        if str(correct_answer) == str(user_answer):
            messagebox.showinfo("結果", "正解")
            
            
            i += 1
        
        else:
            messagebox.showinfo("結果", f"不正解！正解は {correct_answer}")
            
            
            i -= 1

        # 実行時間を計算
        end_time = time.time()
        execution_time.append(end_time - start_time)

        # ログファイルに結果を書き込む
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f'問題文: {X} × {Y} = {correct_answer}\n')
            f.write(f'回答: {user_answer}\n')
            f.write(f'実行時間: {execution_time[j]:.6f} 秒\n')
            f.write('-----------------------\n')
        j += 1

    
    json_data = {
        'parent': { 'database_id': DATABASE_ID },
        'properties': {
            '名前': {
                'title': [
                    {
                        'text': {
                            'content': str( datetime.now())
                        }
                    }
                ]
            },
            '経過時間': {
                'number': sum(execution_time)
            },
            "正答率":{
                "number": 0.5+count/2/j
            },
            "問題数":{
                "number": j
            },
            
        }
    }
    response = requests.post(url, headers=headers, json=json_data)

    # Notion APIのレスポンスを確認
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
    else:
        print("Notionにデータが正常に送信されました。")
    

    # 配列内の合計を計算し、その合計を要素数で割る
    average_time = sum(execution_time) / len(execution_time)
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(f'日付: {current_date}, 平均時間: {average_time:.6f} 秒\n')
        f.write('----------------------------------------------------\n')
    
    messagebox.showinfo("結果", f"日付: {current_date}, 平均時間: {average_time:.6f} 秒")
    
    print(f"日付: {current_date}, 平均時間: {average_time:.6f} 秒,正答率：{0.5+count/2/j}")

# ログファイルのパス（エスケープシーケンス対策 + ファイル名追加）
log_file_path = r'C:\Users\奥平\プログラム\.a動作テストと物置\.vscode\作成したコード\python\log.txt'

# 乱数を生成し加算、結果をログに書き込む
generate_and_add_random_int(log_file_path)

# Tkinterを終了
root.destroy()