# 正式上線 TODO（剩餘事項）

> 程式碼與範本層的優化已全部完成（見 git 歷史）。本檔只保留**尚未完成**的事項。
> 完整部署步驟見 `deploy/SETUP.md`。

---

## 🔴 上線前必做（只有你能做）

- [ ] **輪換祕密** — 在 `.env` 換上全新的 `SECRET_KEY` 與 `ADMIN_ACCESS_KEY`；前端 `.env` 的
      `VITE_ADMIN_ACCESS_KEY` 同步。舊值已洩漏在 git 歷史，**絕不可沿用**。
  - `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

## 🟠 部署時的手動動作（非程式碼，需主機環境）

- [ ] 套用 `deploy/egress-firewall.sh.example`（主機 root 執行 + 持久化），封靶機對外連線。
- [ ] 套用 `deploy/nginx.conf.example`（填值後放 `/etc/nginx/conf.d/`）。
- [ ] 要開錯誤監控時，設後端 `SENTRY_DSN` 與前端 `VITE_SENTRY_DSN`。

---

## 已決議「不做」（避免日後重提）

- **N-35 防作弊** — 受限於固定 flag 可分享、無 email 可多開；學習平台作弊誘因低，維持不防。
- **P2-21 port 耗盡** — 單機 + 容量上限 30 下幾乎不可能耗盡，不處理。
- **N-24 cap_drop** — egress 防火牆已達成擋跳板/挖礦，`cap_drop:ALL` 破壞風險高，不做。
- **N-26 鏡像來源強制** — 管理員本人自判鏡像安全，不做程式白名單。
- **N-34 secrets vault** — 內網單機，主機 `.env`(權限 600) 已足夠。

## 決策紀錄（背景）

- 答案模型維持固定字串；每個 lab 個案處理 docker，無天生固定答案者由出題者設計成
  攻擊成功後吐出固定 flag，lab 純當靶機。
- **只在內網單機使用** → 免反向代理 of 靶機；靶機 port 綁主機內網 IP；前端 nginx 同機 HTTP。
- 單機部署、接受啟動全域序列化、不做備份、忘記密碼=重辦、容量依硬體、新題用現成 docker。
- 監控用 Sentry；CI 用 GitHub Actions。
