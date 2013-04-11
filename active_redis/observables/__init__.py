# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
from active_redis.core import Observable
from active_redis.registry import Observable as Registry

@Registry.register
class List(Observable):
  """List observable."""
  type = list
  watch_methods = [
    '__setitem__',
    'append',
    'extend',
    'insert',
    'remove',
    'pop',
  ]

@Registry.register
class Dict(Observable):
  """Dictionary observable."""
  type = dict
  watch_methods = [
    '__setitem__',
  ]
