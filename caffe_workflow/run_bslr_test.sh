#!/bin/bash

for i in $(seq 10 10 100)
do
  for j in $(seq 0.0005 0.0005 0.005)
  do
    ./mlmpr_caffe_depend.py new --config minosmatch_nukecczdefs_127x50_x_unshifted_me1Bmc_bs_lr_test.ini --name 'bs_'$i'_lr_'$j -b $i -e 10 -l 1500000 -t 150000 -r $j
  done
done
