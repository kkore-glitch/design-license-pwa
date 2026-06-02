# 室內裝修工程管理乙級題庫 PWA

這是一個手機可用的靜態 PWA，用於練習「建築物室內裝修工程管理乙級」學科題庫。`12600` 是該職類代碼，不是題數。

## 目前內容

- 題庫來源：勞動部技能檢定中心公開學科測試參考資料 `126002A12.pdf`
- 已匯入題數：668 題
- 可直接進 80 題模擬測驗：626 題
- 需看圖題：42 題，保留在題庫瀏覽與章節練習，但不放入 80 題模擬測驗
- 支援單選與複選題
- 本機複習紀錄：作答次數、錯題、收藏、已掌握

## 本機使用

請用 HTTP 伺服器開啟，避免瀏覽器用 `file://` 阻擋題庫 JSON。

```bash
python3 -m http.server 8000
```

開啟：

```text
http://localhost:8000/
```

## 題庫資料

重新產生題庫：

```bash
/Users/kkore/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_questions.py
```

檢查題庫：

```bash
/Users/kkore/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/check_questions.py
```

## GitHub Pages

此 repo 可直接部署靜態檔。GitHub Actions 會把 repo 根目錄上傳到 Pages。

公開發布前，請確認：

- repo 名稱為 `design-license-pwa`
- Pages 使用 GitHub Actions
- 題庫來源仍以官方公告為主

## 注意事項

- 複習紀錄只存在同一台手機的瀏覽器本機儲存；換手機或清除瀏覽器資料後會消失。
- 需看圖題因 PDF 圖形無法完整轉成可作答畫面，第一版不放入 80 題模擬測驗。
- 解析文字是輔助複習用，正式內容仍以官方公告與考試規定為主。
