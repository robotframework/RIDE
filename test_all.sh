#!/usr/bin/bash

export PYTHONPATH=/home/helio/github/RIDE/utest/:$PYTHONPATH
export PYTHONPATH=/home/helio/github/RIDE/src/:$PYTHONPATH

export PYTHONROOT=$(dirname $(a=$(which python);echo $a))

if [ $# -ge 1 ]
then
      DIR="$1"
else
    DIR="utest"
fi

shift
if [ $# -eq 1 ]
then
    DIR="$1"
fi

cd /home/helio/github/RIDE/
for i in `ls -1R $DIR | grep ":"`
do
        a=`echo $i |sed s/://g`
        for j in `ls -1 $a/test_*py 2>/dev/null`
        do
		# printf "$j\n"
                # bypass file that is passing with invoke test
                if [ "$j" = "$a/test_DEBUG_resourcefactory.py" ]
                then
                        b=`true`
                else 
                        b=`$PYTHONROOT/python $j`
                fi
                if [ $? -eq 1 ]
		then
                        printf "$b\n"
			printf "MUST FIX: $j\n"
			exit
		fi
        done
done
