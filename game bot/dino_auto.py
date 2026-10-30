import pyautogui as pyg


SAMPLE_POINT = (190, 420)
TARGET_COLOR = (83, 83, 83)
COLOR_TOLERANCE = 12
POLL_INTERVAL = 0.01


def is_target_color(color):
    return all(
        abs(actual - target) <= COLOR_TOLERANCE
        for actual, target in zip(color, TARGET_COLOR)
    )


def main():
    pyg.FAILSAFE = True
    print("恐龍自動跳躍即將啟動；請切換到恐龍遊戲視窗。")
    pyg.sleep(2)

    was_obstacle_detected = False
    try:
        while True:
            pixel = pyg.screenshot(
                region=(SAMPLE_POINT[0], SAMPLE_POINT[1], 1, 1)
            ).getpixel((0, 0))
            obstacle_detected = is_target_color(pixel)

            if obstacle_detected and not was_obstacle_detected:
                pyg.press("space")

            was_obstacle_detected = obstacle_detected
            pyg.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n恐龍自動跳躍已停止。")


if __name__ == "__main__":
    main()
