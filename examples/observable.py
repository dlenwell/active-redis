# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Active Redis support serialization and storage of complex Python
# data structures using JSON serialization. However, once an object
# is serialized any changes to that object would not normally be
# rewritten to Redis. To remedy this problem, Active Redis uses an
# observer to monitor certain objects for changes and re-serializes
# those objects when updated. Users can define custom handlers for
# observable classes to allow your objects to remain mutable.
from active_redis import Observable
from active_redis import registry

@registry.observable
class QueueObservable(Observable):
  # Indicate the class being observed.
  type = Queue

  # A list of methods to monitor for execution. When one of these
  # methods is called, the observer will be notified and the object
  # will generally be re-serialized and stored.
  watch_methods = [
    'push',
    'pop',
  ]
