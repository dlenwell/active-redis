# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from active_redis import ActiveRedis

redis = ActiveRedis()

# Create an unnamed set.
myset = redis.set()

# Add items to the set.
myset.add('foo')
myset.add('bar')

# We can also create a named set by passing a key to the constructor.
myset = redis.set('myset')
myset.add('foo')
del myset

myset = redis.set('myset')
print myset # set([u'foo'])

myset.delete()
print myset # set()
