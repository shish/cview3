# bool.py - using boolean values
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

DSN = 'dbname=test user=fog'

## don't modify anything below tis line (except for experimenting)

import sys, psycopg, whrandom

if len(sys.argv) > 1:
    DSN = sys.argv[1]

print "Opening connection using dns:", DSN
conn = psycopg.connect(DSN)
curs = conn.cursor()

try:
    curs.execute("CREATE TABLE test_bool (v boolean, i int4)")
except:
    conn.rollback()
    curs.execute("DROP TABLE test_bool")
    curs.execute("CREATE TABLE test_bool (v boolean, i int4)")
conn.commit()

# this is the callable object we use as a typecast (the typecast is
# usually a function, but we use a class, just to demonstrate the
# flexibility of the psycopg casting system

class Boolean:
    """Very simple rectangle."""
    
    def __init__(self, s):
        """Init the rectangle from the string s."""
        if s == 't':
            self.value = True
        else:
            self.value = False

    def __str__(self):
        """Format self as a string usable by the db to represent a box."""
        if self.value:
            return "'t'"
        else:
            return "'f'"

    def __nonzero__(self):
        return self.value

    
# here we select from the empty table, just to grab the description
curs.execute("SELECT v FROM test_bool WHERE 0=1")
booloid = curs.description[0][1]
print "Oid for the boolean datatype is", booloid

# and build the user cast object
BOOLEAN = psycopg.new_type((booloid,), "BOOLEAN", Boolean)
psycopg.register_type(BOOLEAN)

# now insert some data
curs.execute("INSERT INTO test_bool VALUES ('t', 1)")
curs.execute("INSERT INTO test_bool VALUES ('f', 0)")

# select and print all value, then re-insert them
curs.execute("SELECT * FROM test_bool")
for row in curs.fetchall():
    print row
    curs.execute("INSERT INTO test_bool VALUES (%s, %d)", row)

# re-select
print
curs.execute("SELECT * FROM test_bool")
for row in curs.fetchall():
    print row
    
curs.execute("DROP TABLE test_bool")
conn.commit()
