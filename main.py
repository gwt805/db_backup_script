import os
import time
import config
import random
import requests
import datetime
import threading
from aligo import Aligo
from loguru import logger
from wxpusher import WxPusher
import urllib.parse, hashlib, base64, time, hmac
from dingtalkchatbot.chatbot import DingtalkChatbot

def random_color():
    color_code = "0123456789ABCDEF"
    color_str = ""
    for it in range(6):
        color_str += random.choice(color_code)
    return color_str

def size(num):
    return num / 1024 / 1024 / 1024

def send_msg(data):
    contents = f"数据库备份文件 <font color={random_color()}>『{data['filename']}』</font> 成功上传到阿里云盘 <font color={random_color()}>/ESS_Backup/</font> 路径下!<br><br><a href='{data['share_url']}?access_key={data['share_pwd']}' target='_blank'>点我下载/查看文件</a><br><br>若还是需要密码，则密码为地址栏中 access_key等号后面的值!<br><br><label>阿里云盘剩余空间: <font color={random_color()}>{data['free_size']}</font> G</label>"
    markdown_url = f"[点我下载/查看文件]({data['share_url']}?access_key={data['share_pwd']})"
    markdown_contents = contents.replace("<br>","\n\r").replace("<label>","").replace("</label>","").replace(f"<a href='{data['share_url']}?access_key={data['share_pwd']}' target='_blank'>点我下载/查看文件</a>", markdown_url)
    
    def send_wxpusher():
        rep = WxPusher.send_message(content=contents, uids=config.WXPUSHER_UIDS, token=config.WXPUSHER_TOKEN)
        logger.info(f"wxpusher 消息状态: {rep}")
    def send_wecom():
        res = requests.post(
            f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={config.WECOM_ROBOT_WEBHOOK_KEY}", 
            json={
                "msgtype": "markdown",
                "markdown": {
                    "content": markdown_contents
                }
            }
        )
        logger.info(f"企微机器人消息状态: {res.json()}")
    def send_dingtalk():
        timestamp = str(round(time.time() * 1000))
        secret = config.DING_ROBOT_SECRET  # 替换成你的签
        secret_enc = secret.encode("utf-8")
        string_to_sign = "{}\n{}".format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(
            secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

        webhook = f"https://oapi.dingtalk.com/robot/send?access_token={config.DING_ROBOT_WEBHOOK_TOKEN}&timestamp={timestamp}&sign={sign}"
        msgs = DingtalkChatbot(webhook)
        states = msgs.send_markdown(title="cvat-robot", text=markdown_contents, is_at_all=False)
        logger.info(f"钉钉机器人消息状态: {states}")

    if config.WXPUSHER_UIDS == "" or config.WXPUSHER_TOKEN == "":
        logger.info("wxpuser 消息通知没有配置喔!")
    else:
        send_wxpusher_task = threading.Thread(target=send_wxpusher)
        send_wxpusher_task.start()
    if config.WECOM_ROBOT_WEBHOOK_KEY == "":
        logger.info("企业微信机器人消息通知没有配置喔!")
    else:
        send_wecom_task = threading.Thread(target=send_wecom)
        send_wecom_task.start()
    if config.DING_ROBOT_WEBHOOK_TOKEN == "" or config.DING_ROBOT_SECRET == "":
        logger.info("钉钉机器人消息通知没有配置喔!")
    else:
        send_dingtalk_task = threading.Thread(target=send_dingtalk)
        send_dingtalk_task.start()
    

def upload_sql_file(base_path):
    info = ali.get_personal_info()

    total_size = size(info.personal_space_info.total_size)
    used_size = size(info.personal_space_info.used_size)
    free_size = total_size - used_size
    logger.info(f"总容量: {total_size}G, 已用容量: {used_size}G")

    ess_backup_floder_file_list = [item.name for item in ali.get_file_list(parent_file_id=config.ALI_PARENT_FILE_ID)]
    
    file_list = [file  for file in os.listdir(base_path) if file.endswith(".sql")]
    for item in file_list:
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
        
        os.remove(base_path + f"/{item}")
        
        data = {
            "free_size": free_size,
            "filename": item,
            "share_url": share_url,
            "share_pwd": share_pwd                
        }

        send_msg(data)

def export_sql(now):
    sql_file_save_path = config.SQL_BACKUP_LOCAL_PATH
    
    db_export_config ={
        "myess_back": {"server": "", "user": "", "password": "", "port": 3306, "db": "" },
        "dbshow_back":{"server": "", "user": "", "password": "", "port": 3306, "db": "" }
    }
    
    for k,v in db_export_config.items():
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
    logger.info("开始备份......")
    while True:
        datetime_now = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        time_now = datetime_now.split("T")[-1].replace('-',":")
        
        if ":" not in config.DAY_UPLOAD_TIME or config.DAY_UPLOAD_TIME == "":
            raise ValueError("请配置正确的备份时间点!")

        if time_now == config.DAY_UPLOAD_TIME:
            export_sql_task = threading.Thread(target=export_sql, args=(datetime_now,))
            export_sql_task.start()
        time.sleep(1)
        

if __name__ == "__main__":
    ali = Aligo()
    main()