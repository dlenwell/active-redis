import sys, os, unittest

from tests.active_redis import (
  ActiveRedisTestCase,
)

from tests.datatype import (
  ListTestCase,
  HashTestCase,
  SetTestCase,
  SortedSetTestCase,
)

def all_tests():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(ActiveRedisTestCase))
  suite.addTest(unittest.makeSuite(ListTestCase))
  suite.addTest(unittest.makeSuite(HashTestCase))
  suite.addTest(unittest.makeSuite(SetTestCase))
  suite.addTest(unittest.makeSuite(SortedSetTestCase))
  return suite
