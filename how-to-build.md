
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
# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# .\venv\Scripts\activate  # Windows PowerShell

# 安裝依賴套件
pip install -r requirements.txt
docker-compose up -d
python manage.py migrate
