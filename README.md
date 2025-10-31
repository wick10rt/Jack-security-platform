# Jack Security Platform

## 系統需求

- Python ≥ 3.13
- Docker & Docker Compose

---

### 1. 取得專案

```bash
git clone https://github.com/wick10rt/Jack-security-platform.git
```

### 2. 配置環境變數

```bash
#專案根目錄創建.env
cd Jack-security-platform
nvim .env
```

```dotenv
# .env

#使用DJANGO自動產生
#python -> from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())
SECRET_KEY=your-secret-string

#postgresql密碼
DATABASE_PASSWORD=your-password
```

### 3. 啟動服務

a. **啟動資料庫**:

```bash
docker-compose up -d
```

b. **虛擬環境**:

```bash
cd backend
python -m venv venv
source venv/bin/activate
```

c. **安裝依賴**:

```bash
pip install -r requirements.txt

cd frontend
npm install
npm run lint
npm run format
```

d. **資料庫遷移**:

```bash
python manage.py migrate
```

e. **建立管理員帳號**:

```bash
python manage.py createsuperuser
```

f. **啟動伺服器**:

```bash
python manage.py runserver
```

g. **啟動 vue.js**:

```bash
npm run dev
```

透過 http://127.0.0.1:8000/ 進入

---

# 設計圖簡報

https://www.canva.com/design/DAG19OvwFdQ/OMonLDO6pZEA0hrzcX1bcw/view?utlId=h4679177af0#1

---

# 開發成果影片連結

**1 周**:

https://youtu.be/6UBfEKyguUY

**2 周**:

https://youtu.be/D8hVQlWvPsI

**3 周**:

https://youtu.be/D8hVQlWvPsI

**4 周**:

https://youtu.be/1fMSB6qCsnA
