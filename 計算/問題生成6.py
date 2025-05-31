import random
import requests
import time
from datetime import datetime
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
new_row_id = None  # 追加された行（子ページ）のID
new_database_id = None  # 作成されたデータベースのID

totalNumber = 0  # 総回答問題数
Question = []

url = 'https://api.notion.com/v1/pages'
url_create_db = 'https://api.notion.com/v1/databases'

headers = {
    'Notion-Version': '2022-06-28',
    'Authorization': 'Bearer ' + NOTION_API_KEY,
    'Content-Type': 'application/json',
}



# 乱数を生成し問題を出題し、結果をログに書き込む
def generate_and_add_random_int():
    global new_row_id 
    global totalNumber
    
    count = 10  # 出題数
    i = 0  # 現在の問題数を初期化
    
    execution_time = []



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
            judge = "正解"
            i += 1  # 問題数をカウント
        else:
            messagebox.showinfo("結果", f"不正解！正解は {correct_answer}")
            judge = "誤解"
            i-=1
        
        totalNumber += 1
        # 実行時間を計算
        end_time = time.time()
        execution_time.append(end_time - start_time)


        Question.append([f'{X} × {Y}\n', correct_answer, user_answer, float(execution_time[i-1]), judge])
        
    
    


    json_data = {
        'parent': {'database_id': DATABASE_ID},
        'properties': {
            '名前': {
                'title': [
                    {
                        'text': {
                            'content': str(datetime.now())
                        }
                    }
                ]
            },
            '経過時間': {
                'number': sum(execution_time)
            },
            "正答率": {
                "number": 0.5 + (count / 2 / totalNumber)
            },
            "問題数": {
                "number": totalNumber
            },
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    
    if response.status_code == 200:
        print("新しい行が正常に追加されました。")
        new_row_id = response.json()['id']  # グローバル変数に新しい行のIDを保存
        print(f"追加された行のID: {new_row_id}")
        
        # 次に、追加された行にデータベースを作成
        create_database_in_row()
    else:
        print(f"エラーが発生しました: {response.status_code} - {response.text}")
        return None


    # 配列内の合計を計算し、その合計を要素数で割る
    average_time = sum(execution_time) / len(execution_time)


    messagebox.showinfo("結果", f"日付: {current_date}, 平均時間: {average_time:.6f} 秒")
    print(f"日付: {current_date}, 平均時間: {average_time:.6f} 秒,正答率：{0.5 + count / 2 / totalNumber}")


def create_database_in_row():
    global new_row_id, new_database_id  # グローバル変数を使用

    if new_row_id is None:
        print("エラー: 子ページIDが設定されていません。")
        return

    # データベースの構造を定義
    database_data = {
        
        "parent": {"page_id": new_row_id},  # 取得した子ページのIDを使用
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "個別の問題"
                }
            }
        ],
        "properties": {
            "問題番号": {
                "title": {}
            },
            "問題": {  # テキストプロパティの追加
                "rich_text": {}
            },
            "正答": {
                "number": {
                    "format": "number"
                }
            },
            "回答": {
                "number": {
                    "format": "number"
                }
            },
            "時間": {
                "number": {
                    "format": "number"
                }
            },
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

    # データベースをNotionに送信
    response = requests.post(url_create_db, headers=headers, json=database_data)

    if response.status_code == 200:
        print("データベースが正常に作成されました。")
        new_database_id = response.json()['id']  # 作成されたデータベースのIDを取得
        print(f"作成されたデータベースのID: {new_database_id}")
    else:
        print(f"エラーが発生しました: {response.status_code} - {response.text}")


def repeated_task(k):
    global new_database_id
    print(Question[k][4])
    
    json_data = {
        
        'parent': {'database_id': new_database_id},
        'properties': {
            "問題番号": {
                'title': [
                    {
                        'text': {
                            'content': str(k)
                        }
                    }
                ]
            },
            '問題': {
                'rich_text': [
                    {
                        'text': {
                            'content': str(Question[k][0])
                        }
                    }
                ]
            },
            '正答': {
                "number": float (Question[k][1])
            },
            '回答': {
                "number": float (Question[k][2])
            },
            "時間": {
                "number": float (Question[k][3])
            },
            "正誤判定": {
                "select": {
                    "name": str(Question[k][4])
                }
            },
        }
    }

    response = requests.post(url, headers=headers, json=json_data)




# 乱数を生成し加算、結果をログに書き込む
generate_and_add_random_int()

for k in range(totalNumber):
    print("データを書きこみ")
    repeated_task(k)

# Tkinterを終了
root.destroy()