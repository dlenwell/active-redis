# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
from active_redis.core import DataType
from active_redis.registry import DataType as Registry

@Registry.register
class Set(DataType):
  """
  A Redis set data type.
  """
  type = 'set'
  scripts = {}

  def add(self, item):
    """Adds an item to the set."""
    self.redis.sadd(self.key, self.encode(item))

  def remove(self, item):
    """Removes an item from the set."""
    if item in self:
      self.redis.srem(self.key, self.encode(item))
    else:
      raise KeyError("Item not in set.")

  def discard(self, item):
    """Discards an item from the set."""
    self.redis.srem(self.key, self.encode(item))

  def pop(self):
    """Pops an item from the set."""
    item = self.redis.spop(self.key)
    if item is None:
      raise KeyError("Set is empty.")
    else:
      return self.decode(item)

  def clear(self):
    """Clears all items from the set."""
    self.redis.delete(self.key)

  def update(self, other):
    """Updates items in the set with items from 'other'."""
    self.redis.sadd(self.key, [self.encode(item) for item in other])

  def union(self, other):
    """Performs a union on two sets."""
    newset = DataType.get_handler(self.type)(self.redis)
    if self.encoder._is_redis_item(other):
      self.redis.sunionstore(newset.key, self.key, other.key)
    else:
      self._execute_script('union_struct', newset.key, self.key, self._create_unique_key(), [self.encode(item) for item in other])
    return newset

  def intersection(self, other):
    """Performs an intersection on two sets."""
    newset = DataType.get_handler(self.type)(self.redis)
    if self.encoder._is_redis_item(other):
      self.redis.sinterstore(newset.key, self.key, other.key)
    else:
      self._execute_script('intersection_struct', newset.key, self.key, self._create_unique_key(), [self.encode(item) for item in other])
    return newset

  def intersection_update(self, other):
    """Updates the set via intersection."""
    if self.encoder._is_redis_item(other):
      self.redis.sinterstore(self.key, self.key, other.key)
    else:
      self._execute_script('intersection_struct', self.key, self.key, self._create_unique_key(), [self.encode(item) for item in other])
    return self

  def difference(self, other):
    """Performs a diff on two sets."""
    newset = DataType.get_handler(self.type)(self.redis)
    if self.encoder._is_redis_item(other):
      self.redis.sdiffstore(newset.key, self.key, other.key)
    else:
      self._execute_script('difference_struct', newset.key, self.key, self._create_unique_key(), [self.encode(item) for item in other])
    return newset

  def symmetric_difference(self, other):
    """Returns a set of elements on one set or the other."""
    # Remember to check whether 'other' is a Redis set or normal Python set.
    newset = DataType.get_handler(self.type)(self.redis)
    if self.encoder._is_redis_item(other):
      self._execute_script('symmetric_difference_redis', newset.key, self.key, other.key)
    else:
      self._execute_script('symmetric_difference_struct', newset.key, self.key, self._create_unique_key(), [self.encode(item) for item in other])
    return newset

  def symmetric_difference_update(self, other):
    """Updates the set via symmetric difference."""
    if self.encoder._is_redis_item(other):
      self._execute_script('symmetric_difference_redis', self.key, self.key, other.key)
    else:
      self._execute_script('symmetric_difference_struct', self.key, self.key, self._create_unique_key(), [self.encode(item) for item in other])
    return self

  def issubset(self, other):
    """Returns a boolean indicating whether every element in the set is in 'other'."""
    if self.encoder._is_redis_item(other):
      return self._execute_script('subset_redis', self.key, other.key)
    else:
      return self._execute_script('subset_struct', self.key, [self.encode(item) for item in other])

  def issuperset(self, other):
    """Returns a boolean indicating whether every element in 'other' is in the set."""
    if self.encoder._is_redis_item(other):
      return self._execute_script('superset_redis', self.key, other.key)
    else:
      return self._execute_script('superset_struct', self.key, [self.encode(item) for item in other])

  def copy(self):
    """Copies the set."""
    newset = DataType.get_handler(self.type)(self.redis)
    self.redis.sunionstore(newset.key, self.key)
    return newset

  def __len__(self):
    """Supports use of the global len() function."""
    return self.redis.scard(self.key)

  def __iter__(self):
    """Returns an iterator over the set."""
    items = self.redis.smembers(self.key)
    return iter(set([self.decode(item) for item in items]))

  def __contains__(self, item):
    """Supports the 'in' and 'not in' operators."""
    return self.redis.sismember(self.key, self.encode(item))

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

@Set.script
class SetUnionStruct(Script):
  """
  Performs a union on one Redis struct and one Python struct.
  """
  id = 'union_struct'
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

@Set.script
class SetIntersectStruct(Script):
  """
  Performs an intersection on one Redis struct and one Python struct.
  """
  id = 'intersection_struct'
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

@Set.script
class SetDiffStruct(Script):
  """
  Performs an intersection on one Redis struct and one Python struct.
  """
  id = 'difference_struct'
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

@Set.script
class SetSymmetricDifferenceRedis(Script):
  """
  Returns a set of elements in one set or the other but not both.
  """
  id = 'symmetric_difference_redis'
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

@Set.script
class SetSymmetricDifferenceStruct(Script):
  """
  Returns a set of elements in one set or the other but not both.
  """
  id = 'symmetric_difference_struct'
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

@Set.script
class SetSubsetRedis(Script):
  """
  Returns a boolean indicating whether a set is a subset of set1.
  """
  id = 'subset_redis'
  keys = ['set1', 'set2']

  script = """
  local set1 = KEYS[1]
  local set2 = KEYS[2]

  return #redis.call('SDIFF', set1, set2) == 0
  """

@Set.script
class SetSubsetStruct(Script):
  """
  Returns a boolean indicating whether a set is a subset of set1.
  """
  id = 'subset_struct'
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

@Set.script
class SetSupersetRedis(Script):
  """
  Returns a boolean indicating whether a set is a superset of set1.
  """
  id = 'superset_redis'
  keys = ['set1', 'set2']

  script = """
  local set1 = KEYS[1]
  local set2 = KEYS[2]

  return #redis.call('SDIFF', set2, set1) == 0
  """

@Set.script
class SetSupersetStruct(Script):
  """
  Returns a boolean indicating whether a set is a superset of set1.
  """
  id = 'superset_struct'
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
