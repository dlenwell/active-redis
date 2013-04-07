from redis import Redis
import uuid

def defaultConfig(*args, **kwargs):
  """Sets the default Redis client configuration."""
  ActiveRedis.default_config = (args, kwargs)

class ActiveRedis(object):
  """
  Core class for interacting with Redis via ActiveRedis.
  """
  def __init__(self, *args, **kwargs):
    try:
      if isinstance(args[0], Redis):
        self.redis = args[0]
      else:
        self.redis = Redis(*args, **kwargs)
    except IndexError:
      self.redis = Redis(*args, **kwargs)

  def _create_datatype(self, type, key=None):
    """Creates a Redis data type."""
    return DataType.load(type, self.redis, key)

  def string(self, key=None):
    """Returns a new Redis string."""
    return self._create_datatype('string', key)

  def list(self, key=None):
    """Returns a new Redis list."""
    return self._create_datatype('list', key)

  def set(self, key=None):
    """Returns a new Redis set."""
    return self._create_datatype('set', key)

  def sorted_set(self, key=None):
    """Returns a new Redis sorted set."""
    return self._create_datatype('sorted_set', key)

  def hash(self, key=None):
    """Returns a new Redis hash."""
    return self._create_datatype('hash', key)

class DataType(object):
  """
  Base class for Redis data structures.
  """
  def __init__(self, redis, key=None):
    self.redis = redis
    self.encoder = Encoder(redis)
    self.key = key or self._create_unique_key()

  def _create_unique_key(self):
    """Generates a unique Redis key."""
    return uuid.uuid4()

  @classmethod
  def script(cls, script):
    """Registers a server-side Lua script."""
    cls.scripts[script.id] = script
    return script

  def expire(self, expiration=None):
    """Sets the data type to expire."""
    self.redis.pexpire(self.key, expiration)

  def persist(self):
    """Removes an expiration from the data type."""
    self.redis.persist(self.key)

  def rename(self, key=None):
    """Renames the key."""
    oldkey = self.key
    self.key = key or self._create_unique_key()
    self.redis.rename(oldkey, self.key)
    return self.key

  def delete(self):
    """Deletes the data type."""
    self.redis.delete(self.key)

class Encoder(object):
  """
  Handles encoding and decoding of objects.
  """
  REDIS_STRUCTURE_PREFIX = 'redis:struct'
  ABSOLUTE_VALUE_PREFIX = 'redis:abs'

  def __init__(self, redis):
    self.redis = redis

  def encode(self, item):
    if self._is_redis(item):
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
      raise EncoderError("Failed to decode value. Unknown data type.")

  def _is_redis_value(self, value):
    """Indicates whether the value is a Redis data type."""
    return value.startswith(self.REDIS_STRUCTURE_PREFIX)

  def _decode_redis_value(self, value):
    """Decodes a Redis data type value."""
    prefix, key = value.split(':', 1)
    type = self.redis.type(key)
    if type is None:
      raise EncoderError("Failed to decode value. Key %s does not exist.")
    return self.create_datatype(type, key)

  def _is_structure_value(self, value):
    """Indicates whether the value is a Python structure."""
    return value.startswith(self.ABSOLUTE_VALUE_PREFIX)

  def _decode_structure_value(self, value):
    """Decodes a structure value."""
    return json.loads(value[len(self.ABSOLUTE_VALUE_PREFIX)+1:])
