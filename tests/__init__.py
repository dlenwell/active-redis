# Copyright (c) 2013 Jordan Halterman <jordan.halterman@gmail.com>
# See LICENSE for details.
import sys, os, unittest

from tests.core import (
  ActiveRedisTestCase,
  ActiveRedisClientTestCase,
  DataTypeTestCase,
  ObserverTestCase,
  NotifierTestCase,
  ObservableTestCase,
  ScriptTestCase,
)

from tests.registry import (
  RegistryTestCase,
  DataType as DataTypeRegistryTestCase,
  Observable as ObservableRegistryTestCase,
)

from tests.datatypes.list import ListTestCase
from tests.datatypes.dict import DictTestCase
from tests.datatypes.set import SetTestCase

def all_tests():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(ActiveRedisTestCase))
  suite.addTest(unittest.makeSuite(ActiveRedisClientTestCase))
  suite.addTest(unittest.makeSuite(DataTypeTestCase))
  suite.addTest(unittest.makeSuite(ObserverTestCase))
  suite.addTest(unittest.makeSuite(NotifierTestCase))
  suite.addTest(unittest.makeSuite(ObservableTestCase))
  suite.addTest(unittest.makeSuite(ScriptTestCase))

  suite.addTest(unittest.makeSuite(RegistryTestCase))
  suite.addTest(unittest.makeSuite(DataTypeRegistryTestCase))
  suite.addTest(unittest.makeSuite(ObservableRegistryTestCase))

  suite.addTest(unittest.makeSuite(ListTestCase))
  suite.addTest(unittest.makeSuite(DictTestCase))
  suite.addTest(unittest.makeSuite(SetTestCase))
  return suite
