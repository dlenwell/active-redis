from redis import Redis
from .datatype import DataType

def defaultConfig(*args, **kwargs):
  """Sets the default Redis client configuration."""
  ActiveRedis.default_config = (args, kwargs)

class ActiveRedis(object):
  """
  Core class for interacting with Redis via ActiveRedis.
  """
  default_config = tuple()

  def __init__(self, *args, **kwargs):
    if len(args) == 0 and len(kwargs) == 0:
      if len(self.default_config) == 0:
        self.redis = Redis()
      else:
        try:
          self.default_config[1]
          self.redis = Redis(*self.default_config[0], **self.default_config[1])
        except IndexError:
          if isinstance(self.default_config[0], dict):
            self.redis = Redis(**self.default_config[0])
          else:
            self.redis = Redis(*self.default_config[0])
    else:
      try:
        if isinstance(args[0], Redis):
          self.redis = args[0]
        else:
          self.redis = Redis(*args, **kwargs)
      except IndexError:
        self.redis = Redis(*args, **kwargs)

  def create_datatype(self, type, key=None):
    """Creates a Redis data type."""
    return DataType.get_handler(type)(self.redis, key)

  def __getattr__(self, name):
    """Allows creating data types via type names."""
    try:
      DataType.get_handler(name)
    except ActiveRedisError:
      raise AttributeError("Attribute %s not found." % (name,))
    else:
      def create_it(key=None):
        return self.create_datatype(name, key)
      return create_it
