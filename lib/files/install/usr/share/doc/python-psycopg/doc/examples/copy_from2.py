# copy_from2.py -- example about COPY FROM file-like objects and exceptions
#
# Copyright (C) 2003 Federico Di Gregorio
# Based on code from Lex Berezhny.
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

import sys, StringIO, psycopg

if len(sys.argv) > 1:
    DSN = sys.argv[1]

print "Opening connection using dns:", DSN
conn = psycopg.connect(DSN)
curs = conn.cursor()

cast = [
    'Graham Chapman',
    'John Cleese',
    'Terry Gilliam',
    'Eric Idle',
    'Terry Jones',
    'Michael Palin']

# example of how to use a file-like object
names = StringIO.StringIO()
names.write('\n'.join(cast))
names.seek(0)

# good test
try:
    curs.execute("CREATE TABLE names (name varchar)")
except:
    conn.rollback()
    curs.execute("DROP TABLE names")
    curs.execute("CREATE TABLE names (name varchar)")
conn.commit()

# do the copy_from from a file-like object
curs.copy_from(names, 'names');
curs.execute("SELECT * FROM names")
print "Here are the names we copied:"
for l in curs.fetchall():
    print "   ", l[0]

# bad test
class NotStringIO:
    pass
try:
    curs.copy_from(NotStringIO(), 'names');
except AttributeError, error:
    print "And here is the error:"
    print error
    conn.rollback()
    
ages = StringIO.StringIO()
ages.write("too|many|columns|argh!\n")
ages.seek(0)

try:
    curs.copy_from(ages, 'ages');
except psycopg.ProgrammingError, error:
    print "And here is another error:"
    print error
    conn.rollback()

curs.execute("DROP TABLE names")
conn.rollback()
