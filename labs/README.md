# labs/ — 靶機原始碼放這裡（佔位）

這個資料夾是**出題用的工作區**：架設本系統的人在這裡放自己靶機的
build 原始碼（每題一個子資料夾，自帶 `Dockerfile`，需要的話加上開發測試用的
`docker-compose.yml`）。

平台執行時**不會讀這個資料夾** —— 它只認 Django admin 裡 `Lab.docker_image`
指到的鏡像（先 build & push 到 registry，或 `docker build` 進本機）。
建題流程與欄位說明見 `deploy/SETUP.md` 第 9 節。

## 建議結構

```
labs/
└── my-lab/
    ├── Dockerfile            # 靶機鏡像（設定/程式碼烤進鏡像，平台不掛主機檔）
    ├── docker-compose.yml    # （選用）本機開發測試用；平台會自行生成正式 compose
    └── src/ ...              # 漏洞應用程式碼
```

## 注意事項

- 平台會強制覆寫資源/安全限制，並剝除 `ports`/`volumes`/`privileged` 等
  主機相關設定（見 `backend/core/tasks.py` 的 `STRIPPED_SERVICE_KEYS`），
  所以鏡像必須自給自足。
- 固定答案題：靶機在攻擊成功時要能吐出固定 flag；純沙盒題把 Lab 的
  `requires_answer` 取消勾選即可。
- 歷史範例（sqli-labs 系列的 boolean/time-based blind）可從 git 歷史取回：
  `git log --oneline -- labs/`。
