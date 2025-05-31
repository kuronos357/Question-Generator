import random
import requests
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import os
from notion_client import Client

# Tkinterウィンドウを非表示にしておく
root = tk.Tk()
root.withdraw()

current_date = datetime.now().strftime('%Y-%m-%d')

NOTION_API_KEY = 'secret_MBZIR3ot9FCM0oZycKCpb2TKB5pyZuIOtZGL2rEhvSM'
DATABASE_ID = '10f5e314fd47808384fdfb936d00001b'
new_row_id = None
new_database_id = None

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

    user_input = None

    keypad = tk.Toplevel()
    keypad.title(title)
    keypad.geometry('600x600')
    keypad.attributes('-topmost', True)

    question_label = tk.Label(keypad, text=question, font=('Helvetica', 14))
    question_label.pack(pady=10)

    entry_var = tk.StringVar()
    entry = tk.Entry(keypad, textvariable=entry_var, font=('Helvetica', 18), justify='right')
    entry.pack(pady=10)

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

    return user_input


def generate_and_add_random_int():
    global new_row_id 
    global totalNumber

    count = 10
    i = 0
    n=3
    execution_time = []

    while i < count:
        X = []
        correct_answer = []
        for k in range(n):
            X.append(random.randint(1, 9))
            correct_answer.append(random.randint(1, 9))
        X = int(''.join(map(str, X)))
        correct_answer = int(''.join(map(str, correct_answer)))
        Y = X * correct_answer
        print(X,Y,i,totalNumber)
        start_time = time.time()

        question = f"残り問題数：{count-i}問題: {Y} ÷ {X} = ?"
        user_answer = custom_keypad_dialog("問題", question)

        if user_answer is None or user_answer == '':
            messagebox.showinfo("結果", "キャンセルされました。")
            return

        if str(correct_answer) == str(user_answer):
            messagebox.showinfo("結果", "正解")
            judge = "正答"
            i += 1
        else:
            messagebox.showinfo("結果", f"不正解！正解は {correct_answer}")
            judge = "誤答"
            i -= 1

        totalNumber += 1
        end_time = time.time()
        execution_time.append(end_time - start_time)

        Question.append([f'{X} ÷ {Y}\n', correct_answer, user_answer, float(execution_time[i-1]), judge])
        print(Question)

    json_data = {
        'parent': {'database_id': DATABASE_ID},
        'properties': {
            '名前': {
                'title': [{'text': {'content': str(datetime.now())}}]
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
            "問題種":{
                "select":{ 
                    "name":"割り算"
                }
            }
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    
    if response.status_code == 200:
        print("新しい行が正常に追加されました。")
        new_row_id = response.json()['id']
        print(f"追加された行のID: {new_row_id}")
        create_database_in_row()
    else:
        print(f"エラーが発生しました: {response.status_code} - {response.text}")
        return None

    average_time = sum(execution_time) / len(execution_time)
    messagebox.showinfo("結果", f"日付: {current_date}, 平均時間: {average_time:.6f} 秒")
    print(f"日付: {current_date}, 平均時間: {average_time:.6f} 秒, 正答率：{0.5 + count / 2 / totalNumber}")


def create_database_in_row():
    global new_row_id, new_database_id

    if new_row_id is None:
        print("エラー: 子ページIDが設定されていません。")
        return

    database_data = {
        "parent": {"page_id": new_row_id},
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

    response = requests.post(url_create_db, headers=headers, json=database_data)

    if response.status_code == 200:
        print("データベースが正常に作成されました。")
        new_database_id = response.json()['id']
        print(f"作成されたデータベースのID: {new_database_id}")
    else:
        print(f"エラーが発生しました: {response.status_code} - {response.text}")


def repeated_task(k):
    global new_database_id
    print(k,"番目のデータを書きこみ")

    json_data = {
        'parent': {'database_id': new_database_id},
        'properties': {
            "問題番号": {
                'title': [{'text': {'content': str(k)}}]
            },
            '問題': {
                'rich_text': [{'text': {'content': str(Question[k][0])}}]
            },
            '正答': {
                "number": float(Question[k][1])
            },
            '回答': {
                "number": float(Question[k][2])
            },
            "時間": {
                "number": float(Question[k][3])
            },
            "正誤判定": {
                "select": {"name": str(Question[k][4])}
            },
        }
    }

    response = requests.post(url, headers=headers, json=json_data)
    print(Question[k],k,"番目のデータを書きこみ完了")


# メイン処理
generate_and_add_random_int()

for k in range(totalNumber):
    
    repeated_task(k)

root.destroy()
