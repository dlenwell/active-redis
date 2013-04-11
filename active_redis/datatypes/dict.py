# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
from active_redis.core import DataType
from active_redis.registry import DataType as Registry

@Registry.register
class Hash(DataType):
  """
  A Redis hash data type.
  """
  type = 'hash'
  scripts = {}

  def update_subject(self, subject, index):
    """Updates a hash subject."""
    self.__setitem__(index, subject)

  def clear(self):
    """Clears the hash."""
    self.client.delete(self.key)

  def get(self, key, default=None):
    """Gets a value from the hash."""
    item = self.client.hget(self.key, key)
    if item is not None:
      return self.wrap(self.decode(item), key)
    return self.wrap(default, key)

  def has_key(self, key):
    """Indicates whether the given key exists."""
    return self.client.hexists(self.key, key)

  def items(self):
    """Returns all hash items."""
    return [(key, self.wrap(self.decode(item), key)) for key, item in self.client.hgetall(self.key).items()]

  def iteritems(self):
    """Returns an iterator over hash items."""
    for key in self.client.hkeys(self.key):
      yield key, self.wrap(self.decode(self.client.hget(self.key, key)), key)

  def keys(self):
    """Returns all hash keys."""
    return self.client.hkeys(self.key)

  def iterkeys(self):
    """Returns an iterator over hash keys."""
    return iter(self.client.hkeys(self.key))

  def values(self):
    """Returns all hash values."""
    return [self.wrap(self.decode(self.client.hget(self.key, key)), key) for key in self.client.hkeys(self.key)]

  def itervalues(self):
    """Returns an iterator over hash values."""
    for key in self.client.hkeys(self.key):
      yield self.wrap(self.decode(self.client.hget(self.key, key)), key)

  def pop(self, key, *args):
    """Pops a value from the dictionary."""
    item = self.client.hget(self.key, key)
    if item is not None:
      return self.wrap(self.decode(item), key)
    else:
      try:
        return args[0]
      except IndexError:
        raise KeyError("Invalid key %s." % (key,))

  def popitem(self):
    pass

  def setdefault(self, key, default=None):
    """Sets a hash item value or default value."""
    return self._execute_script('setdefault', self.key, key, default)

  def __len__(self):
    return self.client.hlen(self.key)

  def __iter__(self):
    """Iterates over hash keys."""
    return self.iterkeys()

  def __getitem__(self, key):
    """Gets a hash item."""
    item = self.client.hget(self.key, key)
    if item is not None:
      return self.wrap(self.decode(item), key)
    else:
      raise KeyError("Hash key %s not found." % (key,))

  def __setitem__(self, key, item):
    """Sets a hash item."""
    return self.client.hset(self.key, key, self.encode(item))

  def __delitem__(self, key):
    """Deletes an item from the hash."""
    return self.client.hdel(self.key, key)

  def __contains__(self, key):
    """Supports using 'in' and 'not in' operators."""
    return self.has_key(key)

@Hash.script
class HashSetDefault(Script):
  """
  Sets the value or default value of a hash item.
  """
  id = 'setdefault'
  keys = ['key', 'field']
  args = ['default']

  script = """
  var key = KEYS[1]
  var field = KEYS[2]

  var exists = redis.call('HEXISTS', key, field)
  if exists then
    return redis.call('HGET', key, field)
  else
    var default = ARGV[1]
    redis.call('HSET', key, field, default)
    return default
  end
  """
