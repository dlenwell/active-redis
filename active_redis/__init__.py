from active_redis.core import (
  ActiveRedis,
  DataType,
  Script,
)
import active_redis.observables

import sys, pkgutil
import active_redis.datatypes

prefix = active_redis.datatypes.__name__ + '.'
for importer, module_name, _ in pkgutil.iter_modules(active_redis.datatypes.__path__, prefix):
  full_name = '%s.%s' % (active_redis.datatypes, module_name)
  if full_name not in sys.modules:
    __import__(module_name)
