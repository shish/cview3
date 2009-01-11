# this script is a regression test for the psycopg type system. its output
# should be identical to the types.result files; any other result is an
# indication of an error in the psycopg type system.

import sys
from psycopg import *
from mx import DateTime

if len(sys.argv) > 1:
    DSN = sys.argv[1]
else:
    sys.stderr.write("Error: missing connection DSN\n")
    sys.exit(1)


class Infinity:
    def __init__(self, sign=1, typ='timestamp'):
        self.sign = sign
        self.type = typ
    def __str__(self):
        if self.sign < 0: return "%s '-infinity'" % self.type
        else: return "%s 'infinity'" % self.type
        
TYPES = (('name1', ('char(8)', 'aAbBcCdD')),
         ('name2', ('varchar(8)', 'aAbBcCdD')),
         ('name3', ('text', 'aAbBcCdD')),
         ('ivalue1', ('int8', 0)),
         ('ivalue2', ('int4', 256)),
         ('ivalue3', ('int2', -1)),
         ('fvalue1', ('float4', 0.0)),
         ('fvalue2', ('float8', 10e10)),
         ('boolean1', ('boolean', 't')),
         ('time1', ('time', Time(13,12,11))),
         ('date1', ('date', Date(1971,10,19))),
         ('datetime1', ('timestamp', Timestamp(2001, 10, 13, 7, 8, 9))),
         ('datetime2', ('timestamp', Infinity())),
         ('datetime3', ('timestamp', Infinity(-1))),
         ('interval1', ('interval', '2 days')),
         ('interval2', ('interval', '1 day 12:00:00')),
         ('interval3', ('interval', '6:00')),
         ('interval4', ('interval', '10 days 00:00:01')),
         ('interval5', ('interval', '1 year 2 months -1 day')),
         ('interval6', ('interval', '3 days 00:03:59.93')),
         ('binary1',  ('bytea', Binary(r'\\\001\002\003\004\\'))))
         
CHECKS = [NUMBER, LONGINTEGER, INTEGER, FLOAT, STRING, BOOLEAN,
          DATETIME, DATE, TIME, INTERVAL, BINARY, ROWID]


o = connect(DSN)
c = o.cursor()


## create the table
create = "CREATE TABLE types_test ("
for k, v in TYPES:
    create = create + "\n    %s %s, " % (k, v[0])
create = create[:-2] + "\n)"

c.execute(create)


## insert a row of data and a row of NULLs in the table
ins1 = ins2 = "INSERT INTO types_test VALUES ("
dict = {}
for k, v in TYPES:
    dict[k] = v[1]
    ins1 = ins1 + "%%(%s)s, " % k
    ins2 = ins2 + "NULL, "
ins1 = ins1[:-2] + ")"
ins2 = ins2[:-2] + ")"

c.execute(ins1, dict)
c.execute(ins2)


## now select from the tables and print data and types

def test(type):
    s = ''
    for t in CHECKS:
        if t == type: s = s + '1'
        else: s = s + '0'
    return s

c.execute("SELECT * FROM types_test")

row = c.fetchone() 
for i in range(len(row)):
    if c.description[i][1] == LONGINTEGER:
        print repr(row[i]), test(c.description[i][1])
    else:
        print str(row[i]), test(c.description[i][1])


## check for the row id (oid)

c.execute("SELECT oid FROM types_test")
row = c.fetchone()
print "oid", test(c.description[0][1])

#o.commit()
