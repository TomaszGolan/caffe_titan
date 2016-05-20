#!/bin/bash

for i in $(seq 10 10 1000)
do
  ./mlmpr_caffe_depend.py new --config minosmatch_nukecczdefs_127x50_x_unshifted_me1Bmc_batch_size_test.ini --name batch_size_$i -b $i -e 1 -l 1500000 -t 150000
done
