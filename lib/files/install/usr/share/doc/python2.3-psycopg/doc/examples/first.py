# first.py -- first example of dbapi programming
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
    curs.execute("""CREATE TABLE test_first (name text, surname text,
                                             kudos int4)""")
except:
    conn.rollback()
    curs.execute("DROP TABLE test_first")
    curs.execute("""CREATE TABLE test_first (name text, surname text,
                                             kudos int4)""")
conn.commit()

## first insert using an ad-hoc dictionary

curs.execute("""INSERT INTO test_first
                VALUES (%(name)s, %(surname)s, %(kudos)d)""",
             {'name':'Federico', 'surname':'Di Gregorio', 'kudos':3})

## another two inserts using lists

l = (('Andrea', 'Fanfani', 0), ('Alice', 'Fontana', 5))
curs.executemany("""INSERT INTO test_first VALUES (%s, %s, %s)""", l)

## commit our changes to the database
conn.commit()

## extract and print the results

curs.execute("SELECT * FROM test_first")

row = curs.fetchone()
print "First row:\n   ", row[0], row[1], row[2]

rows = curs.fetchall()
print "Other rows:"
for row in rows:
    print "   ", row[0], row[1], row[2]

## drop the table

curs.execute("DROP TABLE test_first")
conn.commit()
