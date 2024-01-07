#!/bin/bash
# How to use:
# ./load_db.sh yyyy mm dd HH MM SS
#directory="data/backup_db/date_$1_$2_$3_$4_$5_$6/scrape_tw"
#mongorestore --drop --nsInclude=scrape_tw.* $directory

directory="data/backup_db/date_$1_$2_$3_$4_$5_$6"
mongorestore --drop --nsFrom='scrape_tw.*' --nsTo='scrape_tw.*' $directory
