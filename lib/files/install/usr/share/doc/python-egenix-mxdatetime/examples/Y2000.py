#! /usr/bin/python -u
""" Y2000.py - The year 2000 countdown.
"""
from mx.DateTime import *
from time import sleep
import sys

while 1:
    d = Date(2000,1,1) - now()
    if d.days < 0:
        print 'Y2000... made it !'
        break
    print 'Y2000... time left: %2i days %2i hours %2i minutes %2i seconds\r'%\
          (d.day,d.hour,d.minute,d.second),
    sys.stdout.flush()
    sleep(1)
