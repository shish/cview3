""" Calculate some informations about lifespans.
"""
from mx.DateTime import *
import string,sys

# Get data from user
print 'Please enter your birthday (year,month,day), e.g. 1969,12,1:'
try:
    year,month,day = input('>>> ')
except:
    print '* Sorry, wrong entry.'
    sys.exit()
print

# Output the lifespan in different formats
birthday = Date(year,month,day)
lifespan = now() - birthday
print 'Lifespan:'
print ' =',lifespan.days,'days'
print ' =',int(lifespan / (29.53 * oneDay)),'moons (+/- 1)'
print ' =',lifespan / (365.2422 * oneDay),'tropical years'
