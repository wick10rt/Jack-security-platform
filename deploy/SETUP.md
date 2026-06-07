# Jack Security Platform — 內網單機部署指南（從 0 到完全運作）

本指南假設：**一台 Linux 主機、內網使用、純 HTTP**。
全文把主機的內網 IP 寫作 `<HOST_IP>`（例如 `192.168.1.50`），請自行替換。

架構：同一台機器上跑
`nginx(80)` → 前端 `dist/` + 反代 `/api` `/admin` 到 `gunicorn(127.0.0.1:8000)`；
`Celery worker/beat` 負責靶機；`Postgres(25000)` + `Redis(6379)` 由 docker-compose 提供；
靶機容器各自綁 `<HOST_IP>:<隨機port>`，使用者直接連。

---

## 0. 安裝系統相依套件

```bash
# 範例為 Debian/Ubuntu，其他發行版請對應
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm nginx git \
                    docker.io docker-compose-plugin
sudo systemctl enable --now docker

# 讓「將來跑 Celery 的使用者」能操作 docker（靶機是 Celery shell-out 起的）
sudo usermod -aG docker $USER
# 重新登入讓群組生效
```

需求：Python 3.12+、Node 20+、Docker + Docker Compose v2、nginx。

---

## 1. 取得程式碼

```bash
git clone https://github.com/wick10rt/Jack-security-platform.git
cd Jack-security-platform
```

---

## 2. 啟動基礎設施（Postgres + Redis）

根目錄的 `docker-compose.yml` 只跑 DB/Redis（不是 App 本體）。
它的 Postgres 密碼讀自根目錄 `.env` 的 `DATABASE_PASSWORD`，所以**先做第 3 步建 `.env`**，再回來執行：

```bash
docker compose up -d        # Postgres 對外 25000、Redis 6379
docker compose ps           # 確認兩個 container 都 Up
```

---

## 3. 後端環境變數（根目錄 `.env`）

先產生兩把全新祕密（**不要用任何舊值**）：

```bash
python3 -c "from secrets import token_urlsafe; print('SECRET_KEY=', token_urlsafe(50)); print('ADMIN_ACCESS_KEY=', token_urlsafe(24))"
```

在**專案根目錄**建立 `.env`：

```dotenv
# === 必填 ===
SECRET_KEY='上面產生的 SECRET_KEY'
DATABASE_PASSWORD='自訂一組 DB 密碼'
ADMIN_ACCESS_KEY='上面產生的 ADMIN_ACCESS_KEY'

DEBUG=False
ALLOWED_HOSTS=<HOST_IP>

# 靶機綁主機內網 IP（使用者才連得到）
INSTANCE_BIND_HOST=<HOST_IP>
INSTANCE_PUBLIC_HOST=<HOST_IP>

# 內網純 HTTP：關掉 https 強制與 Secure cookie，否則 admin 登不進去
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
CSRF_TRUSTED_ORIGINS=http://<HOST_IP>
CORS_ALLOWED_ORIGINS=http://<HOST_IP>

# === 選用 ===
# SENTRY_DSN=...                 # 要開錯誤監控才填
# ACTIVEINSTANCE_LIMIT=30        # 依主機資源調整靶機同時數量上限
# INSTANCE_EXPIRY_MINUTES=30
```

> `chmod 600 .env` 保護它。`DATABASE_HOST`/`DATABASE_PORT` 不填即用預設
> `127.0.0.1:25000`，正好對上第 2 步的 docker-compose。

---

## 4. 後端：安裝、遷移、建管理員、收集靜態檔

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
pip install gunicorn                 # 正式環境用 gunicorn 跑

python manage.py migrate
python manage.py createsuperuser     # 建立管理員（F5 用）
python manage.py collectstatic --noinput
```

---

## 5. 啟動後端服務（gunicorn + Celery worker + beat）

三個都要常駐。手動測試可開三個終端：

```bash
# 終端 A：API（從 backend/，venv 已啟用）
gunicorn myproject.wsgi:application --bind 127.0.0.1:8000 --workers 3

# 終端 B：Celery worker（負責建立/銷毀靶機，需 docker 權限）
celery -A myproject worker -l info

# 終端 C：Celery beat（過期清理 + 孤兒對帳排程）
celery -A myproject beat -l info
```

正式環境請改用 **systemd** 常駐（範例見文末附錄）。

---

## 6. 前端：環境變數 + build

在 `frontend/` 建立 `.env`：

```dotenv
VITE_API_BASE_URL=http://<HOST_IP>/api
VITE_ADMIN_ACCESS_KEY='與後端 ADMIN_ACCESS_KEY 完全相同'
# VITE_SENTRY_DSN=...            # 要開前端監控才填
```

build：

```bash
cd ../frontend
npm ci
npm run build                    # 產出 frontend/dist
```

---

## 7. nginx（服務前端 + 反代後端）

以 `deploy/nginx.conf.example` 為範本，填入：
- `server_name` → `<HOST_IP>`
- `root` → `<專案路徑>/frontend/dist` 的絕對路徑

```bash
sudo cp deploy/nginx.conf.example /etc/nginx/conf.d/jack.conf
sudo vim /etc/nginx/conf.d/jack.conf     # 填上面兩個值
sudo nginx -t && sudo systemctl reload nginx
```

此時瀏覽器開 `http://<HOST_IP>/` 應該看得到登入頁，`/admin/` 反代得到 Django admin。

---

## 8. 靶機對外連線封鎖（egress 防火牆）

```bash
# 先用 docker network inspect 確認容器網段是否落在 172.16.0.0/12（預設多是）
sudo bash deploy/egress-firewall.sh.example
# 持久化（重開機保留），擇一：
#   - apt install iptables-persistent 後 netfilter-persistent save
#   - 或包成 systemd unit 開機執行
```

套用後，靶機容器無法主動連外（擋跳板/挖礦/打內網），但使用者仍連得進靶機。

---

## 9. 建立實驗（Lab）

1. 用 `?admin_key=<ADMIN_ACCESS_KEY>` 第一次進 `http://<HOST_IP>/admin/`（或用 superuser 登入）。
2. 新增 `Lab`：
   - **固定答案題**：填 `solution`（使用者要交回的 flag 字串）、`docker_image`，
     `compose_template` 留空即用預設 web+mysql 模板。
   - **自帶 compose 的題**：把整段 docker-compose YAML 貼進 `compose_template`，
     並設 `web_service`/`web_port`（平台會強制覆寫資源/安全限制、只開受控埠）。
3. 先 `docker pull` 題目鏡像，避免第一次啟動等太久。

---

## 10. 驗收

```bash
curl http://<HOST_IP>/api/health/      # 期望 {"status":"ok","database":true}
```

- 註冊 → 登入 → 進 Lab → 啟動靶機（狀態 creating→running）→ 點「進入靶機」應開到
  `http://<HOST_IP>:<port>` → 提交正確 flag → 填防禦表單 → 看他人解法。
- 30 分鐘後靶機自動銷毀；Celery beat 每分鐘清過期、每 5 分鐘對帳孤兒。

---

## 附錄：systemd 常駐範例

`/etc/systemd/system/jack-gunicorn.service`：

```ini
[Unit]
Description=Jack gunicorn
After=network.target

[Service]
User=<跑服務的使用者>
WorkingDirectory=<專案路徑>/backend
ExecStart=<專案路徑>/backend/venv/bin/gunicorn myproject.wsgi:application --bind 127.0.0.1:8000 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

`jack-celery.service` / `jack-celery-beat.service` 同理，`ExecStart` 換成：
`.../venv/bin/celery -A myproject worker -l info`、`... beat -l info`，
且 `User` 必須在 `docker` 群組。

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now jack-gunicorn jack-celery jack-celery-beat
```
