# 115-programming
2026/10/6

## Chrome 小恐龍自動跳躍

使用 `game bot/dino_auto.py` 偵測指定螢幕座標的像素顏色，並在偵測到障礙物時按下空白鍵。

1. 若尚未安裝 PyAutoGUI，執行：

   ```powershell
   conda run -n iem_python python -m pip install pyautogui
   ```

2. 開啟 Chrome 小恐龍遊戲，讓遊戲視窗保持可見。
3. 在終端機執行：

   ```powershell
   conda run -n iem_python python "game bot\dino_auto.py"
   ```

程式預設偵測座標 `(1220, 414)`，目標色為 `(83, 83, 83)`，並允許每個 RGB 色彩通道有 12 的誤差。若未觸發，請依遊戲視窗位置調整 [dino_auto.py](game%20bot/dino_auto.py) 中的 `SAMPLE_POINT` 和 `TARGET_COLOR`。按 `Ctrl+C` 可停止；將滑鼠移到螢幕左上角也會觸發 PyAutoGUI 的安全停止機制。
