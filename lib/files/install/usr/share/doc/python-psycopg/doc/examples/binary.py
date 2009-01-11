# binary.py -- example code for Binary objects and binary cursors
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

DSN = "dbname=test user=test"

## don't modify anything below tis line (except for experimenting)

import sys, psycopg, string

if len(sys.argv) > 1:
    DSN = sys.argv[1]

print "Opening connection using dns:", DSN
conn = psycopg.connect(DSN)
curs = conn.cursor()

try:
    curs.execute("CREATE TABLE test_binary (id int4, name text, img bytea)")
except:
    curs.execute("DROP TABLE test_binary")
    curs.execute("CREATE TABLE test_binary (id int4, name text, img bytea)")
conn.commit()

## load the binary data from a jpeg image
file_names = ('somehackers.jpg', 'whereareyou.jpg')

data = []
for file_name in file_names:
    data.append({
        'id':1,
        'name':file_name,
        'img':psycopg.Binary(open(file_name).read())})

curs.executemany("""INSERT INTO test_binary
                    VALUES (%(id)d, %(name)s, %(img)s)""", data)

print "\nExtracting the images as strings:"

curs.execute("SELECT * FROM test_binary")

for row in curs.fetchall():
    name, ext = string.split(row[1], '.')
    new_name = name + '_S.' + ext
    print "  writing %s to %s ..." % (name+'.'+ext, new_name),
    open(new_name, 'wb').write(row[2])
    print "done"


print "Extracting the images using a binary cursor:"

curs.execute("""DECLARE zot BINARY CURSOR FOR SELECT img, name FROM test_binary
                                          FOR READ ONLY""")
curs.execute("""FETCH ALL FROM zot""")

for row in curs.fetchall():
    name, ext = string.split(row[1], '.')
    new_name = name + '_B.' + ext
    print "  writing %s to %s ..." % (name, new_name),
    open(new_name, 'wb').write(row[0])
    print "done"

# this commit is requires because we can't drop a table with a binary
# cusor declared and still open
conn.commit()

curs.execute("DROP TABLE test_binary")
conn.commit()

print "\nNow try to load the new images, to check it worked!"
