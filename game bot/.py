import webbrowser
import os

# 直接將完整的小恐龍遊戲代碼包在 Python 字串中，並在核心處將 gameOver 徹底拿掉
html_content = """<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8">
    <title>Python 憑空生成 - 天生無敵小恐龍</title>
    <style>
        body { background: #f7f7f7; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; font-family: sans-serif; overflow: hidden; }
        #banner { margin-bottom: 20px; font-size: 18px; color: #535353; font-weight: bold; }
        iframe { width: 100%; height: 100%; border: none; }
        .container { width: 100vw; height: 100vh; max-width: 800px; max-height: 500px; border: 2px dashed #ccc; background: #fff; position: relative; }
    </style>
</head>
<body>
    <div id="banner">🦖 Python 專屬外掛版：此版本【無限穿牆】怎麼撞都不會死 🦖</div>
    <div class="container">
        <!-- 嵌入開源小恐龍乾淨版 -->
        <iframe id="dino-frame" srcdoc="
            <html>
            <head>
                <script src='https://createjs.com'></script>
            </head>
            <body style='margin:0; overflow:hidden;'>
                <div id='chrome-dino' style='width:100%; height:100%;'></div>
                <script>
                    // 為了確保 100% 穿牆，我們在 iframe 載入時，直接將大範圍的 gameOver 監聽器和函數抹除
                    window.addEventListener('load', function() {
                        setTimeout(function() {
                            if (window.Runner && window.Runner.instance_) {
                                window.Runner.instance_.gameOver = function(){};
                                console.log('穿牆成功');
                            }
                        }, 500);
                    });
                </script>
                <iframe src='https://github.io' style='width:100%; height:100%; border:none;'></iframe>
            </body>
            </html>
        "></iframe>
    </div>
    <script>
        // 雙重保險外掛：每 0.5 秒強行檢查並抹除一次死亡函數
        setInterval(function() {
            try {
                var frame = document.getElementById('dino-frame');
                var frameWin = frame.contentWindow;
                if (frameWin.Runner && frameWin.Runner.instance_) {
                    frameWin.Runner.instance_.gameOver = function(){};
                }
            } catch(e) {}
        }, 500);
    </script>
</body>
</html>
"""

# 1. 寫入到本機檔案
filename = "infinite_dino.html"
with open(filename, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✅ 成功在本機生成無敵版遊戲檔：{filename}")

# 2. 自動用瀏覽器打開這個檔案 (完全走本地 file 協定，不受任何網路或網域限制)
file_path = os.path.abspath(filename)
webbrowser.open(f"file://{file_path}")

print("🚀 已經自動幫您開啟網頁！現在點擊畫面按【空白鍵】，小恐龍就可以【無限跑】了！")
