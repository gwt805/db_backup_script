import os
import random
import datetime
import threading
import config
from aligo import Aligo
from loguru import logger
from wxpusher import WxPusher

def random_color():
    color_code = "0123456789ABCDEF"
    color_str = ""
    for it in range(6):
        color_str += random.choice(color_code)
    return color_str

def size(num):
    return num / 1024 / 1024 / 1024

def send_msg(data):
    logger.info(data['free_size'])
    contents = f"ESS 数据库备份文件 <font color={random_color()}>『{data['filename']}』</font> 成功上传到阿里云盘 <font color={random_color()}>/ESS_Backup/</font> 路径下!<br><br><a href='{data['share_url']}?access_key={data['share_pwd']}' target='_blank'>点我下载/查看文件</a><br><br>若还是需要密码，则密码为地址栏中 access_key等号后面的值!<br><br><label>阿里云盘剩余空间: <font color={random_color()}>{data['free_size']}</font> G</label>"
    rep = WxPusher.send_message(content=contents, uids=config.WXPUSHER_UIDS, token=config.WXPUSHER_TOKEN)
    logger.info(f"wxpusher 消息状态: {rep}")

def upload_sql_file(base_path):
    ali = Aligo()

    info = ali.get_personal_info()

    total_size = size(info.personal_space_info.total_size)
    used_size = size(info.personal_space_info.used_size)
    free_size = total_size - used_size
    logger.info(f"总容量: {total_size}G, 已用容量: {used_size}G")

    ess_backup_floder_file_list = [item.name for item in ali.get_file_list(parent_file_id=config.ALI_PARENT_FILE_ID)]
    
    file_list = [file  for file in os.listdir(base_path) if file.endswith(".sql")]
    for item in file_list:
        if item in ess_backup_floder_file_list:
            os.remove(base_path + f"/{item}")
        else:
            res = ali.upload_file(f"{base_path}/{item}", parent_file_id=config.ALI_PARENT_FILE_ID, name=item)
            logger.info(f"『{item}』 上传状态: {res}")
            try:
                shared = ali.share_file(file_id=res.file_id, share_name=res.file_name, share_pwd=config.SQL_FILE_SHARED_PWD)
                share_pwd = shared.share_pwd
                share_url = shared.share_url
                logger.info(f"{item} 分享状态: 地址: {share_pwd} , 密码: {share_url}")
            except:
                shared = ali.share_file(file_id=res.file_id, share_name=res.name, share_pwd=config.SQL_FILE_SHARED_PWD)
                share_pwd = shared.share_pwd
                share_url = shared.share_url
                logger.info(f"{item} 分享状态: 地址: {share_pwd} , 密码: {share_url}")
            
            data = {
                "free_size": free_size,
                "filename": item,
                "share_url": share_url,
                "share_pwd": share_pwd                
            }

            send_msg_task = threading.Thread(target=send_msg, args=(data,))
            send_msg_task.start()

def export_sql():
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    
    sql_file_save_path = config.SQL_BACKUP_LOCAL_PATH
    
    dbdict ={
        "myess_back": {"server": config.DB_HOST, "user": config.DB_USER, "password": config.DB_PWD, "port": 3306, "db": "myess" },
        "dbshow_back":{"server": config.DB_HOST, "user": config.DB_USER, "password": config.DB_PWD, "port": 3306, "db": "dbshow" }
    }
    
    for k,v in dbdict.items():
        sqlfromat = "mysqldump --column-statistics=0 -h%s -u%s -p%s -P%s %s > %s"
        sql = (sqlfromat % ( v['server'], v['user'], v['password'], v['port'], v['db'], f"{sql_file_save_path}/{now}_{k}.sql" ))
        logger.info(f"执行的导出数据库的sql: {sql}")
        result = os.system(sql)
        logger.info(f"导出结果: {result}")
    try:
        upload_sql_file(sql_file_save_path)
    except:
        logger.error("您的机器断网了!")

def main():
    export_sql_task = threading.Thread(target=export_sql)
    export_sql_task.start()

if __name__ == '__main__':
    main()