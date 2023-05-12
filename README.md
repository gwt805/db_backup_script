- 首次运行会提示让用阿里云盘APP扫码登陆

- 需要先配置 `config.py` 文件

- 然后配置 `main.py` 中的 `dbdict`, key 是文件名，value 中的 `db` 是 要备份的数据库的名字

- 然后 安装环境, pip install -r requirements.txt

- 最后运行 sh db_backup_auto_start.sh 或者  nohup python main.py &