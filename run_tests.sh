#!/bin/bash

# select random service and run test
RAND=$(shuf -i 1-2 -n 1);
echo $RAND;

if [ $RAND -eq "1" ];
    then SVC="dropbox"
else
    SVC='box'
fi

TEST="python /Users/Will/Desktop/MSCS/EECS\ 495\ -\ ISE/test.py $SVC 5"
eval $TEST
