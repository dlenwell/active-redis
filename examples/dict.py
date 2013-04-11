# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from active_redis import ActiveRedis

redis = ActiveRedis()

# Create an unnamed dictionary.
mydict = redis.dict()

# Add items to the dictionary.
mydict['foo'] = '1'
mydict['bar'] = '2'

# Note that when adding a complex data structure the structure
# will be serialized to JSON when written to Redis. However, the
# structure will still be monitored for changes, so even once a
# list is serialized it can still be mutated, and Active Redis
# will capture changes and re-serialize the dictionary.
mydict['baz'] = ['foo', 'bar']
mydict['baz'].append('baz')
mydict.delete()

# We can also create a named dict by passing a key to the constructor.
mydict = redis.dict('mydict')
mydict['foo'] = 'bar'
del mydict

mydict = redis.dict('mydict')
print mydict # {'foo': u'bar'}

mydict.delete()
print mydict # {}
