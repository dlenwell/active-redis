from .exception import DataTypeError, EncodingError, ScriptError
from redis.exceptions import ResponseError
import uuid, json

class Encoder(object):
  """
  Handles encoding and decoding of objects.
  """
  REDIS_STRUCTURE_PREFIX = 'redis:struct'
  ABSOLUTE_VALUE_PREFIX = 'redis:abs'

  def __init__(self, redis):
    self.redis = redis

  def encode(self, item):
    """Encodes a Python object."""
    if self._is_redis_item(item):
      return self._encode_redis_item(item)
    else:
      return self._encode_structure_item(item)

  def _is_redis_item(self, item):
    """Indicaites whether the item is a Redis data type."""
    return isinstance(item, DataType)

  def _encode_redis_item(self, item):
    """Encodes a Redis data type."""
    return "%s:%s" % (self.REDIS_STRUCTURE_PREFIX, item.key)

  def _encode_structure_item(self, item):
    """Encodes a structure."""
    return "%s:%s" % (self.ABSOLUTE_VALUE_PREFIX, json.dumps(item))

  def decode(self, value):
    """Decodes a stored value."""
    if self._is_redis_value(value):
      return self._decode_redis_value(value)
    elif self._is_structure_value(value):
      return self._decode_structure_value(value)
    else:
      raise EncodingError("Failed to decode value. Unknown data type.")

  def _is_redis_value(self, value):
    """Indicates whether the value is a Redis data type."""
    return value.startswith(self.REDIS_STRUCTURE_PREFIX)

  def _decode_redis_value(self, value):
    """Decodes a Redis data type value."""
    prefix, key = value.split(':', 1)
    type = self.redis.type(key)
    if type is None:
      raise EncodingError("Failed to decode value. Key %s does not exist.")
    return DataType.get_handler(type)(self.redis, key)

  def _is_structure_value(self, value):
    """Indicates whether the value is a Python structure."""
    return value.startswith(self.ABSOLUTE_VALUE_PREFIX)

  def _decode_structure_value(self, value):
    """Decodes a structure value."""
    return json.loads(value[len(self.ABSOLUTE_VALUE_PREFIX)+1:])

class DataType(object):
  """
  Base class for Redis data structures.
  """
  handlers = {}

  type = None
  scripts = None

  def __init__(self, redis, key=None):
    self.redis = redis
    self.key = key or self._create_unique_key()
    self.encoder = Encoder(redis)
    self.encode = self.encoder.encode
    self.decode = self.encoder.decode

    self._scripts = {}
    if self.__class__.scripts is not None:
      for id, script in self.__class__.scripts.iteritems():
        self._scripts[id] = self._load_script(id)

  @classmethod
  def register(cls, handler):
    """Registers a data type handler."""
    cls.handlers[handler.type] = handler
    return handler

  @classmethod
  def get_handler(cls, type):
    """Returns a data type handler."""
    try:
      return cls.handlers[type]
    except KeyError:
      raise DataTypeError("Invalid data type %s." % (type,))

  @classmethod
  def script(cls, script):
    """Registers a server-side Lua script."""
    try:
      cls.scripts[script.id] = script
    except TypeError:
      raise DataTypeError("Failed to register data type script.")
    return script

  @classmethod
  def get_script(cls, id):
    """Returns a script handler."""
    try:
      return cls.scripts[id]
    except KeyError:
      raise DataTypeError("Invalid script %s." % (id,))
    except TypeError:
      raise DataTypeErrpr("Failed to get script %s." % (id,))

  def __setattr__(self, name, value):
    """Allows the data type key to be changed."""
    if name == 'key' and hasattr(self, 'key'):
      self.redis.rename(self.key, value)
    object.__setattr__(self, name, value)

  def _load_script(self, id):
    """Loads a server-side Lua script."""
    return self.__class__.get_script(id)(self.redis)

  def _execute_script(self, id, *args, **kwargs):
    """Executes a server-side Lua script."""
    try:
      return self._scripts[id].execute(*args, **kwargs)
    except KeyError:
      raise DataTypeError("Invalid script %s." % (id,))

  def _create_unique_key(self):
    """Generates a unique Redis key."""
    return uuid.uuid4()

  def expire(self, expiration=None):
    """Sets the data type to expire."""
    # self.redis.pexpire(self.key, expiration)

  def persist(self):
    """Removes an expiration from the data type."""
    # self.redis.persist(self.key)

  def delete(self):
    """Deletes the data type."""
    self.redis.delete(self.key)

class Script(object):
  """
  Base class for Redis server-side lua scripts.
  """
  id = None
  is_registered = False
  script = ''
  keys = []
  args = []
  variable_keys = False
  variable_args = False

  def __init__(self, redis):
    """
    Initializes the script.
    """
    self.redis = redis

  def register(self):
    """
    Registers the script with the redis instance.
    """
    cls = self.__class__
    if not cls.is_registered:
      cls.script = self.redis.register_script(self.script)
      cls.is_registered = True

  def prepare(self, keys, args):
    """
    Sub-classes should override this to prepare arguments.
    """
    return keys, args

  def execute(self, *args, **kwargs):
    """
    Executes the script.
    """
    if not self.__class__.is_registered:
      self.register()

    current_index = 0
    keys = []
    for key in self.keys:
      try:
        keys.append(kwargs[key])
      except KeyError:
        try:
          keys.append(args[current_index])
          current_index += 1
        except IndexError:
            raise ScriptError('Invalid arguments for script %s.' % (self.id,))

    arguments = []
    for arg in self.args:
      try:
        arguments.append(kwargs[arg])
      except KeyError:
        try:
          arguments.append(args[current_index])
          current_index += 1
        except IndexError:
            raise ScriptError('Invalid arguments for script %s.' % (self.id,))

    keys, arguments = self.prepare(keys, arguments)
    return self.process(self.script(keys=keys, args=arguments, client=self.redis))

  def __call__(self, *args, **kwargs):
    """
    Executes the script.
    """
    return self.execute(*args, **kwargs)

  def process(self, value):
    """
    Sub-classes should override this to perform post-processing on return values.
    """
    return value

@DataType.register
class List(DataType):
  """
  A Redis list data type.
  """
  type = 'list'
  scripts = {}

  def __iter__(self):
    """Returns an iterator."""
    item = self.redis.lpop(self.key)
    while item is not None:
      yield self.decode(item)
      item = self.redis.lpop(self.key)

  def __len__(self):
    """Supports the len() global function."""
    return self.redis.llen(self.key)

  def __getitem__(self, key):
    """Gets a list item."""
    item = self.redis.lindex(key)
    if item is None:
      raise IndexError("Index out of range.")
    return self.decode(item)

  def __setitem__(self, key, item):
    """Sets a list item."""
    return self.redis.lset(self.key, key, self.encode(item))

  def __delitem__(self, key):
    """Deletes a list item."""
    try:
      return self._execute_script('delete', self.key, key)
    except ResponseError:
      raise IndexError("Index out of range.")

  def __contains__(self, item):
    """Supports using 'in' and 'not in' operators."""
    return self._execute_script('contains', self.key, self.encode(item))

  def append(self, item):
    """Appends an item to the list."""
    self.redis.rpush(self.key, self.encode(item))

  def extend(self, items):
    """Extends the list."""
    self.redis.rpush(*[self.encode(item) for item in items])

  def insert(self, index, item):
    """Inserts an item into the list."""
    return self.execute_script('insert', self.key, index, self.encode(item))

  def remove(self, item):
    """Removes an item from the list."""
    self.redis.lrem(self.key, self.encode(item))

  def pop(self, index=0):
    """Pops and returns an item from the list."""
    # Note that this should remove and then return the index item.
    # return self.redis.lindex(self.key, index)

  def index(self, index):
    """Returns a list item by index."""
    item = self.redis.lindex(self.key, index)
    if item is not None:
      return self.decode(item)
    else:
      raise IndexError("Index out of range.")

  def count(self, item):
    """Counts the number of occurences of an item in the list."""
    return self._execute_script('count', self.key, self.encode(item))

  def sort(self):
    """Sorts the list."""
    self.redis.sort(self.key)
    return self

  def reverse(self):
    """Reverses the list."""
    raise NotImplementedError("Reverse method not implemented.")

@List.script
class ListInsert(Script):
  """
  Handles inserting an item into a list.
  """
  id = 'insert'
  keys = ['key', 'index']
  args = ['item']

  script = """
  var key = KEYS[1]
  var index = KEYS[2]
  var item = ARGV[1]
  return redis.call('LINSERT', key, redis.call('LINDEX', key, index), item)
  """

@List.script
class ListCount(Script):
  """
  Handles counting the number of occurences of an item in a list.
  """
  id = 'count'
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

@List.script
class ListContains(Script):
  """
  Indicates whether the list contains an object.
  """
  id = 'contains'
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

@List.script
class ListDelete(Script):
  """
  Deletes an item from a list by index.
  """
  id = 'delete'
  keys = ['key']
  args = ['index']

  script = """
  local key = KEYS[1]
  local index = ARGV[1]

  local delval = '____delete____'
  redis.call('LSET', key, index, delval)
  redis.call('LREM', key, 1, delval)
  """

@DataType.register
class Hash(DataType):
  """
  A Redis hash data type.
  """
  type = 'hash'
  scripts = {}

  def clear(self):
    """Clears the hash."""
    self.redis.delete(self.key)

  def get(self, key, default=None):
    """Gets a value from the hash."""
    item = self.redis.hget(self.key, key)
    if item is not None:
      return self.decode(item)
    return default

  def has_key(self, key):
    """Indicates whether the given key exists."""
    return self.redis.hexists(self.key, key)

  def items(self):
    """Returns all hash items."""
    return [(key, self.decode(item)) for key, item in self.redis.hgetall(self.key).items()]

  def iteritems(self):
    """Returns an iterator over hash items."""
    for key in self.redis.hkeys(self.key):
      yield key, self.decode(self.redis.hget(self.key, key))

  def keys(self):
    """Returns all hash keys."""
    return self.redis.hkeys(self.key)

  def iterkeys(self):
    """Returns an iterator over hash keys."""
    return iter(self.redis.hkeys(self.key))

  def values(self):
    """Returns all hash values."""
    return [self.decode(item) for item in self.redis.hvals(self.key)]

  def itervalues(self):
    """Returns an iterator over hash values."""
    for key in self.redis.hkeys(self.key):
      yield self.decode(self.redis.hget(self.key, key))

  def pop(self, key, *args):
    """Pops a value from the dictionary."""
    item = self.redis.hget(self.key, key)
    if item is not None:
      return self.decode(item)
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
    return self.redis.hlen(self.key)

  def __iter__(self):
    """Iterates over hash keys."""
    return self.iterkeys()

  def __getitem__(self, key):
    """Gets a hash item."""
    item = self.redis.hget(self.key, key)
    if item is not None:
      return self.decode(item)
    else:
      raise KeyError("Hash key %s not found." % (key,))

  def __setitem__(self, key, item):
    """Sets a hash item."""
    return self.redis.hset(self.key, key, self.encode(item))

  def __delitem__(self, key):
    """Deletes an item from the hash."""
    return self.redis.hdel(self.key, key)

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

@DataType.register
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

@DataType.register
class SortedSet(DataType):
  """
  A Redis sorted set.
  """
  type = 'sorted_set'
  scripts = {}
