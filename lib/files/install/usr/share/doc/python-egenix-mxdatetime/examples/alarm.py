#! /usr/bin/python -u

""" Simple Forking Alarm

    Sample Application for DateTime types and CommandLine. Only works
    on OSes which support os.fork().

    Author: Marc-Andre Lemburg, mailto:mal@lemburg.com
"""
import time,sys,os
from mx.DateTime import *
from CommandLine import Application,ArgumentOption

class Alarm(Application):

    header = "Simple Forking Alarm"
    options = [ArgumentOption('-s',
                              'set the alarm to now + arg seconds'),
               ArgumentOption('-m',
                              'set the alarm to now + arg minutes'),
               ArgumentOption('-a',
                              'set the alarm to ring at arg (hh:mm)'),
               ]
    version = '0.1'

    def main(self):

        atime = now() + (self.values['-s'] or 
                         self.values['-m'] * 60 or 
                         self.values['-h'] * 3600) * oneSecond
        abs = self.values['-a']
        if abs:
            atime = strptime(abs,'%H:%M',today(second=0))
        if atime < now():
            print 'Alarm time has expired...'
            return
        print 'Alarm will ring at',atime
        if not os.fork():
            time.sleep((atime - now()).seconds)
            alarm()
            os._exit(0)

def alarm():

    """ Ring alarm
    """
    for i in range(10):
        sys.stdout.write('\007')
        sys.stdout.flush()
        time.sleep(0.2)

if __name__ == '__main__':
    Alarm()
