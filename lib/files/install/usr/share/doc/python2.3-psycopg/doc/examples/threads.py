# threads.py -- example of multiple threads using psycopg
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

## some others parameters
INSERT_THREADS = ('A', 'B', 'C')
SELECT_THREADS = ('1', '2')

ROWS = 1000

COMMIT_STEP = 20
SELECT_SIZE = 25001
SELECT_STEP = 500
SELECT_DIV  = 250
SERIALIZE   = 1

## don't modify anything below tis line (except for experimenting)

import sys, psycopg, threading

if len(sys.argv) > 1:
    DSN = sys.argv[1]
if len(sys.argv) > 2:
    SERIALIZE = int(sys.argv[2])
    
print "Opening connection using dns:", DSN
conn = psycopg.connect(DSN, serialize=SERIALIZE)
curs = conn.cursor()

try:
    curs.execute("""CREATE TABLE test_threads (
                        name text, value1 int4, value2 float)""")
except:
    conn.rollback()
    curs.execute("DROP TABLE test_threads")
    curs.execute("""CREATE TABLE test_threads (
                        name text, value1 int4, value2 float)""")
conn.commit()


## this function inserts a big number of rows and creates and destroys
## a large number of cursors

def insert_func(conn, rows):
    name = threading.currentThread().getName()
    
    if SERIALIZE: cmt = conn
    else: cmt = conn.cursor()
    
    for i in range(rows):
        if divmod(i, COMMIT_STEP)[1] == 0:
            cmt.commit()
            s = name + ": COMMIT STEP " + str(i)
            print s
            c = conn.cursor()
            if not SERIALIZE: cmt = c
        try:
            c.execute("INSERT INTO test_threads VALUES (%s, %d, %f)",
                      (str(i), i, float(i)))
        except psycopg.ProgrammingError, err:
            print name, ": an error occurred; skipping this insert"
            print err
    cmt.commit()

## a nice select function that prints the current number of rows in the
## database (and transefer them, putting some pressure on the network)
    
def select_func(conn, z):
    name = threading.currentThread().getName()

    c = conn.cursor()
    if SERIALIZE: cmt = conn
    else:
        cmt = None
        c.autocommit()
    
    for i in range(SELECT_SIZE):
        if divmod(i, SELECT_STEP)[1] == 0:
            try:
                c.execute("SELECT * FROM test_threads WHERE value2 < %d",
                          ((i/z),))
                l = c.fetchall()
                s = name + ": number of rows fetched: " + str(len(l))
                print s
            except psycopg.ProgrammingError, err:
                print name, ": an error occurred; skipping this select"
                print err

            # update the cursor if not in autocommit
            if cmt:
                cmt.commit()
            else:
                c = conn.cursor()
                c.autocommit()

## create the threads
threads = []

print "Creating INSERT threads:"
for name in INSERT_THREADS:
    t = threading.Thread(None, insert_func, 'Thread-'+name, (conn, ROWS))
    t.setDaemon(0)
    threads.append(t)

print "Creating SELECT threads:"
for name in SELECT_THREADS:
    t = threading.Thread(None, select_func, 'Thread-'+name, (conn, SELECT_DIV))
    t.setDaemon(0)
    threads.append(t)

## really start the threads now
for t in threads:
    t.start()

# and wait for them to finish
for t in threads:
    t.join()
    print t.getName(), "exited OK"


curs.execute("SELECT count(name) FROM test_threads")
print "Inserted", curs.fetchone()[0], "rows."

curs.execute("DROP TABLE test_threads")

