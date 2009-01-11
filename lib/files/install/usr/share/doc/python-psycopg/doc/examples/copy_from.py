# copy_from.py -- example about copy_from 
#
# Copyright (C) 2002    Tom Jenkins <tjenkins@devis.com>
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

## put in DSN your DSN string

DSN = 'dbname=test user=test'

## don't modify anything below tis line (except for experimenting)

import sys, psycopg
import os, StringIO


if len(sys.argv) > 1:
    DSN = sys.argv[1]

print "Opening connection using dns:", DSN
conn = psycopg.connect(DSN)
curs = conn.cursor()

try:
    curs.execute("CREATE TABLE test_copy (fld1 text, fld2 text, fld3 int4)")
except:
    conn.rollback()
    curs.execute("DROP TABLE test_copy")
    curs.execute("CREATE TABLE test_copy (fld1 text, fld2 text, fld3 int4)")
conn.commit()

# demostrate copy_from functionality

# copy_from using defaults
io = open('copy_from.txt', 'wr')
data = ['Tom\tJenkins\t37\n', 'Madonna\t\N\t45\n',
        'Federico\tDi Gregorio\t\N\n']
io.writelines(data)
io.close()

io = open('copy_from.txt', 'r')
curs.copy_from(io, 'test_copy')
print "Copy %d records from file object into " % len(data) + \
      "table using default sep (\t) and null (\N)"
io.close()

curs.execute("SELECT * FROM test_copy")
rows = curs.fetchall()
print "Select using cursor returned %d rows" % len(rows)

for r in rows:
    print "%s\t%s\t%s" % (r[0], r[1], r[2])
curs.execute("delete from test_copy")
conn.commit()

#
# copy_from using custom separator
io = open('copy_from.txt', 'wr')
data = ['Tom:Jenkins:37\n', 'Madonna:\N:45\n', 'Federico:Di Gregorio:\N\n']
io.writelines(data)
io.close()

io = open('copy_from.txt', 'r')
curs.copy_from(io, 'test_copy', ':')
print "Copy %d records from file object into table using sep of :" % len(data)
io.close()

curs.execute("SELECT * FROM test_copy")
rows = curs.fetchall()
print "Select using cursor returned %d rows" % len(rows)

for r in rows:
    print "%s\t%s\t%s" % (r[0], r[1], r[2])
curs.execute("delete from test_copy")
conn.commit()

#
# copy_from using custom null identifier
io = open('copy_from.txt', 'wr')
data = ['Tom\tJenkins\t37\n', 'Madonna\tNULL\t45\n',
        'Federico\tDi Gregorio\tNULL\n']
io.writelines(data)
io.close()

io = open('copy_from.txt', 'r')
curs.copy_from(io, 'test_copy', '\t', 'NULL')
print "Copy %d records from file object into table " % len(data) + \
      "using sep of : and null of NULL"
io.close()

curs.execute("SELECT * FROM test_copy")
rows = curs.fetchall()
print "Select using cursor returned %d rows" % len(rows)

for r in rows:
    print "%s\t%s\t%s" % (r[0], r[1], r[2])
curs.execute("delete from test_copy")
conn.commit()

#
# copy_from using custom separator and null identifier
io = open('copy_from.txt', 'wr')
data = ['Tom:Jenkins:37\n', 'Madonna:NULL:45\n', 'Federico:Di Gregorio:NULL\n']
io.writelines(data)
io.close()

io = open('copy_from.txt', 'r')
curs.copy_from(io, 'test_copy', ':', 'NULL')
print "Copy %d records from file object into table using sep of :" % len(data)
io.close()

curs.execute("SELECT * FROM test_copy")
rows = curs.fetchall()
print "Select using cursor returned %d rows" % len(rows)

for r in rows:
    print "%s\t%s\t%s" % (r[0], r[1], r[2])
curs.execute("delete from test_copy")
conn.commit()

# error test
data = StringIO.StringIO()
data.write('\n'.join(['Tom\tJenkins\t37', 'Madonna\t\N\t45',
                      'Federico\tDi Gregorio\taaa']))
data.seek(0)
try:
    curs.copy_from(data, 'test_copy')
except StandardError, err:
    conn.rollback()
    print "Catched error (as expected):\n", err

conn.rollback()
curs.execute("DROP TABLE test_copy")
conn.commit()
os.unlink('copy_from.txt')


