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
docker compose up -d        # Postgres 127.0.0.1:25000、Redis 127.0.0.1:6379（僅本機可連）
docker compose ps           # 確認兩個 container 都 Up
```

> Postgres/Redis 都刻意只綁 `127.0.0.1`：後端/Celery 走 localhost 連得到，但內網
> 其他人與「被攻陷的靶機」都碰不到，這是擋靶機跳板打基礎設施的關鍵。

---

## 3. 後端環境變數（根目錄 `.env`）

先產生兩把全新祕密（**不要用任何舊值**）：

```bash
python3 -c "from secrets import token_urlsafe; print('SECRET_KEY=', token_urlsafe(50)); print('ADMIN_ACCESS_KEY=', token_urlsafe(24))"
```

在**專案根目錄**建立 `.env`（可 `cp .env.example .env` 後改值）：

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
pip install -r ../requirements.txt   # 已含 gunicorn

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
# VITE_SENTRY_DSN=...            # 要開前端監控才填
# VITE_ADMIN_URL=...             # 管理員登入後跳轉的 /admin/ 網址；
#                                # 不填會自動由 VITE_API_BASE_URL 推導（http://<HOST_IP>/admin/）
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

## 8. 靶機對外連線封鎖（egress 防火牆）— **必做**

靶機是故意做漏的，要假設攻擊者一定拿得到靶機內的 shell。這步是擋他「往外打別人」
的主防線，**不是選用**。

```bash
# 先用 docker network inspect 確認容器網段是否落在 172.16.0.0/12（預設多是）
sudo bash deploy/egress-firewall.sh.example
# 持久化（重開機保留），擇一：
#   - apt install iptables-persistent 後 netfilter-persistent save
#   - 或包成 systemd unit 開機執行
```

套用後：靶機容器無法主動連外（FORWARD：擋挖礦/打內網/連別人靶機的公開埠），
也無法直連 host 自身服務（INPUT：擋打 SSH 等 host 上 0.0.0.0 服務）。使用者仍連得進靶機。

## 8.1 容器權限硬化（P1，已內建 + 一個選用主機設定）

- **cap_drop（已自動）**：平台對每個靶機容器強制丟掉 `NET_RAW`（擋同網段 ARP 欺騙/
  raw 封包）、`SYS_ADMIN`/`DAC_READ_SEARCH`（擋逃逸）等危險 capabilities，清單見後端
  `INSTANCE_CAP_DROP`。預設清單不影響 apache(:80)/mysql 正常啟動。**換上你自己的靶機
  鏡像後，請實測它能正常開機**；若你的鏡像需要被擋掉的 cap，調整 `INSTANCE_CAP_DROP`/
  `INSTANCE_CAP_ADD`（或設 `INSTANCE_CAP_DROP=ALL` 後用 `INSTANCE_CAP_ADD` 精準加回）。
- **userns-remap（選用、強烈建議）**：讓容器內的 root 對應到 host 上的非特權 UID，
  萬一發生容器逃逸也不是 host root。編輯 `/etc/docker/daemon.json`：

  ```json
  { "userns-remap": "default" }
  ```

  然後 `sudo systemctl restart docker`。注意：開啟後鏡像會以重映射 UID 重新展開、
  首次較慢；與 `--privileged`、bind-mount 主機路徑不相容（本平台本來就把這些剝掉，故
  相容）。開啟前先在測試機驗證你的靶機鏡像仍能啟動。

---

## 9. 建立實驗（Lab）

1. 用 `?admin_key=<ADMIN_ACCESS_KEY>` 第一次進 `http://<HOST_IP>/admin/`（或用 superuser 登入）。
2. 新增 `Lab`：
   - **固定答案題**：勾選 `requires_answer`（預設），填 `solution`（使用者要交回的 flag
     字串）、`docker_image`，`compose_template` 留空即用預設 web+mysql 模板。
   - **純跑靶機題（沙盒）**：取消勾選 `requires_answer`，`solution` 可留空。使用者只會看到
     啟動/進入靶機，沒有提交答案、防禦表單、社群解法，也不計入完成進度。
   - **自帶 compose 的題**：把整段 docker-compose YAML 貼進 `compose_template`，
     並設 `web_service`/`web_port`（平台會強制覆寫資源/安全限制、只開受控埠）。
3. 先 `docker pull` 題目鏡像，避免第一次啟動等太久。

每個 Lab 還有幾個選填的彈性欄位（留空＝用全域預設，不影響既有題）：

- **`web_env`**：一行一個 `KEY=VALUE`，合進 web 服務的環境變數。BYO 鏡像若用不同的
  DB env 名稱（如 `MYSQL_HOST`、`DATABASE_URL`），在這裡覆寫即可，不必手寫整段 compose。
- **`expiry_minutes`**：此題靶機存活分鐘數（複雜多步驟題可調長、速解題可調短）。
- **`max_extensions`**：此題可延長次數上限。

> 答案比對是**大小寫不敏感**＋自動去頭尾空白，學習者不會因大小寫打錯而卡關；
> 出題者仍應把 flag 格式寫清楚。

---

## 10. 驗收

```bash
curl http://<HOST_IP>/api/health/      # 期望 {"status":"ok","database":true}
```

- 註冊 → 登入 → 進 Lab → 啟動靶機（狀態 creating→running）→ 點「進入靶機」應開到
  `http://<HOST_IP>:<port>` → 提交正確 flag → 填防禦表單 → 看他人解法。
- 30 分鐘後靶機自動銷毀；Celery beat 每分鐘清過期、每 5 分鐘對帳孤兒。

---

## 11. 容量規劃與靶機存取控制（取捨）

### 同時靶機數量怎麼抓

`ACTIVEINSTANCE_LIMIT` 是「全域同時靶機數」的硬上限（預設 30）。但真正的天花板是**主機
RAM**，不是這個數字。每個靶機的記憶體上限由設定決定（`INSTANCE_WEB_MEM` +
`INSTANCE_DB_MEM`，預設各 `512m`）：

- 需要 DB 的題：web 512m + mysql 512m ≈ **1GB/靶機**
- 不需 DB / 純跑靶機題（`needs_db` 取消）：只有 web ≈ **0.5GB/靶機**

抓上限的公式：

```
ACTIVEINSTANCE_LIMIT ≈ (主機RAM_GB − 系統與服務保留 4~8GB) / 每靶機GB
```

例：32GB 主機、全是 needs_db 題 → `(32 − 6) / 1 ≈ 26`，設 25~28 較穩（預設 30 是抓 32GB
機器的樂觀值）。要撐 40 人同時，三條路：加 RAM、多用「不需 DB 的題」、或調低
`INSTANCE_DB_MEM`（換 mariadb 或 mysql:5.6 較省）。

CPU 採超賣無妨（`INSTANCE_WEB_CPUS`/`INSTANCE_DB_CPUS` 是上限不是保留，靶機多半閒置）；
先撞到的幾乎一定是 RAM。

降 churn 壓力的旋鈕：`INSTANCE_EXPIRY_MINUTES`（預設 30）、`INSTANCE_MAX_EXTENSIONS`
（預設 2）、`INSTANCE_EXTENSION_MINUTES`（預設 30）。課堂越短、人越多，就把到期時間調短、
延長次數壓低，加速回收。

### 靶機存取控制現況（重要取捨）

靶機綁在 `INSTANCE_BIND_HOST:<隨機port>`（部署設 `<HOST_IP>`），使用者瀏覽器**直連、不經
nginx**。這代表：

- 同網段任何人只要猜到 `HOST_IP:port`，就能連進**別人的**靶機 —— 平台只擋「拿 URL」這個
  API（owner 限定），**不擋容器埠本身**。
- 在「校內、信任使用者、靶機是故意做漏的練習機、裡面無真資料」的前提下，此風險可接受，
  是目前刻意的設計取捨。
- 已有防線：第 8 步的 egress 防火牆擋住靶機**主動連外**（跳板/挖礦/打內網）。建議再用主機
  防火牆把靶機 port range（docker 預設高位埠）限制成只接受校園網段來源。

要更強隔離（屬日後強化、非 MVP）：把靶機改只綁 `127.0.0.1`，前面加反向代理
（nginx/Traefik）依「每實例一組 owner token/cookie」動態路由才連得進去 —— 那會把 §7 的
nginx 從「只反代 /api /admin」擴成「也反代每個靶機」。

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
