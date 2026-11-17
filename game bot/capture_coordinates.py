# 用來捕捉滑鼠座標的程式，按住 Ctrl + 滑鼠右鍵可以記錄目前滑鼠位置，按 Ctrl+C 結束程式，最後會列出所有記錄的座標，並計算前兩個座標的寬度、高度和中心點。
# 使用這支程式，要先安G裝 pynput 套件，安裝方式：pip install pynput
import ctypes
import signal
import sys
import threading

from pynput import keyboard, mouse

positions: list[tuple[float, float]] = []
_positions_lock = threading.Lock()

ctrl_held = False
_ctrl_lock = threading.Lock()

_CTRL_KEYS = (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r)


def on_press(key):
    global ctrl_held
    if key in _CTRL_KEYS:
        with _ctrl_lock:
            ctrl_held = True


def on_release(key):
    global ctrl_held
    if key in _CTRL_KEYS:
        with _ctrl_lock:
            ctrl_held = False


def on_click(x, y, button, pressed):
    if not pressed or button != mouse.Button.right:
        return
    with _ctrl_lock:
        holding_ctrl = ctrl_held
    if not holding_ctrl:
        return
    with _positions_lock:
        positions.append((x, y))
    print(f"已記錄: ({x}, {y})", flush=True)


def _ignore_ctrl_c():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    if sys.platform == "win32":
        ctypes.windll.kernel32.SetConsoleCtrlHandler(None, 1)


def main():
    print("按住 Ctrl + 滑鼠右鍵：記錄目前滑鼠位置", flush=True)
    print("按 Ctrl+C 結束程式", flush=True)

    keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    mouse_listener = mouse.Listener(on_click=on_click)

    try:
        keyboard_listener.start()
        mouse_listener.start()
        while mouse_listener.is_alive() and keyboard_listener.is_alive():
            mouse_listener.join(0.1)
    except KeyboardInterrupt:
        _ignore_ctrl_c()
        print("\n收到 Ctrl+C，結束中…", flush=True)
    finally:
        mouse_listener.stop()
        keyboard_listener.stop()
        for listener in (mouse_listener, keyboard_listener):
            if listener.ident is not None:
                listener.join(timeout=2)

        print("\n所有記錄的座標：", flush=True)
        for index, (x, y) in enumerate(positions, 1):
            print(f"{index}. ({x}, {y})", flush=True)
        print(f"共 {len(positions)} 個座標", flush=True)


        # 取前 2 個座標出來
        if len(positions) >= 2:
            print(f"\n前兩個座標：({positions[0][0]}, {positions[0][1]}), ({positions[1][0]}, {positions[1][1]})", flush=True)
            # 計算寬度和高度
            width = abs(positions[1][0] - positions[0][0])
            height = abs(positions[1][1] - positions[0][1])
            print(f"寬度: {width}, 高度: {height}", flush=True)
            # 計算中心點
            center_x = (positions[0][0] + positions[1][0]) / 2
            center_y = (positions[0][1] + positions[1][1]) / 2
            print(f"中心點: ({center_x}, {center_y})", flush=True)
        else:
            print("\n沒有足夠的座標來顯示前兩個", flush=True)


if __name__ == "__main__":
    main()
