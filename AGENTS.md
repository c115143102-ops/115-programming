# AGENTS.md

Repo is greenfield: only `README.md` and Python `.gitignore` exist. No source, manifests, toolchain, CI, or tests yet.

- 所有的回應一律使用繁體中文。
- 專案語言為 Python，使用 conda 管理套件，環境名稱為 `iem_python`；執行或安裝前先 `conda activate iem_python`（非互動式改用 `conda run -n iem_python ...`）。

- Repo 現況接近 greenfield：僅有 `README.md`、Python `.gitignore`，尚無 manifests、toolchain、CI 或測試。
- 尚無已驗證的 build / test / lint 指令；新增前勿臆測，一律以實際加入的 manifests 或設定為準。
- `.gitignore` 為標準 Python 範本（涵蓋 `__pycache__/`、`.venv/`、`venv/`、`.pytest_cache/` 等）。
