import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from active_redis import ActiveRedis
from redis import Redis

aredis = ActiveRedis(Redis())

mylist = aredis.list('foo')
mylist.append('foo')
mylist.append('bar')
mylist[1] = 'baz'

otherlist = aredis.list()
otherlist.append('bank')
otherlist.append('money!')
print 'money!' in otherlist
del otherlist[1]
print 'money!' in otherlist

mylist.append(otherlist)
mylist.delete()