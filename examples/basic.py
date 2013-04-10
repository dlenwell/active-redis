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

myhash = aredis.hash()
myhash['foo'] = 'foo'
myhash['bar'] = 'bar'
myhash['bar'] = 'baz'

myset = aredis.set()
myset.add('foo')
print len(myset)

myhash['baz'] = myset
print len(myhash['baz'])
myhash.delete()

activeredis = ActiveRedis(Redis())

# Create a new hash with the key 'foo_hash'.
foohash = activeredis.hash('foo_hash')
foohash['foo'] = []

# Store a JSON serialized list ['bar'] at key 'foo_hash' field 'foo'.
foohash['foo'] = ['bar']

# Even once the list has been serialized, we can still append new
# values to the list and it will be automatically re-serialized.
# Active Redis internally wraps and monitors the list for changes.
foohash['foo'].append('baz')

# Create a new list with the key 'foo_list'.
foolist = activeredis.list('foo_list')

# Append the hash 'foo_hash' to the list.
# This will RPUSH an Active Redis reference to 'foo_hash'.
foolist.append(foohash)

print foolist[0]['foo'] # ['bar', 'baz']

# We can load the objects using the same keys.
del foohash
foohash = activeredis.hash('foo_hash')
print foohash['foo'] # ['bar', 'baz']

del foolist
foolist = activeredis.list('foo_list')
print foolist[0]['foo'] # ['bar', 'baz']

# If we want to actually delete the keys, call the delete() method.
# This will delete all referenced keys as well.
foolist.delete()

try:
  foohash['foo'] # Not happening.
except KeyError:
  print "foohash['foo'] is gone!"
else:
  print "foohash['foo'] is not gone!"

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
