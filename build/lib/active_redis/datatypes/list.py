# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
from active_redis.core import DataType, Observer, Script
from active_redis.registry import datatype

class ListInsert(Script):
  """
  Handles inserting an item into a list.
  """
  keys = ['key', 'index']
  args = ['item']

  script = """
  local key = KEYS[1]
  local index = KEYS[2]
  local item = ARGV[1]
  return redis.call('LINSERT', key, redis.call('LINDEX', key, index), item)
  """

class ListPop(Script):
  """
  Handles popping an item from a list.
  """
  keys = ['key']
  args = ['index']

  script = """
  local key = KEYS[1]
  local index = ARGV[1]
  local item = redis.call('LINDEX', key, index)
  redis.call('LSET', key, index, '____delete____')
  redis.call('LREM', key, 0, '____delete____')
  return item
  """

class ListCount(Script):
  """
  Handles counting the number of occurences of an item in a list.
  """
  keys = ['key']
  args = ['item']

  script = """
  local key = KEYS[1]
  local item = ARGV[1]

  local i = 0
  local count = 0
  local val = redis.call('LINDEX', i)
  while val do
    if val == item then
      count = count + 1
    end
    i = i + 1
    val = redis.call('LINDEX', i)
  end
  return count
  """

class ListContains(Script):
  """
  Indicates whether the list contains an object.
  """
  keys = ['key']
  args = ['item']

  script = """
  local key = KEYS[1]
  local item = ARGV[1]

  local i = 0
  local val = redis.call('LINDEX', key, i)
  while val do
    if val == item then
      return true
    end
    i = i + 1
    val = redis.call('LINDEX', key, i)
  end
  return false
  """

class ListReverse(Script):
  """
  Reverses all items in the list.
  """
  keys = ['key']

  # Copies the list to a temporary key and builds the list in reverse.
  script = """
  local key = KEYS[1]
  local tempkey = key..':reverse'
  redis.call('SUNIONSTORE', tempkey, key)
  redis.call('DEL', key)

  local item = redis.call('RPOP', tempkey)
  while item do
    redis.call('RPUSH', key)
    item = redis.call('RPOP', tempkey)
  end
  redis.call('DEL', tempkey)
  return true
  """

class ListDelete(Script):
  """
  Deletes an item from a list by index.
  """
  keys = ['key']
  args = ['index']

  script = """
  local key = KEYS[1]
  local index = ARGV[1]

  local delval = '____delete____'
  redis.call('LSET', key, index, delval)
  redis.call('LREM', key, 1, delval)
  """

@datatype
class List(DataType, Observer):
  """
  A Redis list data type.
  """
  type = 'list'
  _scripts = {
    'insert': ListInsert,
    'pop': ListPop,
    'count': ListCount,
    'contains': ListContains,
    'reverse': ListReverse,
    'delete': ListDelete,
  }

  def notify(self, subject, index):
    """Updates a list subject."""
    self.__setitem__(index, subject)

  def append(self, item):
    """Appends an item to the list."""
    self.client.rpush(self.key, self.client.encode(item))

  def extend(self, items):
    """Extends the list."""
    self.client.rpush(*[self.client.encode(item) for item in items])

  def insert(self, index, item):
    """Inserts an item into the list."""
    return self._execute_script('insert', self.key, index, self.client.encode(item))

  def remove(self, item):
    """Removes an item from the list."""
    self.client.lrem(self.key, self.client.encode(item))

  def pop(self, index=0):
    """Pops and returns an item from the list."""
    return self._execute_script('pop', self.key, index)

  def index(self, index):
    """Returns a list item by index."""
    item = self.client.lindex(self.key, index)
    if item is not None:
      return self.client.decode(item)
    else:
      raise IndexError("Index out of range.")

  def count(self, item):
    """Counts the number of occurences of an item in the list."""
    return self._execute_script('count', self.key, self.client.encode(item))

  def sort(self):
    """Sorts the list."""
    self.client.sort(self.key)
    return self

  def reverse(self):
    """Reverses the list."""
    self._execute_script('reverse', self.key)
    return self

  def delete(self, references=False):
    """Deletes the list."""
    if references is True:
      for item in self:
        if isinstance(item, DataType):
          item.delete()
    self.client.delete(self.key)

  def __iter__(self):
    """Returns an iterator."""
    i = 0
    item = self.client.lindex(self.key, i)
    while item is not None:
      yield self.observe(self.client.decode(item), i)
      i += 1
      item = self.client.lindex(self.key, i)

  def __len__(self):
    """Supports the len() global function."""
    return self.client.llen(self.key)

  def __getitem__(self, key):
    """Gets a list item."""
    item = self.client.lindex(self.key, key)
    if item is None:
      raise IndexError("Index out of range.")
    return self.observe(self.client.decode(item), key)

  def __setitem__(self, key, item):
    """Sets a list item."""
    return self.client.lset(self.key, key, self.client.encode(item))

  def __delitem__(self, key):
    """Deletes a list item."""
    try:
      return self._execute_script('delete', self.key, key)
    except ResponseError:
      raise IndexError("Index out of range.")

  def __contains__(self, item):
    """Supports using 'in' and 'not in' operators."""
    return self._execute_script('contains', self.key, self.client.encode(item))

  def __repr__(self):
    return repr([item for item in self])
