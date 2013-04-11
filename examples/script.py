# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# The Active Redis API provides native support for Redis server-side
# Lua scripting.
from active_redis import Script

class PushMany(Script):
  """
  Push several items on to a queue.
  """
  # Define keyword argument names for keys used by the script.
  keys = ['key']

  # Define keyword argument names for all other arguments to the script.
  args = []

  # In this case, we're using a variable number of arguments. Note that
  # when variable arguments are used, only the last defined argument
  # may have a variable number.
  variable_args = True

  # Finally, define the Lua script. This is just a simple example.
  script = """
  local key = KEYS[1]
  local vals = ARGV
  redis.call('RPUSH', key, unpack(vals))
  """

# Building upon the datatype example, we can extend the Queue class
# and make use of our script.
from datatype import Queue
from active_redis import registry

@registry.datatype
class BetterQueue(Queue):
  """A better version of our queue."""
  type = 'better_queue'

  _scripts = {
    'pushmany': PushMany,
  }

  def push_many(self, *args):
    """Pushes many items on to the queue."""
    return self._execute_script('pushmany', self.key, *args)
