# 張胖胖資安攻防平台

## 開發人員-老張

10/7 創建環境,引入 django 框架,初始化 django 跟 postgresql <br>
10/8 定義資料庫結構 ,註冊到 D4 ,開發 F5-管理員後台<br>
10/10 B2 API: 開發 /labs/, /labs/{lab id}/的 api<br>
10/11 B1 API: 開發/auth/register/, /auth/login/<br>
10/12 B3 API: 開發 /progress/ API





# Jack Security Platform

## 系統需求

- Python ≥ 3.13
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
# ports:
#   - "25000:5432"  >> "5432:5432"
nvim docker-compose.yml

docker-compose up -d

python manage.py migrate

python manage.py createsuperuser
```
