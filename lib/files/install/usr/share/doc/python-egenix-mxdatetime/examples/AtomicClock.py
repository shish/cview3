#! /usr/bin/python -u

""" AtomicClock.py - Access the NIST standard time service.

    The script will output the current time together with a marker
    indicating the source of information (NIST = genuine NIST signal,
    [NIST] = NIST calibrated CPU clock, CPU = uncalibrated CPU clock).

    You can call this script with a calibration float as parameter.
    It will then be set as calibration for the NIST module to use.

"""
import sys
import mx.DateTime.NIST
import mx.DateTime
from time import sleep

if len(sys.argv) == 2:
    try:
        mx.DateTime.NIST.set_calibration(float(sys.argv[1]))
    except ValueError:
        pass

def run():
    while 1:

        if mx.DateTime.NIST.calibrating and mx.DateTime.NIST.online():
            # Using the real thing
            marker = 'NIST'
        elif mx.DateTime.NIST.calibrated:
            # Using calibrated CPU clock
            marker = '[NIST]'
        else:
            # Using the uncalibrated CPU clock
            marker = 'CPU'

        # Get and show time
        utc = mx.DateTime.NIST.utctime()
        print '  %-6s Local: %s | UTC: %s | %+6.2fs\r' % \
              (marker,mx.DateTime.utc2local(utc),utc,
               mx.DateTime.NIST.calibration),
        sys.stdout.flush()
        sleep(1)

        # Recalibrate every 10 minutes
        if utc.minute % 10 == 0:
            mx.DateTime.NIST.reset_auto_calibration()

if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print
        print 'Current CPU clock calibration:',mx.DateTime.NIST.calibration
