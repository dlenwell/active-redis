# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from active_redis import ActiveRedis

redis = ActiveRedis()

# Create an unnamed list.
mylist = redis.list()

# Append items to the list.
mylist.append('foo')
mylist.append('bar')

# Note that when appending a complex data structure the structure
# will be serialized to JSON when written to Redis. However, the
# structure will still be monitored for changes, so even once a
# list is serialized it can still be mutated, and Active Redis
# will capture changes and re-serialize the list.
mylist.append(['foo', 'bar'])
mylist[2].append('baz')

# We can also create a named list by passing a key to the constructor.
mylist = redis.list('mylist')
mylist.append('foo')
del mylist

mylist = redis.list('mylist')
print mylist # ['foo']
