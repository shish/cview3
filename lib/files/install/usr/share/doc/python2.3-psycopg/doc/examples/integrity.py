# integrity.py - test for IntegrityError
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
    curs.execute("CREATE TABLE test_integrity (val int4 unique)")
except:
    conn.rollback()
    curs.execute("DROP TABLE test_integrity")
    curs.execute("CREATE TABLE test_integrity (val int4 unique)")
conn.commit()

# insert 20 rows in the table
for i in range(20):
    curs.execute("INSERT INTO test_integrity VALUES (%d)", (i,))

# insert the row that cause the exception
try:
    curs.execute("INSERT INTO test_integrity VALUES (%d)", (0,))
except psycopg.IntegrityError, err:
    print "Error catched, it was:"
    print err

# lets experiment:the transaction aborted, so we should *not*
# find any data in the db even if we commit
conn.commit()
curs.execute("SELECT * FROM test_integrity")
print "Rows fetched:", len(curs.fetchall())

# cleanup
curs.execute("DROP TABLE test_integrity")
conn.commit()


