#!/usr/bin/env python

import os
import sys
from datetime import datetime
import matplotlib
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

b = []
a = []
l = []

for logfile in ls(path):
    batch_size = int(logfile[len(prefix):].split('_')[0])

    with open(os.path.join(path, logfile), 'r') as f:
        log = f.read().split('\n')

    try:

        acc = float(get_acc(log))
        lrate = get("base_lr", log)
        lrate = float(lrate.split()[1])

        b.append(batch_size)
        a.append(acc)
        l.append(lrate)
    except:
        pass

fig, ax = plt.subplots(2, 5)
fig.set_size_inches((5, 2) * fig.get_size_inches())

for i in xrange(10, 110, 10):
    x = []
    y = []

    for j, size in enumerate(b):
        if size == i:
            x.append(l[j] * 1000)
            y.append(a[j])

    data = zip(x, y)
    data.sort()

    posx = int(i > 50)
    posy = i / 10 - 5 * posx - 1
    ax[posx, posy].set_title("batch size = %d" % i)
    ax[posx, posy].set_xlabel("learning rate [$10^{-3}$]")
    ax[posx, posy].set_ylabel("accuracy")
    ax[posx, posy].set_ylim([0.8, 1.0])

    try:
        x, y = zip(*data)
        ax[posx, posy].plot(x, y)
    except:
        pass

plt.savefig('bslr.png')
