import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from active_redis import ActiveRedis
from redis import Redis

aredis = ActiveRedis(Redis())

mylist = aredis.list('foo')
mylist.append('foo')
mylist.append('bar')
mylist[1] = 'baz'

otherlist = aredis.list()
otherlist.append('bank')
otherlist.append('money!')
print 'money!' in otherlist
del otherlist[1]
print 'money!' in otherlist

mylist.append(otherlist)
mylist.delete()

mydict = aredis.dict()
mydict['foo'] = 'foo'
mydict['bar'] = 'bar'
mydict['bar'] = 'baz'

myset = aredis.set()
myset.add('foo')
print len(myset)

mydict['baz'] = myset
print len(mydict['baz'])
mydict.delete()

activeredis = ActiveRedis(Redis())

# Create a new dict with the key 'foo_dict'.
foodict = activeredis.dict('foo_dict')
foodict['foo'] = []

# Store a JSON serialized list ['bar'] at key 'foo_dict' field 'foo'.
foodict['foo'] = ['bar']

# Even once the list has been serialized, we can still append new
# values to the list and it will be automatically re-serialized.
# Active Redis internally wraps and monitors the list for changes.
foodict['foo'].append('baz')

# Create a new list with the key 'foo_list'.
foolist = activeredis.list('foo_list')

# Append the dict 'foo_dict' to the list.
# This will RPUSH an Active Redis reference to 'foo_dict'.
foolist.append(foodict)

print foolist[0]['foo'] # ['bar', 'baz']

# We can load the objects using the same keys.
del foodict
foodict = activeredis.dict('foo_dict')
print foodict['foo'] # ['bar', 'baz']

del foolist
foolist = activeredis.list('foo_list')
print foolist[0]['foo'] # ['bar', 'baz']

# If we want to actually delete the keys, call the delete() method.
# This will delete all referenced keys as well.
foolist.delete()

try:
  foodict['foo'] # Not happening.
except KeyError:
  print "foodict['foo'] is gone!"
else:
  print "foodict['foo'] is not gone!"

# Finally, if key names are irrelevant (such as in the case of
# a job queue) Active Redis can automatically generate unique keys.
fooset = activeredis.set()
fooset.add('foo')
fooset.add('bar')

# Event complex operations are supported via server-side Lua scripting.
barset = activeredis.set()
barset.add('bar')
barset.add('baz')

fooset &= barset
