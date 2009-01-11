# oid.py -  example of using lastoid() function
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
    curs.execute("CREATE TABLE test_oid (name text, surname text)")
except:
    curs.execute("DROP TABLE test_oid")
    curs.execute("CREATE TABLE test_oid (name text, surname text)")
conn.commit()

data = ({'name':'Federico', 'surname':'Di Gregorio'},
        {'name':'Michele', 'surname':'Comitini'})

curs.execute("""INSERT INTO test_oid
                VALUES (%(name)s, %(surname)s)""", data[0])

foid = curs.lastoid()
print "Oid for %(name)s %(surname)s" % data[0], "is", foid

curs.execute("""INSERT INTO test_oid
                VALUES (%(name)s, %(surname)s)""", data[1])
moid = curs.lastoid()
print "Oid for %(name)s %(surname)s" % data[1], "is", moid

curs.execute("SELECT * FROM test_oid WHERE oid = %d", (foid,))
print "Oid", foid, "selected %s %s" % curs.fetchone()

curs.execute("SELECT * FROM test_oid WHERE oid = %d", (moid,))
print "Oid", moid, "selected %s %s" % curs.fetchone()

curs.execute("DROP TABLE test_oid")
conn.commit()




