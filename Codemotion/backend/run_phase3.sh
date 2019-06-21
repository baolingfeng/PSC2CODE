#!/bin/bash
for i in $(eval echo {$1..$2}); do
	echo
	echo processing ${i}
	# time python phase3.py $i 2>../public/other/video${i}b.json >>temp/tempB
	time python phase3.py $i 2>../public/other/${i}.json >>temp/tempB
	echo -- $i >> temp/temp
done
