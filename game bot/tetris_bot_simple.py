"""
俄羅斯方塊 bot：從畫面、試算到按鍵的教學範例。
使用方式 python tetris_bot_simple.py --check 先檢查座標與辨識 NEXT
使用方式 python tetris_bot_simple.py --play 讓 bot 自動玩遊戲
"""

import sys
import time

import pyautogui


# 先用 capture_coordinates.py 量好，再填入自己的螢幕座標。
# 左上、右上都是盤面「內側」邊界；格子高度依照盤面寬度推算。
BOARD_TOP_LEFT = (169,208)# 例如 (246, 233)
BOARD_TOP_RIGHT = (491, 208)# 例如 (556, 233)
# 框住 NEXT 最上面的一塊，不要包含第二塊。
NEXT_TOP_LEFT = (516,263)
NEXT_BOTTOM_RIGHT = (576, 326)

ROWS, COLS = 20, 10
START_DELAY = 5            # 切回遊戲的時間
SETTLE_DELAY = 0.5         # 等落地和消行動畫；請依畫面調整
RETRY_DELAY = 0.2          # 盤面不一致時，隔多久再拍一次
RETRY_COUNT = 2            # 最多重新拍幾次（不含第一次）
KEY_DELAY = 0.05
EMPTY_MAX_SUM = 140        # 黑色是 (0, 0, 0)；容許截圖有少量雜訊
COLOR_DISTANCE = 40
MIN_COLOR_PIXELS = 10
TOP_ROWS_TO_IGNORE = 4     # 畫面上正在下落的新方塊，不算已落地方塊

# 每種方塊的初始方向。1 代表有方塊，0 代表空白。
SHAPES = {
    "I": [[1, 1, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "Z": [[1, 1, 0], [0, 1, 1]],
}

# 這是 NEXT 的顏色，盤面上方塊的顏色不一定相同。
COLORS = {
    "I": (0, 221, 242), "J": (0, 106, 254),
    "L": (254, 127, 0), "O": (255, 233, 2),
    "S": (8, 216, 10), "T": (171, 46, 204), "Z": (228, 33, 11),
}

# 初始方向、順時針轉 1、2、3 次之後的左邊界欄號。
# 遊戲可能因轉向、牆或障礙物而產生位移；實際結果仍須檢查。
START_COLS = {
    "I": [3, 5], "J": [3, 4, 3, 3], "L": [3, 4, 3, 3],
    "O": [4], "S": [3, 4], "T": [3, 4, 3, 3], "Z": [3, 4],
}


def check_settings():
    """座標未填好時停止，避免對錯誤的位置取樣。"""
    points = (BOARD_TOP_LEFT, BOARD_TOP_RIGHT, NEXT_TOP_LEFT, NEXT_BOTTOM_RIGHT)
    if any(p is None for p in points):
        raise ValueError("請先在程式開頭填好盤面與 NEXT 的四個座標。")
    if BOARD_TOP_RIGHT[0] <= BOARD_TOP_LEFT[0]:
        raise ValueError("盤面右上角必須在左上角的右邊。")
    if abs(BOARD_TOP_RIGHT[1] - BOARD_TOP_LEFT[1]) > 2:
        raise ValueError("盤面左右上角高度不同，請重新量測。")
    if (NEXT_BOTTOM_RIGHT[0] <= NEXT_TOP_LEFT[0]
            or NEXT_BOTTOM_RIGHT[1] <= NEXT_TOP_LEFT[1]):
        raise ValueError("NEXT 矩形的座標不正確。")


def cell_center(row, col):
    """第 row 列、第 col 欄的中心點，列和欄都從 0 開始。"""
    size = (BOARD_TOP_RIGHT[0] - BOARD_TOP_LEFT[0]) / COLS
    x = BOARD_TOP_LEFT[0] + (col + 0.5) * size
    y = BOARD_TOP_LEFT[1] + (row + 0.5) * size
    return round(x), round(y)


def read_board(image):
    """看每格中心是否接近黑色；回傳 20 列、10 欄的 0/1 清單。"""
    board = []
    for row in range(ROWS):
        line = []
        for col in range(COLS):
            rgb = image.getpixel(cell_center(row, col))[:3]
            line.append(0 if sum(rgb) <= EMPTY_MAX_SUM else 1)
        board.append(line)
    return board


def read_next(image):
    """掃描 NEXT 第一塊的矩形，票數最多的顏色代表方塊種類。"""
    votes = {name: 0 for name in COLORS}
    for y in range(NEXT_TOP_LEFT[1], NEXT_BOTTOM_RIGHT[1], 2):
        for x in range(NEXT_TOP_LEFT[0], NEXT_BOTTOM_RIGHT[0], 2):
            rgb = image.getpixel((x, y))[:3]
            for name, color in COLORS.items():
                distance = sum((rgb[i] - color[i]) ** 2 for i in range(3))
                if distance <= COLOR_DISTANCE ** 2:
                    votes[name] += 1
                    break
    winner = max(votes, key=votes.get)
    return (winner if votes[winner] >= MIN_COLOR_PIXELS else None), votes


def rotate(shape):
    """順時針旋轉 90 度。"""
    return [list(row) for row in zip(*shape[::-1])]


def rotations(shape):
    """依轉動次數列出不重複的形狀。"""
    result = []
    while shape not in result:
        result.append(shape)
        shape = rotate(shape)
    return result


def fits(board, shape, row, col):
    """這個位置會不會出界或碰到已落地的方塊？"""
    for r in range(len(shape)):
        for c in range(len(shape[0])):
            if shape[r][c]:
                y, x = row + r, col + c
                if y < 0 or y >= ROWS or x < 0 or x >= COLS or board[y][x]:
                    return False
    return True


def drop_row(board, shape, col):
    """從頂端一直往下試，回傳最後停住的列；放不下則回傳 None。"""
    if not fits(board, shape, 0, col):
        return None
    row = 0
    while fits(board, shape, row + 1, col):
        row += 1
    return row


def place_and_clear(board, shape, row, col):
    """複製盤面、放入方塊、消掉滿行；不修改原盤面。"""
    new_board = [line[:] for line in board]
    for r in range(len(shape)):
        for c in range(len(shape[0])):
            if shape[r][c]:
                new_board[row + r][col + c] = 1
    remaining = [line for line in new_board if 0 in line]
    cleared = ROWS - len(remaining)
    return [[0] * COLS for _ in range(cleared)] + remaining, cleared


def count_holes(board):
    """同一欄中，上面已經有方塊的空格稱為洞。"""
    holes = 0
    for col in range(COLS):
        covered = False
        for row in range(ROWS):
            if board[row][col]:
                covered = True
            elif covered:
                holes += 1
    return holes


def choose_move(board, piece):
    """試所有方向與欄位，回傳最高分的 (分數, 轉幾次, 欄, 列, 新盤面)。"""
    best = None
    for turns, shape in enumerate(rotations(SHAPES[piece])):
        for col in range(COLS - len(shape[0]) + 1):
            row = drop_row(board, shape, col)
            if row is None:
                continue
            after, cleared = place_and_clear(board, shape, row, col)
            score = row + 100 * cleared - 50 * count_holes(after)
            if best is None or score > best[0]:
                best = (score, turns, col, row, after)
    return best


def send_move(piece, turns, col):
    """先轉、再水平移動、最後按空白鍵直接落下。"""
    for _ in range(turns):
        pyautogui.press("up")
        time.sleep(KEY_DELAY)
    distance = col - START_COLS[piece][turns]
    for _ in range(abs(distance)):
        pyautogui.press("right" if distance > 0 else "left")
        time.sleep(KEY_DELAY)
    pyautogui.press("space")


def show_board(board):
    print("   0123456789")
    for row, line in enumerate(board):
        print(f"{row:2} " + "".join("#" if cell else "." for cell in line))


def check_board(expected):
    """核對試算盤面；暫時不一致時重拍，回傳（是否一致, 最後的畫面盤面）。"""
    for attempt in range(RETRY_COUNT + 1):
        actual = read_board(pyautogui.screenshot())
        if actual[TOP_ROWS_TO_IGNORE:] == expected[TOP_ROWS_TO_IGNORE:]:
            if attempt > 0:
                print(f"重新檢查第 {attempt} 次後，盤面一致，繼續。")
            return True, actual
        if attempt < RETRY_COUNT:
            print(f"盤面暫時不一致，等待 {RETRY_DELAY} 秒後重新檢查。")
            time.sleep(RETRY_DELAY)
    return False, actual


def countdown():
    print(f"{START_DELAY} 秒後讀取畫面，請切回遊戲並確認遊戲有鍵盤焦點。")
    time.sleep(START_DELAY)


def inspect_screen():
    """只觀察，不發出遊戲按鍵。"""
    countdown()
    image = pyautogui.screenshot()
    show_board(read_board(image))
    piece, votes = read_next(image)
    print(f"NEXT 辨識結果：{piece}；各顏色票數：{votes}")


def play():
    """從新遊戲開始：記住 NEXT，放棄第一塊，之後重複試算與執行。"""
    countdown()
    image = pyautogui.screenshot()
    board = read_board(image)
    if any(any(line) for line in board[TOP_ROWS_TO_IGNORE:]):
        print("盤面下方不是空的；請從新的遊戲開始，並檢查座標。")
        return
    current, _ = read_next(image)
    if current is None:
        print("無法辨識 NEXT，請先執行 --check。")
        return
    print(f"記住下一塊 {current}，讓第一塊直接落下。")
    pyautogui.press("space")
    time.sleep(SETTLE_DELAY)
    board = read_board(pyautogui.screenshot())
    # 新遊戲的第一塊落下後，下方應該剛好多出四格。
    if sum(sum(line) for line in board[TOP_ROWS_TO_IGNORE:]) != 4:
        print("第一塊落地後未讀到四格，停止；請檢查焦點、座標和等待時間。")
        return
    board[:TOP_ROWS_TO_IGNORE] = [[0] * COLS for _ in range(TOP_ROWS_TO_IGNORE)]

    while True:
        next_piece, _ = read_next(pyautogui.screenshot())
        if next_piece is None:
            print("無法辨識下一塊，停止。")
            return
        move = choose_move(board, current)
        if move is None:
            print("沒有可放的位置，停止。")
            return
        score, turns, col, row, expected = move
        print(f"{current}：轉 {turns} 次，放第 {col} 欄、第 {row} 列，評分 {score}", flush=True)
        send_move(current, turns, col)
        time.sleep(SETTLE_DELAY)
        if any(any(line) for line in expected[:TOP_ROWS_TO_IGNORE]):
            print("堆疊已接近頂端，無法安全排除下落中的方塊，停止。")
            return
        matches, actual = check_board(expected)
        if not matches:
            print("重新檢查後，實際盤面仍與試算不同，停止。請檢查座標、按鍵和等待時間。")
            print("試算盤面：")
            show_board(expected)
            print("畫面盤面（上方可能包含正在下落的方塊）：")
            show_board(actual)
            return
        board = expected
        current = next_piece


def demo():
    """不讀取螢幕、不按鍵，示範在一個盤面試放 T。"""
    board = [[0] * COLS for _ in range(ROWS)]
    board[-1] = [1, 1, 1, 0, 0, 0, 1, 1, 1, 1]
    print("試算前：")
    show_board(board)
    score, turns, col, row, after = choose_move(board, "T")
    print(f"T：轉 {turns} 次，放第 {col} 欄、第 {row} 列，評分 {score}")
    print("試算後：")
    show_board(after)


if __name__ == "__main__":
    try:
        if len(sys.argv) == 1:
            demo()
        elif sys.argv[1:] == ["--check"]:
            check_settings()
            inspect_screen()
        elif sys.argv[1:] == ["--play"]:
            check_settings()
            play()
        else:
            print("用法：不加參數試算，或使用 --check / --play")
    except (pyautogui.FailSafeException, KeyboardInterrupt):
        print("\n已停止。")
    except ValueError as error:
        print(f"設定有誤：{error}")
