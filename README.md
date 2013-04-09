Active Redis
============

Active Redis is a Python library for interacting with Redis data
structures via global Python classes. The library takes care of
mapping relationships between Python objects using the `list`,
`dict`, and `set` interfaces you already know.

Note that this library is still under development and currently
lacks tests.

```python
from active_redis import ActiveRedis
from redis import Redis

activeredis = ActiveRedis(Redis())

# Create a new hash with the key 'foo_hash'.
foohash = activeredis.hash('foo_hash')
foohash['foo'] = []

# Store a JSON serialized list ['bar'] at key 'foo_hash' field 'foo'.
foohash['foo'] = ['bar']

# Note that appending to the serialized list will not work, since
# Active Redis currently does not have a way to know when the list
# is updated. So this will not work.
foohash['foo'].append('baz')

# Create a new list with the key 'foo_list'.
foolist = activeredis.list('foo_list')

# Append the hash 'foo_hash' to the list.
# This will RPUSH an Active Redis reference to 'foo_hash'.
foolist.append(foohash)

print foolist[0]['foo'] # ['bar']

# We can load the objects using the same keys.
del foohash
foohash = activeredis.hash('foo_hash')
print foohash['foo'] # ['bar']

del foolist
foolist = activeredis.list('foo_list')
print foolist[0]['foo'] # ['bar']

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
```
