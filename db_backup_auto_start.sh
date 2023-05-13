#!/bin/bash

pid=$$
str=$"\n"

cd /home/$USER/db_backup_script

echo $pid > ./db_backup_auto_start_pid.txt

nohup /home/$USER/anaconda3/bin/python main.py > ./db_backup_script.log 2>&1 &

sstr=$(echo -e $str)
echo $sstr
echo $pid
pidc=$!
echo $pidc >> ./db_backup_auto_start_pid.txt