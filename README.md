# 部署
pip3 install -r requirements-base.txt
python3 cli/cli.py init
修改网站配置文件
cp .env.example config/.env
vim config/.env
python3 cli/cli.py install

## 更新后端代码
python3 cli/cli.py update-backend

## 更新前端代码
python3 cli/cli.py update-frontend