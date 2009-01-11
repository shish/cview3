# copy_to.py -- example about copy_to 
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

if len(sys.argv) > 1:
    DSN = sys.argv[1]

print "Opening connection using dns:", DSN
conn = psycopg.connect(DSN)
curs = conn.cursor()

try:
    curs.execute("CREATE TABLE test_copy (fld1 text, fld2 text, fld3 int4)")
except:
    curs.execute("DROP TABLE test_copy")
    curs.execute("CREATE TABLE test_copy (fld1 text, fld2 text, fld3 int4)")
conn.commit()

# demostrate copy_to functionality
data = [('Tom', 'Jenkins', '37'), ('Madonna', None, '45'), ('Federico', 'Di Gregorio', None)]
insert = 'insert into test_copy values (%s, %s, %s)'
for params in data:
    curs.execute(insert, params)
conn.commit()

# copy_to using defaults
io = open('copy_to.txt', 'w')
curs.copy_to(io, 'test_copy')
print "Copy %d records from table into file object using default sep (\\t) and null (\N)"%(len(data),)
io.close()

io = open('copy_to.txt', 'r')
rows = io.readlines()
print "File has %d rows" % len(rows)

for r in rows:
    print r,
io.close()

#
# copy_to using custom separator
io = open('copy_to.txt', 'w')
curs.copy_to(io, 'test_copy', ':')
print "Copy %d records from table into file object using custom sep (:)"%(len(data),)
io.close()

io = open('copy_to.txt', 'r')
rows = io.readlines()
print "File has %d rows" % len(rows)

for r in rows:
    print r,
io.close()

#
# copy_to using custom null identifier
io = open('copy_to.txt', 'w')
curs.copy_to(io, 'test_copy', '\t', 'NULL')
print "Copy %d records from table into file object using custom null (NULL)"%(len(data),)
io.close()

io = open('copy_to.txt', 'r')
rows = io.readlines()
print "File has %d rows" % len(rows)

for r in rows:
    print r,
io.close()

#
# copy_to using custom separator and null identifier
io = open('copy_to.txt', 'w')
curs.copy_to(io, 'test_copy', ':', 'NULL')
print "Copy %d records from table into file object using custom sep (:) and custom null (NULL)"%(len(data),)
io.close()

io = open('copy_to.txt', 'r')
rows = io.readlines()
print "File has %d rows" % len(rows)

for r in rows:
    print r,
io.close()


curs.execute("DROP TABLE test_copy")



