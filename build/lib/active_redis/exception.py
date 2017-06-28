# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
__all__ = [
  'ActiveRedisError',
  'RegistryError',
  'EncodingError',
  'DataTypeError',
  'ScriptError',
]

class ActiveRedisError(Exception):
  """
  Base class for Active Redis exceptions.
  """

class RegistryError(ActiveRedisError):
  """
  Registry error.
  """

class EncodingError(ActiveRedisError):
  """
  Encoder/decoder error.
  """

class DataTypeError(ActiveRedisError):
  """
  Generic data type error.
  """

class ScriptError(ActiveRedisError):
  """
  Script error.
  """
