#!/bin/bash

#-------------------------------------------------------------------------------
# # Information for Vera:
# - This is the only script that runs Launchd in the specified time interval.
# - In turn, this script executes autoupdate.py, in order to collect the Trends.
# - 
#-------------------------------------------------------------------------------

#--> TODO: cd /Users/v/Desktop/dev_stuff/twit
source env/bin/activate
python3 autoupdate.py >> autoupdate_log.txt