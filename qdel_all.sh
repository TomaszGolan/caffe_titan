#!/bin/bash

for job in $(qstat | grep goran | awk '{print $1}')
do
    qdel $job
done
