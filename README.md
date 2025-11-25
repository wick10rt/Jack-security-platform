# Jack Security Platform

**設計簡報**:

<https://www.canva.com/design/DAG19OvwFdQ/OMonLDO6pZEA0hrzcX1bcw/view?utm_content=DAG19OvwFdQ&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h4679177af0>

---

## 系統需求

- **Python**
- **Node.js**
- **Docker & Docker Compose**

---

### 1. 取得專案

```bash
git clone https://github.com/wick10rt/Jack-security-platform.git
cd Jack-security-platform
```

### 2. 配置環境變數(.env)

```dotenv
# .env

# python -> from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())
SECRET_KEY='your-key'
DATABASE_PASSWORD='your-password'
```

### 3. 啟動後端與資料庫

a. **啟動 PostgreSQL 資料庫**:

```bash
docker-compose up -d
```

b. **啟用虛擬環境**:

```bash
cd backend
python -m venv venv
source venv/bin/activate
#or
.\venv\Scripts\activate
```

c. **安裝後端依賴**:

```bash
pip install -r requirements.txt
```

d. **執行資料庫遷移**:

```bash
python manage.py migrate
```

e. **建立管理員帳號**:

```bash
python manage.py createsuperuser
```

f. **啟動 Django 開發伺服器**:

```bash
python manage.py runserver
```

### 4. 啟動前端

a. **進入前端專案目錄並安裝依賴**:

```bash
cd frontend
npm install
```

b. **檢查程式碼**:

```bash
npm run lint
```

c. **啟動 Vue.js 開發伺服器**:

```bash
npm run dev
```

### 5. 進入系統

- **前端使用者介面**: `http://localhost:5173/`
- **後端 API**: `http://127.0.0.1:8000/`

---

### 開發成果影片連結

**第 1 周**:

<https://youtu.be/6UBfEKyguUY>

**第 2 周**:

<https://youtu.be/D8hVQlWvPsI>

**第 3 周**:

<https://youtu.be/BnvHT9BLQB0>

**第 4 周**:

<https://youtu.be/1fMSB6qCsnA>

**第 5 周:**

<https://youtu.be/OzDE_BdZOjo>

**第 6,7 周:**

<https://youtu.be/ZFG1guBRovA>

**第 8,9 周:**

<https://youtu.be/kf87MPGtzp0>

**第 10 周:**

<https://youtu.be/-eIVovvtz4o>
