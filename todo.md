# 正式上線 TODO（剩餘事項）

> 程式碼與範本層的優化已全部完成（見 git 歷史）。本檔只保留**尚未完成**的事項。
> 完整部署步驟見 `deploy/SETUP.md`。

---

## 🔴 上線前必做（只有你能做）

- [ ] **輪換祕密** — 在 `.env` 換上全新的 `SECRET_KEY` 與 `ADMIN_ACCESS_KEY`。
      舊值已洩漏在 git 歷史，**絕不可沿用**。
  - `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

## 🟠 部署時的手動動作（非程式碼，需主機環境）

- [ ] **（必做）** 套用 `deploy/egress-firewall.sh.example`（主機 root 執行 + 持久化）：
      封靶機對外連線 + 擋容器直連 host。這是擋「靶機當跳板打別人」的主防線。
- [ ] **（建議）** 開 Docker `userns-remap`（`/etc/docker/daemon.json`），逃逸時容器
      root ≠ host root；開前先在測試機確認你的靶機鏡像仍能啟動。見 `deploy/SETUP.md` §8.1。
- [ ] 套用 `deploy/nginx.conf.example`（填值後放 `/etc/nginx/conf.d/`）。
- [ ] 要開錯誤監控時，設後端 `SENTRY_DSN` 與前端 `VITE_SENTRY_DSN`。

---

## Bug 清單（2026-06-10 診斷 → B1–B10 已修，測試通過）

> B1–B8、B10 已修並通過後端測試 + 真機 v2 compose 驗證；B9 複查後非 bug；B11 維持已知取捨。

### ✅ 已修

- **B1 — compose 指令寫死 `docker-compose`（v1）。** 改用 `settings.DOCKER_COMPOSE_CMD`
  （預設 v2 `docker compose`，可 env 覆寫），`core/tasks.py` 統一走 `_compose()` 助手。
  真機 v2 up/port/ps/down 全驗過。
- **B2 — DRF 節流可被 XFF 偽造繞過。** 設 `REST_FRAMEWORK["NUM_PROXIES"]=1`（env 可調）。
- **B3 — `host_port` 解析脆弱。** 改用 `_extract_host_port()`：取第一個非空行、空輸出丟例外重試。
- **B4 — `pollInstanceStatus` 重複輪詢。** 進入時先 `stopPolling()`，杜絕 setInterval 洩漏。
- **B5 — 空 solution 答案題會被空白答案誤判通過。** `SubmitAnswerView` 加空 solution 擋。
- **B6 — 409 復原後殘留 error toast。** 409 分支清 `error.value` 並改顯示 info。
- **B7 — refresh 失敗時排隊請求 hang。** 失敗時逐一 reject 排隊者。
- **B8 — 關閉→立刻重開可短暫超額。** view 不再立即刪列，改由拆除 task 完成時刪
  （broker 掛了才退回立即刪）。
- **B10 — `run.py` 不等 Redis。** 啟動前加 Redis port 等待。

### ❎ 非 bug（複查結論）

- **B9 — reconcile 誤殺剛建立的容器。** 不成立：DB 列恆在容器之前建立（view 先建列才派
  任務），故運行中的實例永遠不會被當成 orphan；拆除中被 reconcile 重複 down 也是冪等無害。

### ⏳ 維持已知取捨

- **B11 — `LaunchInstanceView` 的 `select_for_update()` 全域序列化 launch。** 量大時是吞吐
  瓶頸，但單機 + 30 台上限下可接受，暫不改（要改得引入 per-user 鎖或樂觀重試）。

## 靶機隔離硬化（已加做 P0+P1）

- Postgres/Redis 改綁 `127.0.0.1`，靶機/LAN 都碰不到（根 `docker-compose.yml`）。
- egress 防火牆補 INPUT 規則（擋容器直連 host）、文件改為**必做**。
- 每個靶機容器強制 `cap_drop` 危險 capabilities（`NET_RAW`/`SYS_ADMIN`/… 可由
  `INSTANCE_CAP_DROP`/`INSTANCE_CAP_ADD` 調整），預設不破壞 apache/mysql。
- userns-remap 寫進 `deploy/SETUP.md` §8.1（選用、建議）。

## 已決議「不做」（避免日後重提）

- **N-35 防作弊** — 受限於固定 flag 可分享、無 email 可多開；學習平台作弊誘因低，維持不防。
- **P2-21 port 耗盡** — 單機 + 容量上限 30 下幾乎不可能耗盡，不處理。
- **N-26 鏡像來源強制** — 管理員本人自判鏡像安全，不做程式白名單。
- **N-34 secrets vault** — 內網單機，主機 `.env`(權限 600) 已足夠。
- **read_only rootfs** — 靶機 ephemeral（≤30 分鐘即銷毀），裝工具/持久化價值低；強制會
  破壞 mysql 與寫檔類題目。跳板/逃逸已由 cap_drop + no-new-privileges + egress 涵蓋，不加。
- **gVisor/Kata、每實例反向代理（P2）** — 真正的 VM/kernel 級隔離與靶機 owner-token
  路由；維運成本高、與「內網單機直連」取捨衝突，MVP 不做，列為日後強化。

## 決策紀錄（背景）

- 答案模型維持固定字串；每個 lab 個案處理 docker。無天生固定答案者：可由出題者設計成
  攻擊成功後吐出固定 flag，或將 Lab 的 `requires_answer` 取消勾選做成純沙盒
  （無答案／省思／完成，純當靶機）。
- **只在內網單機使用** → 免反向代理 of 靶機；靶機 port 綁主機內網 IP；前端 nginx 同機 HTTP。
- 單機部署、接受啟動全域序列化、不做備份、忘記密碼=重辦、容量依硬體、新題用現成 docker。
- 監控用 Sentry；CI 用 GitHub Actions。
