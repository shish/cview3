import psycopg, UserDict, UserList

o = psycopg.connect(database='test')
c = o.cursor()
c.execute("SELECT %s AS foo", ('zip',))
print c.fetchone()
c.execute("SELECT %(zip)s AS foo", {'zip':'zip'})
print c.fetchone()

d = UserDict.UserDict()
d['zip'] = 'zip'
c.execute("SELECT %(zip)s AS foo", d)
print c.fetchone()

l = UserList.UserList(['zip'])
c.execute("SELECT %s AS foo", l)
print c.fetchone()

c.execute("SELECT 'zip' AS foo", l)
print c.fetchone()

c.execute("SELECT 'zip' AS foo", d)
print c.fetchone()

c.execute("SELECT %s AS foo", d)
c.execute("SELECT %(zip)s AS foo", l)



