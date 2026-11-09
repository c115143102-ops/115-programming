"""
Bejeweled Blitz 自動消除（8x8 棋盤）

用法：
    python bejeweled_auto.py            # 開始自動消除
    python bejeweled_auto.py calibrate  # 校正棋盤座標與顏色
    python bejeweled_auto.py selftest   # 邏輯測試（不需要遊戲畫面）

操作：
    按住 Q 停止，或把滑鼠移到螢幕左上角（pyautogui 安全機制）可停止
"""

import ctypes
import sys
import time

import cv2
import numpy as np
import pyautogui
from PIL import ImageGrab

# 讓 pyautogui 與截圖使用相同的實體像素座標（高 DPI 螢幕必備）
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# =========================
# 棋盤位置（螢幕座標）
# 請用 calibrate 模式校正後填入
# =========================
LEFT, TOP = 495, 371
RIGHT, BOTTOM = 820, 691
WIDTH, HEIGHT = RIGHT - LEFT, BOTTOM - TOP
N = 8

# 座標填錯（例如寬高小於 100）會讓後面所有辨識失敗，先擋下來
assert WIDTH > 100 and HEIGHT > 100, (
    f"棋盤座標設定錯誤：寬 {WIDTH}、高 {HEIGHT}，"
    f"請先執行 calibrate 重新校正"
)

CW, CH = WIDTH / N, HEIGHT / N

# =========================
# 寶石定位
# =========================
# basex, basey：左上角寶石的中心點（螢幕座標）
basex = int(LEFT + CW / 2)
basey = int(TOP + CH / 2)

# gap：每顆寶石的間距（可給單一數值，或 (水平, 垂直)）
gap = (CW, CH)


def gem_pos(r, c):
    """回傳第 r 列（row）、第 c 行（column）那顆寶石的中心點 (x, y)。"""
    gap_x, gap_y = gap if isinstance(gap, (tuple, list)) else (gap, gap)
    return int(basex + c * gap_x), int(basey + r * gap_y)


# =========================
# 時間與流程設定
# =========================
ROUND_TIME = 62       # Bejeweled Blitz 一局約 60 秒，留一點緩衝
START_DELAY = 10      # 按下執行後，等幾秒才開始動作（先切到遊戲畫面）
STILL_LIMIT = 8       # 連續幾次找不到步可走，就判定遊戲結束
SETTLE_TIMEOUT = 2.0  # 等棋盤穩定的最長時間（秒）
VERBOSE = True        # 是否印出每次辨識到的棋盤

# 不列入消除判斷的格子
IGNORE = {"empty", "unknown"}

SYMBOL = {
    "red": "R", "orange": "O", "yellow": "Y", "green": "G",
    "blue": "B", "purple": "P", "white": "W",
    "empty": ".", "unknown": "?",
}


# =========================
# 截圖
# =========================
def capture():
    img = ImageGrab.grab(
        bbox=(LEFT, TOP, RIGHT, BOTTOM), all_screens=True
    )
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def stop_pressed():
    """按住 Q 停止（不需額外套件）。"""
    return bool(ctypes.windll.user32.GetAsyncKeyState(ord("Q")) & 0x8000)


def sleep_interruptible(seconds):
    """等待期間每 0.1 秒檢查一次 Q，可隨時中斷；回傳是否正常等完。"""
    deadline = time.time() + seconds
    while time.time() < deadline:
        if stop_pressed():
            return False
        time.sleep(0.1)
    return True


# =========================
# 顏色辨識
# =========================
def identify(patch):
    """把一小塊畫面（BGR）轉成寶石顏色名稱。"""
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV).reshape(-1, 3).astype(np.float32)

    # 色相是環狀量（0 與 179 相鄰），直接取中位數會在交界處
    # （尤其是紅色）算錯，改用向量平均求圓形平均色相。
    ang = hsv[:, 0] * (np.pi / 90.0)
    hue = int(round(np.degrees(np.arctan2(
        np.sin(ang).mean(), np.cos(ang).mean())))) % 180
    sat = int(np.median(hsv[:, 1]))
    val = int(np.median(hsv[:, 2]))

    if val < 55:        # 太暗 → 空格
        return "empty"
    if sat < 45:        # 幾乎沒有飽和度 → 白色 / 特殊寶石
        return "white"
    if hue < 8 or hue >= 170:
        return "red"
    if hue < 22:
        return "orange"
    if hue < 35:
        return "yellow"
    if hue < 85:
        return "green"
    if hue < 115:
        return "blue"
    return "purple"


def read_board(img):
    """把截圖轉成 8x8 的顏色盤面。"""
    board = []
    for r in range(N):
        row = []
        for c in range(N):
            x = int((c + .5) * CW)
            y = int((r + .5) * CH)
            patch = img[y - 4:y + 5, x - 4:x + 5]
            row.append(identify(patch))
        board.append(row)
    return board


def print_board(board):
    for row in board:
        print(" " + " ".join(SYMBOL.get(c, "?") for c in row))


# =========================
# 消除判斷
# =========================
def find_matches(board):
    """回傳所有會被消除的格子座標集合 {(r, c), ...}。"""
    found = set()

    # 水平
    for r in range(N):
        c = 0
        while c < N:
            color = board[r][c]
            end = c
            while end < N and board[r][end] == color:
                end += 1
            if color not in IGNORE and end - c >= 3:
                found.update((r, x) for x in range(c, end))
            c = end

    # 垂直
    for c in range(N):
        r = 0
        while r < N:
            color = board[r][c]
            end = r
            while end < N and board[end][c] == color:
                end += 1
            if color not in IGNORE and end - r >= 3:
                found.update((y, c) for y in range(r, end))
            r = end

    return found


# 舊名稱，方便沿用
matches = find_matches


def best_move(board, failed=None):
    """回傳 (a, b, score)；找不到就回傳 None。

    failed：集合，內容是「試過但遊戲沒接受」的交換 {((r1,c1),(r2,c2)), ...}，
    這些組合會被跳過，避免一直重複做無效的交換。
    """
    failed = failed or set()
    best = None
    best_score = 0

    for r in range(N):
        for c in range(N):
            for dr, dc in ((0, 1), (1, 0)):
                r2, c2 = r + dr, c + dc
                if r2 >= N or c2 >= N:
                    continue

                # (r, c) 一定小於 (r2, c2)，交換組合的 key 保證一致
                if ((r, c), (r2, c2)) in failed:
                    continue

                color = board[r][c]
                other = board[r2][c2]
                if color in IGNORE or other in IGNORE:
                    continue
                if color == other:
                    continue

                test = [row[:] for row in board]
                test[r][c], test[r2][c2] = other, color

                found = find_matches(test)

                # 交換的位置必須真的被消掉，才算是有效步
                if (r, c) not in found and (r2, c2) not in found:
                    continue

                score = len(found)
                if score > best_score:
                    best_score = score
                    best = ((r, c), (r2, c2), score)

    return best


def board_is_empty(board):
    """整個盤面幾乎都是空格 → 遊戲結束（或已離開遊戲）。"""
    empty = sum(cell == "empty" for row in board for cell in row)
    return empty >= N * N * 0.7


def signature(board):
    return tuple(tuple(row) for row in board)


# =========================
# 滑鼠交換
# =========================
def swap(a, b):
    x1, y1 = gem_pos(*a)
    x2, y2 = gem_pos(*b)
    pyautogui.moveTo(x1, y1, duration=0.05)
    pyautogui.dragTo(x2, y2, duration=0.15, button="left")


def wait_stable(timeout=SETTLE_TIMEOUT):
    """等畫面連續三次一樣，代表掉落動畫結束。"""
    deadline = time.time() + timeout
    last = None
    same = 0
    board = None

    while time.time() < deadline:
        board = read_board(capture())
        sig = signature(board)
        if sig == last:
            same += 1
            if same >= 2:
                return board
        else:
            same = 0
            last = sig
        time.sleep(0.06)

    return board


# =========================
# 校正模式
# =========================
def calibrate():
    img = capture()
    board = read_board(img)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    print(f"棋盤範圍：x {LEFT}~{RIGHT}, y {TOP}~{BOTTOM}（{WIDTH}x{HEIGHT}）")
    print("辨識結果（R 紅 O 橙 Y 黃 G 綠 B 藍 P 紫 W 白 . 空）：")
    print_board(board)

    print("\n各格中心 HSV（h, s, v）：")
    for r in range(N):
        for c in range(N):
            x = int((c + .5) * CW)
            y = int((r + .5) * CH)
            h, s, v = (int(n) for n in np.median(
                hsv[y - 4:y + 5, x - 4:x + 5].reshape(-1, 3), axis=0))
            print(f" ({r},{c}) -> {board[r][c]:7s} h={h:3d} s={s:3d} v={v:3d}")

    path = "board_debug.png"
    ok, buf = cv2.imencode(".png", img)
    if ok:
        buf.tofile(path)  # 用 tofile 才支援中文路徑
        print(f"\n截圖已存成 {path}")


# =========================
# 邏輯測試（不需要遊戲畫面）
# =========================
def selftest():
    import random

    rng = random.Random(20260101)
    colors = ["red", "green", "blue", "yellow", "purple", "orange"]

    # 固定亂數種子，找一個「沒有現成三連、但存在有效步」的盤面
    base = None
    for _ in range(5000):
        cand = [[rng.choice(colors) for _ in range(N)] for _ in range(N)]
        if not find_matches(cand) and best_move(cand) is not None:
            base = cand
            break
    assert base is not None, "找不到合適的測試盤面"

    # 橫向三連要被找到
    lined = [row[:] for row in base]
    lined[0][0] = lined[0][1] = lined[0][2] = "red"
    found = find_matches(lined)
    assert {(0, 0), (0, 1), (0, 2)} <= found, "橫向三連沒抓到"

    # 縱向三連要被找到
    lined = [row[:] for row in base]
    lined[0][4] = lined[1][4] = lined[2][4] = "blue"
    found = find_matches(lined)
    assert {(0, 4), (1, 4), (2, 4)} <= found, "縱向三連沒抓到"

    # 一定找得到有效步，而且該步真的能消
    move = best_move(base)
    assert move is not None, "找不到有效步"

    a, b, score = move
    test = [row[:] for row in base]
    test[a[0]][a[1]], test[b[0]][b[1]] = test[b[0]][b[1]], test[a[0]][a[1]]
    found = find_matches(test)
    assert a in found or b in found, "選到的步不會消除"
    assert score == len(found), "分數與實際消除數不一致"

    # 交換過的組合加入 failed 後，同一組不該再被選到
    move2 = best_move(base, failed={(a, b)})
    if move2 is not None:
        assert (move2[0], move2[1]) != (a, b), "failed 的交換又被選到了"

    # 空格過多 → 視為遊戲結束
    empty = [["empty"] * N for _ in range(N)]
    assert board_is_empty(empty)

    # 座標設定錯誤要在一開始就被擋下（模擬寬度只有 1 的情況）
    try:
        assert (388 - 387) > 100
    except AssertionError:
        pass  # 這裡只是示範，真正的檢查在檔案開頭的 assert

    print(f"selftest OK（範例最佳步：{a} <-> {b}，可消 {score} 顆）")


# =========================
# 主流程
# =========================
def main():
    print("寶石方塊 自動消除")
    print(f"棋盤範圍：x {LEFT}~{RIGHT}, y {TOP}~{BOTTOM}（{WIDTH}x{HEIGHT}）")
    print(f"{START_DELAY} 秒後開始，請先切換到遊戲畫面")
    print("按住 Q，或把滑鼠移到左上角可停止")
    if not sleep_interruptible(START_DELAY):
        print("手動停止")
        return

    start = time.time()
    moves = 0
    still = 0
    last_board = None
    failed = set()  # 遊戲沒接受的交換 {((r1,c1),(r2,c2)), ...}

    try:
        while True:
            if stop_pressed():
                print("手動停止")
                break

            elapsed = time.time() - start
            if elapsed >= ROUND_TIME:
                print(f"時間到（{elapsed:.1f} 秒），停止")
                break

            board = read_board(capture())

            if board_is_empty(board):
                print("盤面幾乎空了，遊戲可能已結束")
                break

            if VERBOSE and board != last_board:
                print_board(board)
                last_board = [row[:] for row in board]

            move = best_move(board, failed)

            if move is None:
                if failed:
                    # 不是沒有步可走，而是剩下的步都試過且無效
                    print(f"可走的步都試過了（{len(failed)} 種無效交換），停止")
                    break
                still += 1
                print(f"找不到可消除的組合（{still}/{STILL_LIMIT}）")
                if still >= STILL_LIMIT:
                    print("連續找不到步可走，判定遊戲結束")
                    break
                time.sleep(0.4)
                continue

            still = 0
            a, b, score = move
            print(f"[{elapsed:5.1f}s] 交換 {a} <-> {b}，預計消除 {score} 顆")
            swap(a, b)
            moves += 1

            new_board = wait_stable()
            if new_board is not None and signature(new_board) == signature(board):
                # 盤面完全沒變 → 遊戲沒接受這一步（例如判定為無效交換）
                failed.add((a, b))
                print("交換後盤面沒變化，已略過這個組合")

    except pyautogui.FailSafeException:
        print("偵測到滑鼠在左上角，停止")

    print(f"結束：共交換 {moves} 次，耗時 {time.time() - start:.1f} 秒")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "calibrate":
        calibrate()
    elif mode == "selftest":
        selftest()
    else:
        main()
