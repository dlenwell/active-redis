
class ActiveRedisError(Exception):
  """
  Base class for Active Redis exceptions.
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
