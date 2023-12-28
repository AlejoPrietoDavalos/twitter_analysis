#!/bin/bash
# How to use:
# ./load_db.sh yyyy mm dd HH MM SS
mongorestore --drop --db scrape_tw data/backup_db/date_$1_$2_$3_$4_$5_$6/scrape_tw