# usercast.py -- example of user defined typecasters
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
    curs.execute("CREATE TABLE test_cast (p1 point, p2 point, b box)")
except:
    conn.rollback()
    curs.execute("DROP TABLE test_cast")
    curs.execute("CREATE TABLE test_cast (p1 point, p2 point, b box)")
conn.commit()

# this is the callable object we use as a typecast (the typecast is
# usually a function, but we use a class, just to demonstrate the
# flexibility of the psycopg casting system

class Rect:
    """Very simple rectangle."""
    
    def __init__(self, s=None):
        """Init the rectangle from the optional string s."""
        self.x = self.y = self.width = self.height = 0.0
        if s: self.from_string(s)

    def from_points(self, x0, y0, x1, y1):
        """Init the rectangle from points."""
        if x0 > x1: (x0, x1) = (x1, x0)
        if y0 > y1: (y0, y1) = (y1, y0)
        self.x = x0
        self.y = y0
        self.width = x1 - x0
        self.height = y1 - y0

    def from_string(self, s):
        """Init the rectangle from a string."""
        seq = eval(s)
        self.from_points(seq[0][0], seq[0][1], seq[1][0], seq[1][1])

    def __str__(self):
        """Format self as a string usable by the db to represent a box."""
        s = "'((%d,%d),(%d,%d))'" % (
            self.x, self.y, self.x + self.width, self.y + self.height)
        return s

    def show(self):
        """Format a description of the box."""
        s = "X: %d\tY: %d\tWidth: %d\tHeight: %d" % (
            self.x, self.y, self.width, self.height)
        return s
    
# here we select from the empty table, just to grab the description
curs.execute("SELECT b FROM test_cast WHERE 0=1")
boxoid = curs.description[0][1]
print "Oid for the box datatype is", boxoid

# and build the user cast object
BOX = psycopg.new_type((boxoid,), "BOX", Rect)
psycopg.register_type(BOX)

# now insert 100 random data (2 points and a box in each row)
for i in range(100):
    p1 = (whrandom.randint(0,100), whrandom.randint(0,100))
    p2 = (whrandom.randint(0,100), whrandom.randint(0,100))
    b = Rect()
    b.from_points(whrandom.randint(0,100), whrandom.randint(0,100),
                  whrandom.randint(0,100), whrandom.randint(0,100))
    curs.execute("INSERT INTO test_cast VALUES ('%(p1)s', '%(p2)s', %(box)s)",
                 {'box':b, 'p1':p1, 'p2':p2})

# select and print all boxes with at least one point inside
curs.execute("SELECT b FROM test_cast WHERE p1 @ b OR p2 @ b")
boxes = curs.fetchall()
print "Found %d boxes with at least a point inside:" % len(boxes)
for box in boxes:
    print " ", box[0].show()

curs.execute("DROP TABLE test_cast")
conn.commit()
