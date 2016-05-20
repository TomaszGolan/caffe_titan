#!/usr/bin/env python

import os
import sys
from datetime import datetime
import matplotlib.pyplot as plt


def str2time(str):
    return datetime.strptime(str, '%M:%S.%f')


def ls(path):
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)):
            yield f


def get(str, log):
    for l in log:
        if str in l:
            return l.strip()


def get_acc(log):
    temp = []
    for l in log:
        if 'accuracy = ' in l:
            temp.extend(l.split())
    return temp[-1]

path = sys.argv[1]
prefix = sys.argv[2]

time_prefix = "Elapsed (wall clock) time (h:mm:ss or m:ss):"

b = []
t = []
a = []

for logfile in ls(path):
    batch_size = int(logfile[len(prefix):].split('_')[0])

    with open(os.path.join(path, logfile), 'r') as f:
        log = f.read().split('\n')

    time = str2time((get(time_prefix, log)[len(time_prefix):].strip()))
    time = 3600 * time.hour + 60 * time.minute + time.second

    acc = float(get_acc(log))

    b.append(batch_size)
    t.append(time)
    a.append(acc)

data = zip(b, t, a)
data.sort()

b, t, a = zip(*data)

plt.figure(1)

plt.xlabel('batch size')
plt.ylabel('time [s]')

plt.plot(b, t)
plt.savefig('batch_size_vs_time.png')

plt.figure(2)

plt.ylabel('accuracy')

plt.plot(b, a)
plt.savefig('batch_size_vs_acc.png')
