# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
from exception import RegistryError
import inspect

class Registry(object):
  """
  Abstract registry.
  """
  @classmethod
  def register(cls, handler):
    """Registers a handler."""
    cls._handlers[handler.type] = handler
    return handler

  @classmethod
  def unregister(cls, handler):
    """Unregisters a handler."""
    try:
      del cls._handlers[handler.type]
    except KeyError:
      pass

  @classmethod
  def exists(cls, type):
    """Returns a value indicating whether a handler type exists."""
    try:
      cls._handlers[type]
    except KeyError:
      return False
    else:
      return True

  @classmethod
  def get(cls, type):
    """Gets a registered handler."""
    if not cls.exists(type):
      raise RegistryError("Invalid handler type %s." % (type,))
    else:
      return cls._handlers[type]

class DataType(Registry):
  """
  Data type registry.
  """
  _handlers = {}

class Observable(Registry):
  """
  Observable registry.
  """
  _handlers = {}

  @classmethod
  def is_observable(cls, type):
    if not inspect.isclass(type):
      type = type.__class__
    return cls.exists(type)

  @classmethod
  def get(cls, type):
    if not inspect.isclass(type):
      type = type.__class__
    if not cls.exists(type):
      raise RegistryError("Invalid handler type %s." % (type,))
    else:
      return cls._handlers[type]
