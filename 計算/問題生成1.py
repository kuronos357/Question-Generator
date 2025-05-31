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


def generate_and_add_random_int(file_path):
    count = 2
    i = 0
    
    start_time = time.time()
    while i < count:
        print("残り問題数",count-i)
        X = random.randint(1, 999)
        print(" ",X)
        Y = random.randint(1, 999)
        print("×",Y)
        print("-------")
        a=X*Y
        print(a)
        b=input()
        if str(a) ==str(b):
            print("正解")
            i+=1
        else:
            print("不正解")
            print("正解は",a)
            i-=1

    # 実行終了時間
    end_time = time.time()

    # 実行時間を計算
    execution_time = end_time - start_time

    # ログファイルに結果を書き込む
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(f'日付: {current_date}\n')
        f.write(f'問題文: {X}*{Y}={a}\n')
        f.write(f'回答: {b}\n')
        f.write(f'実行時間: {execution_time:.6f} 秒\n')
        f.write('-----------------------\n')
    print(f"日付: {current_date},問題文: {X}*{Y}={a}, 回答: {b}, 実行時間: {execution_time:.6f} 秒")

# ログファイルのパス（エスケープシーケンス対策）
log_file_path = r'C:\Users\奥平\プログラム\.a動作テストと物置\.vscode\作成したコード\python\log.txt'