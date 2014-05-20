#!/usr/bin/env python

import os
import re
import sys
import time
import copy
import thread
import logging
from pcl import common

import matplotlib.pyplot as plt

#fig = plt.figure(figsize=(40, 50), dpi=100)

fig, subplots = plt.subplots(4, 4)
fig.set_size_inches(10, 6)
fig.tight_layout()
fig.subplots_adjust(left=0.125)
subplots = [item for sublist in subplots for item in sublist]


def get_field(d, f):
    if f in d:
        return d[f]
    return 0

def main():
    if len(sys.argv) != 2:
        print sys.argv[0], 'stat.log'
        return

    fname = sys.argv[1]

    lines = file(fname).readlines()
    lines = [common.json_decode(line) for line in lines if line.startswith('{')]
    lines = [line for line in lines if 'ts' in line]
    fields = ['qps', 'cpu', 'du', 'mem-vms',
            'mem-rss','avqqu-sz', 'avgrq-sz', 'util',
            'w/s', 'wkB/s', 'wrqm/s', 'await',
            'r/s', 'rkB/s', 'rrqm/s', 'svctm',
            ]
    #print fields
    #x = [line['ts'] for line in lines]

    for i, f in enumerate(fields):
        p = subplots[i]
        y = [get_field(line, f) for line in lines]
        p.plot(y, 'r', linewidth=0.3)
        p.set_title(f)
        plt.setp(p.get_xticklabels(), visible=False)
    plt.savefig(fname+'.png', dpi=100)

if __name__ == "__main__":
    main()
