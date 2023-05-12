#!/bin/bash
str=$"\n"
cd /home/weitao/db_backup_script
nohup /home/weitao/anaconda3/bin/python main.py > /home/weitao/db_backup_script/db_backup_script.log 2>&1 &
sstr=$(echo -e $str)
echo $sstr