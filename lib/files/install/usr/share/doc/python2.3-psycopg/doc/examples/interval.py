# interval.py - insert some intervals and check them
#
# Copyright (C) 2001 Federico Di Gregorio  <fog@debian.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# -*- Mode: pyhton -*-

## put in DSN your DSN string

DSN = 'dbname=test user=test'

## don't modify anything below tis line (except for experimenting)

import sys, psycopg

if len(sys.argv) > 1:
    DSN = sys.argv[1]

print "Opening connection using dns:", DSN
conn = psycopg.connect(DSN)
curs = conn.cursor()

try:
    curs.execute("CREATE TABLE test_interval (i interval)")
except StandardError, err:
    conn.rollback()
    print "Recovering from error:", err
    curs.execute("DROP TABLE test_interval")
    curs.execute("CREATE TABLE test_interval (i interval)")
    
conn.commit()

INTERVALS = ["00:06:00", "-00:06:11", "-0:12", "-0:00:23", "01:06:00",
             "5d 00:00:01", "5d 01:00:01", "-200d 00:01:00", "-40 y 1d"]

for i in INTERVALS:
    curs.execute("INSERT INTO test_interval VALUES ('" + i + "')")

curs.execute("SELECT * FROM test_interval")

for i1, i2 in zip(INTERVALS, curs.fetchall()):
    print i1, " -> ", i2

## drop the table

#curs.execute("DROP TABLE test_interval")
conn.commit()
