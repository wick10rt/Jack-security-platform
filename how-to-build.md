
# Jack Security Platform

## 系統需求

- Python ≥ 3.11
- Docker & Docker Compose
- Git

---

## 1️⃣ 取得專案

```bash
git clone https://github.com/wick10rt/Jack-security-platform.git
cd Jack-security-platform/backend
python -m venv venv
source venv/bin/activate  
.\venv\Scripts\activate  

pip install -r requirements.txt
docker-compose up -d
python manage.py migrate
