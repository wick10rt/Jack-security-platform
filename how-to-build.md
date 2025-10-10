# Jack Security Platform

## 系統需求

- Python ≥ 3.11
- Docker & Docker Compose
- Git

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
docker-compose up -d

python manage.py migrate

python manage.py createsuperuser
```
