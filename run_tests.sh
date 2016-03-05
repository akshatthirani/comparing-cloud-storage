#!/bin/bash

# select random service and run test 3-6 times
RAND=$(shuf -i 1-4 -n 1);
echo $RAND;

if [ $RAND -eq "1" ]
    then SVC="dropbox"
elif [ $RAND -eq "2" ]
    then SVC="box"
elif [ $RAND -eq "3" ]
    then SVC="google"
else
    SVC="amazon"
fi

python '/Users/Will/Desktop/MSCS/EECS 495 - ISE/test.py' $SVC $(shuf -i 3-6 -n 1)
