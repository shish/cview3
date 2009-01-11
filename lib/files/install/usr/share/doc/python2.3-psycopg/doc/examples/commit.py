# commit.py -- example about autocommit and cursor isolation
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
conn1 = psycopg.connect(DSN)
curs1 = conn1.cursor()
curs2 = conn1.cursor()

try:
    curs1.execute("CREATE TABLE test_commit (zot text)")
except:
    conn.rollback()
    curs1.execute("DROP TABLE test_commit")
    curs1.execute("CREATE TABLE test_commit (zot text)")
conn1.commit()

# demostrate connection isolation, we expect data to be available to
# cursor 3 only after a commit on the connection 1 and 2, but cursor 2
# should be able to access the data immediately.

curs1.execute("INSERT INTO test_commit VALUES('Uagh-gag!')")
print "Inserted a single row into table using cursor 1 (connection 1)"

curs1.execute("SELECT * FROM test_commit")
rows = curs1.fetchall()
print "Select using cursor 1 (connection 1) returned %d rows" % len(rows)

curs2.execute("SELECT * FROM test_commit")
rows = curs2.fetchall()
print "Select using cursor 2 (connection 1) returned %d rows" % len(rows)

conn2 = psycopg.connect(DSN)
curs3 = conn2.cursor()

curs3.execute("SELECT * FROM test_commit")
rows = curs3.fetchall()
print "Select using cursor 3 (connection 2) returned %d rows" % len(rows)

conn1.commit()
print "Executed commit on connection 1"

curs3.execute("SELECT * FROM test_commit")
rows = curs3.fetchall()
print "Select using cursor 3 (connection 2) returned %d rows" % len(rows)

conn2.commit()
print "Executed commit on connection 2"

curs3.execute("SELECT * FROM test_commit")
rows = curs3.fetchall()
print "Select using cursor 3 (connection 2) returned %d rows" % len(rows)

conn2.autocommit()
print "Autocommit on connection 2"

curs1.execute("INSERT INTO test_commit VALUES('Uagh-gag-bloch!')")
print "Inserted another row into table using cursor 1 (connection 1)"

curs3.execute("SELECT * FROM test_commit")
rows = curs3.fetchall()
print "Select using cursor 3 (connection 2) returned %d rows" % len(rows)

conn1.commit()
print "Executed commit on connection 1"

curs3.execute("SELECT * FROM test_commit")
rows = curs3.fetchall()
print "Select using cursor 3 (connection 2) returned %d rows" % len(rows)

conn2.autocommit(0)
print "Autocommit off on connection 2"

curs1.execute("INSERT INTO test_commit VALUES('Uagh-gag-bloch!')")
print "Inserted another row into table using cursor 1 (connection 1)"

curs3.execute("SELECT * FROM test_commit")
rows = curs3.fetchall()
print "Select using cursor 3 (connection 2) returned %d rows" % len(rows)

conn1.commit()
print "Executed commit on connection 1"

curs3.execute("SELECT * FROM test_commit")
rows = curs3.fetchall()
print "Select using cursor 3 (connection 2) returned %d rows" % len(rows)

# uh-ops... if we don't destroy or commit() on connection 2 the
# database is locked in a transaction and can't drop!
conn2.rollback()

curs1.execute("DROP TABLE test_commit")
conn1.commit()



