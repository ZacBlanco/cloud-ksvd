#!/bin/bash

tD=(3 5 10)
t0=(3 5)
tc=(3 5)
tp=(3 5)

for i in "${tD[@]}"
do
	for j in "${t0[@]}"
	do
		for k in "${tc[@]}"
		do
			for l in "${tp[@]}"
			do
				echo "tD: $i | t0: $j | tc: $k | tp: $l"
				mpiexec -np 4 python CloudkSVD.py $i $j $k $l
			done
		done
	done
done