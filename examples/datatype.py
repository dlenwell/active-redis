# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# This is a basic data type example.
from active_redis import DataType, registry

@registry.datatype
class Queue(DataType):
  # The type string is used to allow the data type to be constructed
  # directly from the ActiveRedis class and helps unserialize the
  # data type when stored in Redis.
  type = 'queue'

  def push(self, item):
    """Push an item onto the queue."""
    self.client.rpush(self.key, item)

  def delete(self):
    """Delete the queue."""
    self.client.delete(self.key)

  def __repr__(self):
    pass

# Now we can use our data type.
from active_redis import ActiveRedis
redis = ActiveRedis()

myqueue = redis.queue()
myqueue.push('foo')
myqueue.push('bar')
