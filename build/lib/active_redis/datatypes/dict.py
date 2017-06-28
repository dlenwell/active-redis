# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
from active_redis.core import DataType, Observer, Script
from active_redis.registry import datatype

class SetDefault(Script):
  """
  Sets the value or default value of a dict item.
  """
  keys = ['key']
  args = ['field', 'default']

  script = """
  local key = KEYS[1]
  local field = ARGV[1]

  local exists = redis.call('HEXISTS', key, field)
  if exists then
    return redis.call('HGET', key, field)
  else
    local default = ARGV[2]
    redis.call('HSET', key, field, default)
    return default
  end
  """

class PopItem(Script):
  """
  Pops and returns an item from the dictionary.
  """
  keys = ['key']

  script = """
  local key = KEYS[1]
  local keys = redis.call('HKEYS', key)
  if keys[1] != nil then
    local val = redis.call('HGET', key, keys[1])
    redis.call('HDEL', key, keys[1])
    return val
  end
  return nil
  """

@datatype
class Dict(DataType, Observer):
  """
  A Redis dict data type.
  """
  type = 'dict'
  _scripts = {'set_default': SetDefault}

  def notify(self, subject, key):
    """Updates a dict subject."""
    self.__setitem__(key, subject)

  def clear(self):
    """Clears the dict."""
    self.client.delete(self.key)

  def get(self, key, default=None):
    """Gets a value from the dict."""
    item = self.client.hget(self.key, key)
    if item is not None:
      return self.client.decode(item)
    return default

  def has_key(self, key):
    """Indicates whether the given key exists."""
    return self.client.hexists(self.key, key)

  def items(self):
    """Returns all dict items."""
    return [(key, self.observe(self.client.decode(item), key)) for key, item in self.client.hgetall(self.key).items()]

  def iteritems(self):
    """Returns an iterator over dict items."""
    for key in self.client.hkeys(self.key):
      yield key, self.observe(self.client.decode(self.client.hget(self.key, key)), key)

  def keys(self):
    """Returns all dict keys."""
    return self.client.hkeys(self.key)

  def iterkeys(self):
    """Returns an iterator over dict keys."""
    return iter(self.client.hkeys(self.key))

  def values(self):
    """Returns all dict values."""
    return [self.observe(self.client.decode(self.client.hget(self.key, key)), key) for key in self.client.hkeys(self.key)]

  def itervalues(self):
    """Returns an iterator over dict values."""
    for key in self.client.hkeys(self.key):
      yield self.observe(self.client.decode(self.client.hget(self.key, key)), key)

  def pop(self, key, *args):
    """Pops a value from the dictionary."""
    item = self.client.hget(self.key, key)
    if item is not None:
      return self.client.decode(item)
    else:
      try:
        return args[0]
      except IndexError:
        raise KeyError("Invalid key %s." % (key,))

  def popitem(self):
    """Pops a random item from the dictionary."""
    item = self._execute_script('popitem', self.key)
    if item is not None:
      return self.client.decode(item)
    else:
      raise KeyError("Dictionary is empty.")

  def setdefault(self, key, default=None):
    """Sets a dict item value or default value."""
    return self._execute_script('setdefault', self.key, key, default)

  def delete(self, references=False):
    """Deletes the dictionary."""
    if references is True:
      for key, item in self.iteritems():
        if isinstance(item, DataType):
          item.delete()
    self.client.delete(self.key)

  def __len__(self):
    return self.client.hlen(self.key)

  def __iter__(self):
    """Iterates over dict keys."""
    return self.iterkeys()

  def __getitem__(self, key):
    """Gets a dict item."""
    item = self.client.hget(self.key, key)
    if item is not None:
      return self.observe(self.client.decode(item), key)
    else:
      raise KeyError("Key %s not found." % (key,))

  def __setitem__(self, key, item):
    """Sets a dict item."""
    return self.client.hset(self.key, key, self.client.encode(item))

  def __delitem__(self, key):
    """Deletes an item from the dict."""
    return self.client.hdel(self.key, key)

  def __contains__(self, key):
    """Supports using 'in' and 'not in' operators."""
    return self.has_key(key)

  def __repr__(self):
    return repr(dict(self.items()))
