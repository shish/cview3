# dt.py - how to use date and time types
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
from mx import DateTime

if len(sys.argv) > 1:
    DSN = sys.argv[1]

print "Opening connection using dns:", DSN
conn = psycopg.connect(DSN)
curs = conn.cursor()

try:
    curs.execute("CREATE TABLE test_timestamp (t timestamp)")
except:
    curs.execute("DROP TABLE test_timestamp")
    curs.execute("CREATE TABLE test_timestamp (t timestamp)")
conn.commit()

t1 = psycopg.TimestampFromMx(DateTime.now())
t2 = psycopg.Timestamp(2001, 10, 31, 23, 55, 17)

print "Inserting two timestamps:"
print t1, "from", DateTime.now()
print t2, "from",  2001, 10, 31, 23, 55, 17

curs.executemany("INSERT INTO test_timestamp VALUES (%(stamp)s)",
                 ({'stamp':t1}, {'stamp':t2}))

curs.execute("SELECT * FROM test_timestamp")
rows = curs.fetchall()

print "Values returned by SELECT:"
print rows[0][0]
print rows[1][0]

curs.execute("DROP TABLE test_timestamp")
conn.commit()




