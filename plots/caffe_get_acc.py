#!/usr/bin/env python

import os
import sys
from datetime import datetime
import matplotlib.pyplot as plt

path = sys.argv[1]
prefix = sys.argv[2]
suffix = ".out"
factor = 15000


def ls(path):
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)):
            if f.startswith(prefix) and f.endswith(suffix):
                yield f


def get_acc(log):
    itr = []
    acc = []
    log = iter(log)
    for l in log:
        if 'Testing net' in l:
            words = iter(l.split())
            for word in words:
                if word == "Iteration":
                    itr.append(float(words.next().replace(',', ''))/factor)
            acc.append(float(log.next().split()[-1]))

    return itr, acc

i = []
a = []

for logfile in ls(path):
    with open(os.path.join(path, logfile), 'r') as f:
        log = f.read().split('\n')

    it, acc = get_acc(log)

    i.extend(it)
    a.extend(acc)


data = zip(i, a)
data.sort()

i, a = zip(*data)

plt.xlabel('epoch')
plt.ylabel('accuracy')
plt.title('epsilon xuv 127x50, fixed lr = 0.0025')

plt.plot(i, a)
plt.savefig('eps_xuv_127x50_flr.png')
