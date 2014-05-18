#!/usr/bin/env python
#coding: utf-8
#file   : iostat.py
#author : ning
#date   : 2014-05-18 17:37:10


import os
import re
import sys
import time
import commands
from datetime import datetime
import copy
import thread
import logging
from pprint import pprint


PWD = os.path.dirname(os.path.realpath(__file__))
WORKDIR = os.path.join(PWD,  '../')
LOGPATH = os.path.join(WORKDIR, 'log/iostat.log')

sys.path.append(os.path.join(WORKDIR, 'lib/'))

def tonum(n):
    if n.isdigit():
        return int(n)
    return n

def disk_io_counters():
    lines = file("/proc/partitions").readlines()[2:]
    partitions = set([line.split()[-1] for line in lines if not line.strip()[-1].isdigit()])

    def line_to_dict(line):
        major, minor, dev, r_ios, r_merges, r_sec, r_ticks, w_ios, w_merges, w_sec, w_ticks, ios_pgr, tot_ticks, rq_ticks = line.split()
        del line
        d = {k: tonum(v) for k, v in locals().items() }
        d['ts'] = time.time()
        return d

    lines = file("/proc/diskstats").readlines()
    stats = [line_to_dict(line) for line in lines]
    stats = {stat['dev']: stat for stat in stats if stat['dev'] in partitions}
    return stats


#:rrqm/s   : The number of read requests merged per second that were queued to the device.    #( rd_merges[1] - rd_merges[0] )
#:wrqm/s   :
#:r/s      : The number of read requests that were issued to the device per second.           #(rd_ios[1] - rd_ios[0])
#:w/s      :
#:rkB/s    : The number of kilobytes read from the device per second.                         #( rd_sectors[1] - rd_sectors[0] ) * sector_size
#:wkB/s    :

#:avgrq-sz : (平均请求大小)The average size **in sectors** of the requests that were issued to the device.
            #( ( rd_sectors[1] - rd_sectors[0] ) + ( wr_sectors[1] - wr_sectors[0] ) ) / (rd_ios[1] - rd_ios[0]) + (wr_ios[1] - wr_ios[0])
#:avgqu-sz : The average queue length of the requests that were issued to the device.
            #这不是ios_pgr, 而是: (rq_ticks[1] - rq_ticks[0]) / 1000 这是什么原理.

#:await    : (等待时间)The average time (in milliseconds) for I/O requests issued to the  device  to  be  served
            #( ( rd_ticks[1] - rd_ticks[0] ) + ( wr_ticks[1] - wr_ticks[0] ) ) / (rd_ios[1] - rd_ios[0]) + (wr_ios[1] - wr_ios[0])
#:svctm    : (服务时间)The average service time (in milliseconds) for I/O requests that were issued to the device.  (和上一个很像)
            #util/(rd_ios[1] - rd_ios[0]) + (wr_ios[1] - wr_ios[0])
#:util     : Percentage  of  CPU time during which I/O requests were issued to the device
            #(tot_ticks[1] - tot_ticks[0]) / 1000 * 100

def calc(last, curr):
    SECTOR_SIZE = 512
    stat = {}

    def diff(field):
        return (curr[field] - last[field]) / (curr["ts"] - last["ts"])

    stat['rrqm/s']   = diff('r_merges')
    stat['wrqm/s']   = diff('w_merges')
    stat['r/s']      = diff('r_ios')
    stat['w/s']      = diff('w_ios')
    stat['rkB/s']    = diff('r_sec') * SECTOR_SIZE / 1024
    stat['wkB/s']    = diff('w_sec') * SECTOR_SIZE / 1024

    stat['avqqu-sz'] = diff('rq_ticks') / 1000
    print 'tot_ticks', curr['tot_ticks'], last['tot_ticks']
    stat['util']     = diff('tot_ticks')/10 #???

    if diff('r_ios') + diff('w_ios') > 0:
        stat['avgrq-sz'] = ( diff('r_sec') + diff('w_sec') ) / ( diff('r_ios') + diff('w_ios') )
        stat['await']    = ( diff('r_ticks') + diff('w_ticks') ) / ( diff('r_ios') + diff('w_ios') )
        stat['svctm']    = diff('tot_ticks') / ( diff('r_ios') + diff('w_ios') )
    else:
        stat['avgrq-sz'] = 0
        stat['await']    = 0
        stat['svctm']    = 0

    return stat

last = None
def tick():
    global last
    curr = disk_io_counters()
    if not last:
        last =  curr
        return

    stat = {}
    for dev in curr.keys():
        stat[dev] = calc(last[dev], curr[dev])
    last = curr
    return stat


def printstat(stat):
    print datetime.now(),
    for k, v in stat.items():
        print '%s: %.2f' % (k, float(v)) ,
    print ''

def main():
    """docstring for main"""
    pprint(disk_io_counters())
    while True:
        stat = tick()
        if stat:
            for dev in stat.keys():
                print dev,
                printstat(stat[dev])
        time.sleep(10)

def call_iostat(dev, interval):
    cmd = 'iostat -kxt %d 2' % interval
    out = commands.getoutput(cmd)
    lines = out.split('\n')
    lines.reverse()

    def line_to_dict(line):
        #Device:         rrqm/s   wrqm/s     r/s     w/s    rkB/s    wkB/s avgrq-sz avgqu-sz   await  svctm  %util
        fields = line.split()

        stat = {}
        stat['rrqm/s']   = fields[1]
        stat['wrqm/s']   = fields[2]
        stat['r/s']      = fields[3]
        stat['w/s']      = fields[4]
        stat['rkB/s']    = fields[5]
        stat['wkB/s']    = fields[6]

        stat['avgrq-sz'] = fields[7]
        stat['avqqu-sz'] = fields[8]

        stat['await']    = fields[9]
        stat['svctm']    = fields[10]
        stat['util']     = fields[11]
        return stat

    for line in lines:
        if line.startswith(dev):
            return line_to_dict(line)

def check():

    while True:
        stat = tick()
        if stat:
            printstat(stat['sda'])
        #time.sleep(10)
        printstat(call_iostat('sda', 10))

if __name__ == "__main__":
    #main()
    check()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4


