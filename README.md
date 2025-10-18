# Jack Security Platform

## 系統需求

- Python ≥ 3.13
- Docker , Docker Compose

---

## 取得專案

```bash
git clone https://github.com/wick10rt/Jack-security-platform.git
```

## 虛擬環境

```bash
python -m venv venv
source venv/bin/activate
.\venv\Scripts\activate
```

## 安裝依賴

```bash
pip install -r requirements.txt
```

## 初始化

```bash
# ports:
#   - "25000:5432"  >> "5432:5432"
#   POSTGRES_PASSWORD="your_password"
#
nvim docker-compose.yml

docker-compose up -d

#   DATABASE SETTING
#   "PASSWORD": "your_password"
#   "PORT": "5432"
#
nvim backend\myproject\settings.py

python manage.py migrate

python manage.py createsuperuser

python manage.py runserver
```
