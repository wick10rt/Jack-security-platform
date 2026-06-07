# 正式上線優化清單 (TODO)

> 來源：對 `backend/` `frontend/` `labs/` 現況的程式碼檢視，對照 `word.docx` 設計書。
> 狀態圖示：⬜ 未開始　🟦 進行中　✅ 完成

---

## ✅ 已完成 (2026-06-07，已測試)

> 測試環境：venv + Postgres/Redis(docker-compose)，`manage.py check` 通過，
> `core` 24 個單元測試全綠，前端 `type-check` + `build` 通過，compose schema 端到端驗證合法。

- ✅ **P0-1 靶機遠端存取（內網版）** — 改用 `INSTANCE_BIND_HOST`(綁定) + `INSTANCE_PUBLIC_HOST`(回傳網址)；單機內網只要把兩者設成主機內網 IP，同網段即可連靶機，免反向代理。
- ✅ **P1-9 mysql 升級** — 預設 `INSTANCE_DB_IMAGE=mysql:8.0`，預設模板加 `--default-authentication-plugin=mysql_native_password` 維持舊 PHP 靶機相容。
- ✅ **P1-10 靶機狀態回報** — `ActiveInstance` 加 `status`(creating/running/error) 取代 `"creating..."` 字串；失敗保留 row 標 error，前端輪詢顯示「啟動失敗」，relaunch 自動清除舊 error。migration `0003`。
- ✅ **P2-16 描述 XSS** — `lab.description` 的 `v-html` 改用 DOMPurify 淨化（社群解法本就由 Vue 自動轉義）。
- ✅ **P2-17 / N-29 JWT 撤銷** — 加 `token_blacklist` app、`/api/auth/logout/` 登出撤銷 refresh、access 壽命縮短為 30 分（env 可調）；**順手補上缺失的 `/api/auth/token/refresh/` 路由**（前端原本 refresh 是壞的）。
- ✅ **P2-20 靶機延長時間** — `/api/instances/extend/`，每次 +30 分、上限 2 次（env 可調），前端加延長按鈕。
- ✅ **N-25 孤兒容器對帳** — `reconcile_instances` Celery Beat（每 5 分）：依 compose project label 雙向對帳，清孤兒容器；DB 卡 `creating` 逾寬限期標 error。

- ✅ **P1-8 / N-23 靶機 compose 模板彈性化** — `Lab` 新增 `compose_template`/`web_service`/`web_port`；`build_compose_content` 支援每題自帶 compose（空則用預設 web+mysql），平台**強制注入** cpus/mem/pids/security_opt/restart 並**移除** 作者的 ports/privileged/cap_add，只開受控 `127.0.0.1::<web_port>`。已用 Juice Shop 單容器案例端到端驗證（無 db、移除 privileged、改寫開埠）。migration `0002`。

- ✅ **P0-2 DEBUG env 化** — `settings.py` `DEBUG = env("DEBUG")`（預設 False）。
- ✅ **P0-3 ALLOWED_HOSTS env 化** — `env.list(...)`。
- ✅ **P0-4 HTTPS / 安全標頭** — `not DEBUG` 時啟用 SSL redirect / Secure cookies / HSTS / nosniff / CSRF_TRUSTED_ORIGINS；`check --deploy` 在 DEBUG=False 下零警告。
- ✅ **P0-5 Admin 金鑰移出程式碼** — 改讀 `settings.ADMIN_ACCESS_KEY`(env)，留空則停用繞過。
- ✅ **P0-6 靜態檔策略** — `STATIC_ROOT` + whitenoise（`STORAGES` + middleware），collectstatic 驗證通過。
- ✅ **P0-7 DB 帳密/位址 env 化** — NAME/USER/HOST/PORT 皆 env 帶預設。
- ✅ **P1-12 答案/註冊節流** — DRF `ScopedRateThrottle`，register 10/hour、submit 30/min；429 觸發已單元測試。
- ✅ **P1-13 魔術數字集中** — 靶機 limit/expiry/cpu/mem/image/pids 移到 settings（env 可調）。
- ✅ **P1-14 logging 設定** — 完整 `LOGGING`（console handler，env 可調 level）。
- ✅ **P1-15 核心流程測試** — 註冊/登入/答題/反思/解法門檻/靶機擁有權/健康檢查/節流共 15 測。
- ✅ **P2-18 健康檢查端點** — `GET /api/health/`（含 DB 探測）。
- ✅ **P2-19 DB 連線復用** — `CONN_MAX_AGE`。
- ✅ **P2-22 去重擁有權檢查** — 抽出 `IsInstanceOwner` permission，StatusView/AccessView 共用。
- ✅ **N-27 容量可配置** — `ACTIVEINSTANCE_LIMIT` env 化（依硬體調整）。
- ✅ **N-28 時區一致性** — `TIME_ZONE=Asia/Taipei` 對齊 Celery。
- ✅ **N-33 i18n** — `LANGUAGE_CODE=zh-hant`。
- ✅ **(順手) CORS / Celery broker URL env 化** — 部署靈活性。
- ✅ **N-30 CI/CD** — `.github/workflows/ci.yml`：後端 test（CI 起 postgres+redis 用 env 接）+ 前端 type-check + build。
- ✅ **N-31 監控** — 整合 Sentry：後端 `settings`(Django+Celery integration，`SENTRY_DSN` 啟用) + 前端 `main.ts`(`VITE_SENTRY_DSN`)；未設 DSN 完全 no-op。
- ✅ **N-32 SPA serve** — `deploy/nginx.conf.example`：服務 `dist/` + 反代 `/api` `/admin` `/static`，HTTP + SPA fallback。
- ✅ **P1-11/N-24 濫用防護** — `deploy/egress-firewall.sh.example`（DOCKER-USER 封容器外連、放行回程）+ 既有 `no-new-privileges`/`pids_limit`/移除 `privileged`+`cap_add`/資源限制。**cap_drop 決議先不做**（egress 防火牆已達成擋跳板/挖礦目標，cap_drop:ALL 破壞風險高）。

---

## ✅ 已決議結案 / 不做

- **N-24 cap_drop** — 先不做（egress 防火牆已達成擋跳板/挖礦，cap_drop:ALL 破壞風險高）。
- **N-26 鏡像來源信任** — 管理員為本人、自行判斷鏡像安全，不做程式強制。
- **N-34 secrets 管理** — 內網單機，主機 `.env`(權限 600) 已足夠，不導入 vault。
- **P2-21 port 耗盡** — 單機 + 容量上限 30 下風險極低，不處理。
- **N-35 防作弊（低優先）** — 答案分享 / 多開帳號 / 抄襲社群解法，先擱置。

---

## 📋 剩餘皆為部署時的手動動作（非程式碼）

- 套用 `deploy/egress-firewall.sh.example`（主機 root，並持久化）
- 套用 `deploy/nginx.conf.example`（填值後放 /etc/nginx/conf.d/）
- 設 `SENTRY_DSN` / `VITE_SENTRY_DSN`（要啟用監控時）
- ⚠️ **輪換祕密**：`.env` 換上全新 `SECRET_KEY` 與 `ADMIN_ACCESS_KEY`（舊值已洩漏在 git 歷史）

---

## 決策紀錄

- 答案模型維持固定字串（Q1/Q12）；**每個 lab 個案處理 docker，無天生固定答案者由出題者設計成攻擊成功後吐出固定 flag，lab 純當靶機**；單機部署（Q4）；**只在內網使用** → 免反向代理，靶機 port 綁主機內網 IP；接受啟動全域序列化（Q5）；不做備份（Q11）；忘記密碼=重辦（Q8）；容量依硬體（Q3）；新題用現成 docker（Q6）、題型越多越好（Q7）。
- **部署提醒（內網）**：`.env` 設 `INSTANCE_BIND_HOST` 與 `INSTANCE_PUBLIC_HOST` = 主機內網 IP；前端 nginx 同機 HTTP，故 `DEBUG=False` 時要設 `SECURE_SSL_REDIRECT=False`（否則強制轉址 https）。
- **基建決策（2026-06-07 grill）**：N-26 信任管理員自判鏡像、不強制；N-24 靶機完全封鎖外連 + cap_drop:ALL；N-31 用 Sentry；N-32 nginx 同機 HTTP；N-30 GitHub Actions；N-34 `.env` 即可。
- ⚠️ **尚未輪換的祕密**：洩漏在 git 歷史的舊 `SECRET_KEY` 與舊 admin 金鑰 `@1121717...`，正式上線前務必在 `.env` 換成全新值（程式碼已就緒，值需你自己填）。
