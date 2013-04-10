
class Wrapper(object):
  """
  Wraps and monitors a Python object.
  """
  wrappers = {}
  watch_methods = []

  def __init__(self, subject, index, parent):
    self.subject = subject
    self.index = index
    self.parent = parent

  @classmethod
  def register(cls, wrapper):
    cls.wrappers[wrapper.cls] = wrapper
    return wrapper

  @classmethod
  def wrap(cls, subject, index, parent):
    """Wraps a subject."""
    try:
      cls.wrappers[subject.__class__]
    except KeyError:
      return subject
    else:
      return cls.wrappers[subject.__class__](subject, index, parent)

  def wrap_method(self, name):
    """Wraps a subject method."""
    def execute_method(*args, **kwargs):
      retval = getattr(self.subject, name)(*args, **kwargs)
      self.parent.update_subject(self.subject, self.index)
      return retval
    return execute_method

  def __getattr__(self, name):
    """Checks for a method that needs to be wrapped."""
    if name in self.watch_methods:
      return self.wrap_method(name)
    elif hasattr(self.subject, name):
      return getattr(self.subject, name)
    else:
      raise AttributeError("Attribute %s not found." % (name,))

  def __repr__(self):
    return repr(self.subject)

@Wrapper.register
class ListWrapper(Wrapper):
  """
  A list wrapper.
  """
  cls = list

  watch_methods = [
    '__setitem__',
    'append',
    'extend',
    'insert',
    'remove',
    'pop',
  ]

@Wrapper.register
class DictWrapper(Wrapper):
  """
  A hash wrapper.
  """
  cls = dict

  watch_methods = [
    '__setitem__',
  ]
