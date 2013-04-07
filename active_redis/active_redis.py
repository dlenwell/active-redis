
def defaultConfig(*args, **kwargs):
  """Sets the default Redis client configuration."""

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
