# dictfetch.py -- examples about using the dictfectch extension
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

curs.execute("CREATE TABLE test_dict (name text, surname text)")

data = ({'name':'Federico', 'surname':'Di Gregorio'},
        {'name':'Michele', 'surname':'Comitini'},
        {'name':'Richard', 'surname':'Stallman'})

curs.executemany("""INSERT INTO test_dict
                    VALUES (%(name)s, %(surname)s)""", data)

curs.execute("SELECT * FROM test_dict")

print "Fetching one row (dictionary):", curs.dictfetchone() 

print "Fetching other rows and cycling on rows and keys:"
rows = curs.dictfetchall()
for d in rows:
    for k in d.keys():
        print "Key:", k, "Value:", d[k],
    print
    
curs.execute("DROP TABLE test_dict")





