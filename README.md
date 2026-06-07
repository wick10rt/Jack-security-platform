# Jack Security Platform

**設計簡報**: <https://www.canva.com/design/DAG19OvwFdQ/OMonLDO6pZEA0hrzcX1bcw/view?utm_content=DAG19OvwFdQ&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h4679177af0>

---

## System Requirements

- **Python**
- **Node.js**
- **Docker & Docker Compose**

---

## Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/wick10rt/Jack-security-platform.git
cd Jack-security-platform
```

### 2. Configure Environment Variables

在專案根目錄創建 `.env` 填入下面的內容:

```dotenv
# .env

# 用 Python 建立django密鑰:
# from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())
SECRET_KEY='your-key'
DATABASE_PASSWORD='your-password'

# 本機開發設 True；正式環境務必設 False
DEBUG=True
# DEBUG=False 時必填，以逗號分隔，例如: example.com,www.example.com
ALLOWED_HOSTS=
# 隱藏的 /admin/ 繞過金鑰，請自行產生高強度隨機值；留空則停用此繞過
ADMIN_ACCESS_KEY='your-admin-access-key'

# 靶機網路（內網部署）：開發維持 127.0.0.1；內網部署時兩者都設成主機內網 IP
INSTANCE_BIND_HOST=127.0.0.1
INSTANCE_PUBLIC_HOST=127.0.0.1
# 內網無 HTTPS 但 DEBUG=False 時，設 False 以免被強制轉址到 https
# SECURE_SSL_REDIRECT=False
```

在 `frontend/` 創建 `.env` 填入下面的內容:

```dotenv
# frontend/.env

VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

### 3. Backend Setup

**a. 啟動資料庫**

```bash
docker-compose up -d
```

**b. 虛擬環境**

```bash
cd backend

# Linux / macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
```

**c. 安裝依賴**

```bash
pip install -r requirements.txt
```

**d. 資料庫遷移**

```bash
python manage.py migrate

python manage.py createsuperuser
```

**e. 啟動後端**

```bash
python manage.py runserver
```

**f. 啟動 Celery**

```bash
# 如果系統支援多進程
celery -A myproject worker -l info

# 單進程
celery -A myproject worker -l info -P solo

celery -A myproject beat -l info
```

### 4. Frontend Setup

**a. 安裝依賴**

```bash
cd frontend
npm install
```

**b. 啟動前端**

```bash
npm run dev
```

---

## Access

| Service         | URL                      |
| :-------------- | :----------------------- |
| **Frontend UI** | <http://localhost:5173/> |
| **Backend API** | <http://127.0.0.1:8000/> |

---

## Videos

| Video            | Video Link                     |
| :--------------- | :----------------------------- |
| **Only Backend** | <https://youtu.be/-wbhllZCkx4> |
| **All In One**   | <https://youtu.be/L85lbrdntMc> |
