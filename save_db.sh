#!/bin/bash
mongodump --db scrape_tw --out data/backup_db/date_$(date +"%Y_%m_%d_%H_%M_%S")