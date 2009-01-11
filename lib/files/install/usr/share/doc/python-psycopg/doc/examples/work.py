# work.py -- how to switch to autocommit to directly use transactions
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
    curs.execute("CREATE TABLE test_work (val int4)")
except:
    curs.execute("DROP TABLE test_work")
    curs.execute("CREATE TABLE test_work (val int4)")
conn.commit()

# we use this function to format the output
def flatten(l):
    """Flattens list of tuples l."""
    return map(lambda x: x[0], l)

# insert 20 rows in the table
for i in range(20):
    curs.execute("INSERT INTO test_work VALUES(%d)", (i,))
conn.commit()

# switch to autocommit the connection
conn.autocommit()

# does some nice tricks with the transaction and postgres cursors
curs.execute("BEGIN WORK; DECLARE crs CURSOR FOR SELECT * FROM test_work")
curs.execute("FETCH 10 FROM crs")
print "First 10 rows:", flatten(curs.fetchall())
curs.execute("MOVE -5 FROM crs")
print "Moved back cursor by 5 rows (to row 5.)"
curs.execute("FETCH 10 FROM crs")
print "Another 10 rows:", flatten(curs.fetchall())
curs.execute("FETCH 10 FROM crs")
print "The remaining rows:", flatten(curs.fetchall())

# switch back from autocommit
conn.autocommit(0)
conn.commit()

curs.execute("DROP TABLE test_work")
conn.commit()


