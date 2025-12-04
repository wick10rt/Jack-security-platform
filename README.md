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
```

在 `frontend/` 創建 `.env` 填入下面的內容:

```dotenv
# frontend/.env

# 要跟 backend/core/middleware.py → ALLOWED_QUERY_VALUE 的一樣
# VITE_ADMIN_ACCESS_KEY 預設是 @1121717dogdog1101737fatfat
VITE_ADMIN_ACCESS_KEY='your-admin-access-key'
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

| Week         | Video Link                                  |
| :----------- | :------------------------------------------ |
| **Week 1**   | [Watch Video](https://youtu.be/6UBfEKyguUY) |
| **Week 2**   | [Watch Video](https://youtu.be/D8hVQlWvPsI) |
| **Week 3**   | [Watch Video](https://youtu.be/BnvHT9BLQB0) |
| **Week 4**   | [Watch Video](https://youtu.be/1fMSB6qCsnA) |
| **Week 5**   | [Watch Video](https://youtu.be/OzDE_BdZOjo) |
| **Week 6-7** | [Watch Video](https://youtu.be/ZFG1guBRovA) |
| **Week 8-9** | [Watch Video](https://youtu.be/kf87MPGtzp0) |
| **Week 10**  | [Watch Video](https://youtu.be/-eIVovvtz4o) |
| **Week 11**  | [Watch Video](https://youtu.be/MmZwC7nAL7E) |
