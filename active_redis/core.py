# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
from redis import Redis
from registry import DataType as DataTypeRegistry
from registry import Observable as ObservableRegistry
from exception import *
import uuid, json

class ActiveRedis(object):
  """
  Active Redis client.
  """
  def __init__(self, *args, **kwargs):
    """Initializes the client.

    The constructor accepts either a Redis instance or arguments
    required to construct a Redis instance.
    """
    if len(args) == 0 and len(kwargs) == 0:
      if len(self.default_config) == 0:
        self.client = Redis()
      else:
        try:
          self.default_config[1]
          self.client = Redis(*self.default_config[0], **self.default_config[1])
        except IndexError:
          if isinstance(self.default_config[0], dict):
            self.client = Redis(**self.default_config[0])
          else:
            self.client = Redis(*self.default_config[0])
    else:
      try:
        if isinstance(args[0], Redis):
          self.client = args[0]
        else:
          self.client = Redis(*args, **kwargs)
      except IndexError:
        self.client = Redis(*args, **kwargs)

  @staticmethod
  def _create_unique_key():
    """Generates a unique Redis key using UUID."""
    return uuid.uuid4()

  def _wrap_datatype(self, datatype):
    """Wraps a datatype constructor."""
    def create_datatype(key=None):
      return datatype(key or ActiveRedis._create_unique_key(), ActiveRedisClient(self.client))
    return create_datatype

  def __getattr__(self, name):
    if DataType.exists(name):
      return self._wrap_datatype(DataType.get(name))
    else:
      raise AttributeError("Attribute %s not found." % (name,))

class ActiveRedisClient(object):
  """
  Handles encoding and decoding of objects.
  """
  REDIS_STRUCTURE_PREFIX = 'redis:struct'
  ABSOLUTE_VALUE_PREFIX = 'redis:absolute'

  def __init__(self, redis):
    self.redis = redis

  def __getattr__(self, name):
    return getattr(self.redis, name)

  def encode(self, item):
    """Encodes a Python object."""
    if isinstance(item, Notifier):
      item = item.observable.subject
    if self._is_redis_item(item):
      return self._encode_redis_item(item)
    else:
      return self._encode_structure_item(item)

  def _is_redis_item(self, item):
    """Indicaites whether the item is a Redis data type."""
    return isinstance(item, DataType)

  def _encode_redis_item(self, item):
    """Encodes a Redis data type."""
    return "%s:%s:%s" % (self.REDIS_STRUCTURE_PREFIX, item.type, item.key)

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
    type, key = value[len(self.REDIS_STRUCTURE_PREFIX)+1:].split(':', 1)
    return DataType.get(type)(key, self)

  def _is_structure_value(self, value):
    """Indicates whether the value is a Python structure."""
    return value.startswith(self.ABSOLUTE_VALUE_PREFIX)

  def _decode_structure_value(self, value):
    """Decodes a structure value."""
    return json.loads(value[len(self.ABSOLUTE_VALUE_PREFIX)+1:])

class DataType(object):
  """
  Abstract data type class.
  """
  _registry = DataTypeRegistry
  _scripts = {}

  def __init__(self, key, client):
    self.key = key
    self.client = client

  @classmethod
  def exists(cls, type):
    """Indicates whether a data type handler exists."""
    return cls._registry.exists(type)

  @classmethod
  def get(cls, type):
    """Returns a data type handler."""
    return cls._registry.get(type)

  def __setattr__(self, name, value):
    """Allows the data type key to be changed."""
    if name == 'key' and hasattr(self, 'key'):
      self.client.rename(self.key, value)
    object.__setattr__(self, name, value)

  def _load_script(self, script):
    """Loads a script handler."""
    try:
      return self._scripts[script](self.client)
    except KeyError:
      raise ScriptError("Invalid script %s." % (script,))

  def _execute_script(self, script, *args, **kwargs):
    """Executes a script."""
    return self._load_script(script)(*args, **kwargs)

  def delete(self):
    """Deletes the data type."""
    raise NotImplementedError("Data types must implement the delete() method.")

class Observer(object):
  """
  Abstract base class for notifiable data types.

  This class should be extended by data types using multiple
  inheritence. Observables can be created using the self.observe(subject)
  method. This allows standard Python data structures such as lists,
  sets, and any other data type to be observed for changes.

  Observable handlers must be registered in the Active Redis
  registry. See the Observable class for more.
  """
  def observe(self, subject, *args, **kwargs):
    """Creates an observer for the given subject."""
    if Observable.is_observable(subject):
      return Notifier(Observable.get_observable(subject)(subject, *args, **kwargs), self)
    else:
      return subject

  def notify(self, subject, *args, **kwargs):
    """Notifies the data type of a change in an observable."""
    raise NotImplementedError("Notifiable data types must implement the notify() method.")

class Notifier(object):
  """
  Monitors an observable object and notifies the observer when
  an observable method is called.
  """
  def __init__(self, observable, observer):
    self.observable = observable
    self.observer = observer

  def _wrap_method(self, name):
    def execute_method(*args, **kwargs):
      retval = getattr(self.observable, name)(*args, **kwargs)
      self.observer.notify(self.observable.subject, *self.observable.args, **self.observable.kwargs)
      return retval
    return execute_method

  def __getattr__(self, name):
    """Checks for a method that needs to be wrapped."""
    if name in self.observable.watch_methods and hasattr(self.observable, name) and callable(getattr(self.observable, name)):
      return self._wrap_method(name)
    elif hasattr(self.observable, name):
      return getattr(self.observable, name)
    else:
      raise AttributeError("Attribute %s not found." % (name,))

  def __repr__(self):
    return repr(self.subject)

class Observable(object):
  """
  Wrapper for observable objects.
  """
  _registry = ObservableRegistry

  type = None
  watch_methods = []

  def __init__(self, subject, *args, **kwargs):
    self.subject = subject
    self.args = args
    self.kwargs = kwargs

  def __getattr__(self, name):
    return getattr(self.subject, name)

  @classmethod
  def is_observable(cls, type):
    """Indicates whether the given type is observable."""
    return cls._registry.is_observable(type)

  @classmethod
  def get_observable(cls, type):
    """Returns an observable handler for a data type."""
    return cls._registry.get(type)

class Script(object):
  """
  Base class for Redis server-side lua scripts.
  """
  is_registered = False
  script = ''
  keys = []
  args = []
  variable_keys = False
  variable_args = False

  def __init__(self, client):
    """
    Initializes the script.
    """
    self.client = client

  def register(self):
    """
    Registers the script with the redis instance.
    """
    if not self.__class__.is_registered:
      self.__class__.script = self.client.register_script(self.script)
      self.__class__.is_registered = True

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
    return self.process(self.script(keys=keys, args=arguments, client=self.client))

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
