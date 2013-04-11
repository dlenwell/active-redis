# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
from active_redis.core import DataType, Script
from active_redis.registry import datatype

class UnionStruct(Script):
  """
  Performs a union on one Redis struct and one Python struct.
  """
  keys = ['newset', 'set1', 'set2']
  variable_args = True

  script = """
  local newset = KEYS[1]
  local set1 = KEYS[2]
  local set2 = KEYS[3]

  local set2args = ARGV

  if #set2args > 2 then
    redis.call('SADD', set2, unpack(set2args))
  end

  redis.call('SUNIONSTORE', newset, set1, set2)
  redis.call('DEL', set2)
  """

class IntersectionStruct(Script):
  """
  Performs an intersection on one Redis struct and one Python struct.
  """
  keys = ['newset', 'set1', 'set2']
  variable_args = True

  script = """
  local newset = KEYS[1]
  local set1 = KEYS[2]
  local set2 = KEYS[3]

  local set2args = ARGV

  if #set2args > 2 then
    redis.call('SADD', set2, unpack(set2args))
  end

  redis.call('SINTERSTORE', newset, set1, set2)
  redis.call('DEL', set2)
  """

class DifferenceStruct(Script):
  """
  Performs an intersection on one Redis struct and one Python struct.
  """
  keys = ['newset', 'set1', 'set2']
  variable_args = True

  script = """
  local newset = KEYS[1]
  local set1 = KEYS[2]
  local set2 = KEYS[3]

  local set2args = ARGV

  if #set2args > 2 then
    redis.call('SADD', set2, unpack(set2args))
  end

  redis.call('SDIFFSTORE', newset, set1, set2)
  redis.call('DEL', set2)
  """

class SymmetricDifferenceRedis(Script):
  """
  Returns a set of elements in one set or the other but not both.
  """
  keys = ['newset', 'set1', 'set2']

  script = """
  local newset = KEYS[1]
  local set1 = KEYS[2]
  local set2 = KEYS[3]

  local set1diff = set1 .. ":diff"
  local set2diff = set2 .. ":diff"
  redis.call('SDIFFSTORE', set1diff, set1, set2)
  redis.call('SDIFFSTORE', set2diff, set2, set1)
  redis.call('SUNIONSTORE', newset, set1diff, set2diff)
  redis.call('DEL', set1diff, set2diff)
  """

class SymmetricDifferenceStruct(Script):
  """
  Returns a set of elements in one set or the other but not both.
  """
  keys = ['newset', 'set1', 'set2']
  args = []
  variable_args = True

  script = """
  local newset = KEYS[1]
  local set1 = KEYS[2]
  local set2 = KEYS[3]

  -- Add set 2 items.
  local set2args = ARGV
  if #set2args > 0 then
    redis.call('SADD', set2, unpack(set2args))
  end

  local set1diff = set1 .. ":diff"
  local set2diff = set2 .. ":diff"
  redis.call('SDIFFSTORE', set1diff, set1, set2)
  redis.call('SDIFFSTORE', set2diff, set2, set1)
  redis.call('SUNIONSTORE', newset, set1diff, set2diff)
  redis.call('DEL', set1diff, set2diff, set2) -- Set 2 is automatically deleted as well.
  """

class SubsetRedis(Script):
  """
  Returns a boolean indicating whether a set is a subset of set1.
  """
  keys = ['set1', 'set2']

  script = """
  local set1 = KEYS[1]
  local set2 = KEYS[2]

  return #redis.call('SDIFF', set1, set2) == 0
  """

class SubsetStruct(Script):
  """
  Returns a boolean indicating whether a set is a subset of set1.
  """
  keys = ['set1']
  variable_args = True

  script = """
  local set1 = KEYS[1]
  local args = ARGV

  local tempset = set1 .. ':temp'
  redis.call('SADD', tempset, unpack(args))

  local count = #redis.call('SDIFF', set1, tempset)
  redis.call('DEL', diffset)
  return count == 0
  """

class SupersetRedis(Script):
  """
  Returns a boolean indicating whether a set is a superset of set1.
  """
  keys = ['set1', 'set2']

  script = """
  local set1 = KEYS[1]
  local set2 = KEYS[2]

  return #redis.call('SDIFF', set2, set1) == 0
  """

class SupersetStruct(Script):
  """
  Returns a boolean indicating whether a set is a superset of set1.
  """
  keys = ['set1']
  variable_args = True

  script = """
  local set1 = KEYS[1]
  local args = ARGV

  local tempset = set1 .. ':temp'
  redis.call('SADD', tempset, unpack(args))

  local count = #redis.call('SDIFF', tempset, set1)
  redis.call('DEL', tempset)
  return count == 0
  """

@datatype
class Set(DataType):
  """
  A Redis set data type.
  """
  type = 'set'
  _scripts = {
    'union_struct': UnionStruct,
    'intersect_struct': IntersectionStruct,
    'difference_struct': DifferenceStruct,
    'symmetric_difference_redis': SymmetricDifferenceRedis,
    'symmetric_difference_struct': SymmetricDifferenceStruct,
    'subset_redis': SubsetRedis,
    'subset_struct': SubsetStruct,
    'superset_redis': SupersetRedis,
    'superset_struct': SupersetStruct,
  }

  def add(self, item):
    """Adds an item to the set."""
    self.client.sadd(self.key, self.client.encode(item))

  def remove(self, item):
    """Removes an item from the set."""
    if item in self:
      self.client.srem(self.key, self.client.encode(item))
    else:
      raise KeyError("Item not in set.")

  def discard(self, item):
    """Discards an item from the set."""
    self.client.srem(self.key, self.client.encode(item))

  def pop(self):
    """Pops an item from the set."""
    item = self.redis.spop(self.key)
    if item is None:
      raise KeyError("Set is empty.")
    else:
      return self.client.decode(item)

  def clear(self):
    """Clears all items from the set."""
    self.client.delete(self.key)

  def update(self, other):
    """Updates items in the set with items from 'other'."""
    self.client.sadd(self.key, [self.client.encode(item) for item in other])

  def union(self, other):
    """Performs a union on two sets."""
    newset = DataType.get(self.type)(self.client)
    if self.client._is_redis_item(other):
      self.client.sunionstore(newset.key, self.key, other.key)
    else:
      self._execute_script('union_struct', newset.key, self.key, self._create_unique_key(), [self.client.encode(item) for item in other])
    return newset

  def intersection(self, other):
    """Performs an intersection on two sets."""
    newset = DataType.get(self.type)(self.client)
    if self.client._is_redis_item(other):
      self.client.sinterstore(newset.key, self.key, other.key)
    else:
      self._execute_script('intersection_struct', newset.key, self.key, self._create_unique_key(), [self.client.encode(item) for item in other])
    return newset

  def intersection_update(self, other):
    """Updates the set via intersection."""
    if self.client._is_redis_item(other):
      self.client.sinterstore(self.key, self.key, other.key)
    else:
      self._execute_script('intersection_struct', self.key, self.key, self._create_unique_key(), [self.client.encode(item) for item in other])
    return self

  def difference(self, other):
    """Performs a diff on two sets."""
    newset = DataType.get(self.type)(self.client)
    if self.client._is_redis_item(other):
      self.client.sdiffstore(newset.key, self.key, other.key)
    else:
      self._execute_script('difference_struct', newset.key, self.key, self._create_unique_key(), [self.client.encode(item) for item in other])
    return newset

  def symmetric_difference(self, other):
    """Returns a set of elements on one set or the other."""
    # Remember to check whether 'other' is a Redis set or normal Python set.
    newset = DataType.get(self.type)(self.client)
    if self.client._is_redis_item(other):
      self._execute_script('symmetric_difference_redis', newset.key, self.key, other.key)
    else:
      self._execute_script('symmetric_difference_struct', newset.key, self.key, self._create_unique_key(), [self.client.encode(item) for item in other])
    return newset

  def symmetric_difference_update(self, other):
    """Updates the set via symmetric difference."""
    if self.client._is_redis_item(other):
      self._execute_script('symmetric_difference_redis', self.key, self.key, other.key)
    else:
      self._execute_script('symmetric_difference_struct', self.key, self.key, self._create_unique_key(), [self.client.encode(item) for item in other])
    return self

  def issubset(self, other):
    """Returns a boolean indicating whether every element in the set is in 'other'."""
    if self.client._is_redis_item(other):
      return self._execute_script('subset_redis', self.key, other.key)
    else:
      return self._execute_script('subset_struct', self.key, [self.client.encode(item) for item in other])

  def issuperset(self, other):
    """Returns a boolean indicating whether every element in 'other' is in the set."""
    if self.client._is_redis_item(other):
      return self._execute_script('superset_redis', self.key, other.key)
    else:
      return self._execute_script('superset_struct', self.key, [self.client.encode(item) for item in other])

  def copy(self):
    """Copies the set."""
    newset = DataType.get(self.type)(self.client)
    self.client.sunionstore(newset.key, self.key)
    return newset

  def delete(self):
    """Deletes the set."""
    for item in self:
      if isinstance(item, DataType):
        item.delete()
    self.client.delete(self.key)

  def __len__(self):
    """Supports use of the global len() function."""
    return self.client.scard(self.key)

  def __iter__(self):
    """Returns an iterator over the set."""
    items = self.client.smembers(self.key)
    return iter(set([self.client.decode(item) for item in items]))

  def __contains__(self, item):
    """Supports the 'in' and 'not in' operators."""
    return self.client.sismember(self.key, self.client.encode(item))

  def __le__(self, other):
    """Alias for determining whether the set is a subset of 'other'."""
    return self.issubset(other)

  def __ge__(self, other):
    """Alias for determining whether the set is a superset of 'other'."""
    return self.issuperset(other)

  def __or__(self, other):
    """Alias for performing a union."""
    return self.union(other)

  def __ior__(self, other):
    """Alias for updating the set."""
    return self.update(other)

  def __xor__(self, other):
    """Alias for performing a symmetric difference operation."""
    return self.symmetric_difference(other)

  def __and__(self, other):
    """Alias for performing an intersection."""
    return self.intersection(other)

  def __iand__(self, other):
    """Alias for performing an intersection update."""
    return self.intersection_update(other)

  def __sub__(self, other):
    """Alias for performing a difference."""
    return self.difference(self.key, other.key)

  def __isub__(self, other):
    """Alias for performing a difference update."""
    return self.difference_update(other)

  def __ixor__(self, other):
    """Alias for performing a symmetric difference update."""
    return self.symmetric_difference_update(other)

  def __repr__(self):
    return repr(set([item for item in self]))
