# comparing-cloud-storage

To get started on a node:
  1) brew install coreutils
  2) export PATH="/usr/local/opt/coreutils/libexec/gnubin:$PATH"
  3) pip install -r requirements.txt
  4) export NODEID, EECSISEUSER
  3) create new crontab, tell it to run run_test.sh

File contents:

  1) requirements.txt - Python libraries required to run the main test script.
     Run like 'pip install -r requirements.txt'

  2) mkaccount.py - Generate jQuery commands to automate account creation.

  3) test.py - the main test script to generate measurements.
     Usage: python test.py service num_trials (--filesize fsize)
     where service is one of {dropbox,box}

     If no file size is specified the script will choose randomly one of {10,25,100MB}

  4) log.csv - local measurement log generated and updated by test.py script


