#!/usr/bin/env python

import sys
from datetime import datetime
import matplotlib.pyplot as plt


def str2time(str):
    return datetime.strptime(str, '%H:%M:%S.%f')


def get(str, log):
    for l in log:
        if str in l:
            return l.strip()


with open(sys.argv[1], 'r') as f:
    log = f.read().split('\n')

timestamps = [l.split()[1] for l in log if l.startswith('I')]

delta = [0] * len(timestamps)

for i in range(len(timestamps) - 1):
    d = (str2time(timestamps[i+1]) - str2time(timestamps[i])).total_seconds()
    delta[i+1] = d

steps = []
steps.extend(range(0, len(delta)))

plt.xlabel('log index')
plt.ylabel('$\Delta t$')

plt.text(50, 60, get('display', log), fontsize=15)
plt.text(50, 55, get('test_interval', log), fontsize=15)
plt.text(50, 50, get('batch_size', log), fontsize=15)
plt.text(50, 45, get('snapshot', log), fontsize=15)

plt.plot(steps, delta)
plt.show()
