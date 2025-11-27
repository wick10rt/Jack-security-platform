# Jack Security Platform

**Design Presentation**: [View on Canva](https://www.canva.com/design/DAG19OvwFdQ/OMonLDO6pZEA0hrzcX1bcw/view?utm_content=DAG19OvwFdQ&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h4679177af0)

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

Create a `.env` file in the root directory and configure the following:

```dotenv
# .env

# Generate a secret key using Python:
# from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())
SECRET_KEY='your-key'
DATABASE_PASSWORD='your-password'
```

Create a `.env` under `frontend/` and configure the following:

```dotenv
# frontend/.env

# Must match backend/core/middleware.py → ALLOWED_QUERY_VALUE
VITE_ADMIN_ACCESS_KEY='your-admin-access-key'
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

### 3. Backend Setup

**a. Start PostgreSQL Database**

```bash
docker-compose up -d
```

**b. Activate Virtual Environment**

```bash
cd backend

# Linux / macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
```

**c. Install Dependencies**

```bash
pip install -r requirements.txt
```

**d. Database Initialization**

```bash
# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

**e. Start Django Development Server**

```bash
python manage.py runserver
```

**f. Start Celery**

Run the following in separate terminals:

```bash
# Worker (Multi-process)
celery -A myproject worker -l info

# Worker (Windows/Solo mode)
celery -A myproject worker -l info -P solo

# Beat (Scheduler)
celery -A myproject beat -l info
```

### 4. Frontend Setup

**a. Install Dependencies**

```bash
cd frontend
npm install
```

**b. Lint and Start Server**

```bash
# Start Vue.js server
npm run dev
```

---

## Access

| Service         | URL                    |
| :-------------- | :--------------------- |
| **Frontend UI** | http://localhost:5173/ |
| **Backend API** | http://127.0.0.1:8000/ |

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
