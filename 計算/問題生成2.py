import random
import time
from datetime import datetime

current_date = datetime.now().strftime('%Y-%m-%d')

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
    count = 2  # 出題数
    i = 0  # 現在の問題数
    j = 0
    execution_time =[]
    
    start_time = time.time()  # 実行開始時間
    with open(file_path, 'a', encoding='utf-8') as f:
        
        f.write('----------------------------------------------------\n')
        
    # 問題を出題するループ
    while i < count:
        print("残り問題数", count - i)
        X = random.randint(1, 999)
        Y = random.randint(1, 999)
        print(f" {X}")
        print(f"× {Y}")
        print("-------")
        
        # 正解を計算
        correct_answer = X * Y
        print(correct_answer)

        # ユーザー入力
        user_answer = input()

        # 正解・不正解の判定
        if str(correct_answer) == str(user_answer):
            print("正解")
            i += 1
        else:
            print("不正解")
            print("正解は", correct_answer)
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
        
        j+=1
    
    # 配列内の合計を計算し、その合計を要素数で割る
    averageTime = sum(execution_time)/ len(execution_time)
    print(sum(execution_time),len(execution_time))



    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(f'日付: {current_date},平均時間{averageTime}\n')
        f.write('----------------------------------------------------\n')
    
    print(f"日付: {current_date}, 問題文: {X} × {Y} = {correct_answer}, 回答: {user_answer}, 実行時間: {averageTime:.6f} 秒")

# ログファイルのパス（エスケープシーケンス対策 + ファイル名追加）
log_file_path = r'C:\Users\奥平\プログラム\.a動作テストと物置\.vscode\作成したコード\python\log.txt'

# 乱数を生成し加算、結果をログに書き込む
generate_and_add_random_int(log_file_path)
