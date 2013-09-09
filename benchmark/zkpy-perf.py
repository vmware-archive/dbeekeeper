#!/usr/bin/env python

import time
import sys
import zookeeper
import threading
from optparse import OptionParser

parser = OptionParser(usage="usage: %prog [options]")
parser.add_option("", "--server", dest="server", default="localhost:2181",
                  help="zookeeper server (default %default)")
parser.add_option("", "--root_znode", dest="root_znode",
                  default="/zk-benchmark-zkpy",
                  help="root znode for the evaluation")
parser.add_option("", "--znode_data_size", dest="znode_data_size",
                  type="int", default=20,
                  help="data size for each znode (default %default)")
parser.add_option("", "--count", dest="count",
                  type="int", default=10000,
                  help="the number of znodes in each test run")
parser.add_option("", "--sync",
                  action="store_false", dest="async", default=True,
                  help="using synchronous api")
parser.add_option("-v", "--verbose",
                  action="store_true", dest="verbose", default=False,
                  help="verbose logging")
parser.add_option("-q", "--quiet",
                  action="store_true", dest="quiet", default=False,
                  help="quiet output, basically just success/failure")
(options, args) = parser.parse_args()


acl = [{"perms": 0x1f, "scheme": "world", "id": "anyone"}]


class Operation():
    create = "create"
    get = "get"
    set = "set"
    delete = "delete"
    NOT_SUPPORT_MSG = "NOT SUPPORTED"


class Callback(object):

    def __init__(self):
        self.cv = threading.Condition()
        self.callback_flag = False
        self.rc = -1
        self.cv.acquire()

    def callback(self, rc):
        self.cv.acquire()
        self.callback_flag = True
        self.rc = rc
        self.cv.notify()
        self.cv.release()

    def wait(self):
        while not self.callback_flag:
            self.cv.wait()
        self.cv.release()

        if self.callback_flag is not True:
            sys.stderr.write("callback timeout")
        if not self.rc == zookeeper.OK:
            sys.stderr.write("async call failed with error code %d" % self.rc)


class GetCallback(Callback):

    def __call__(self, handle, rc, value, stat):
        self.callback(rc)


class SetCallback(Callback):

    def __call__(self, handle, rc, stat):
        self.callback(rc)


class CreateCallback(Callback):

    def __call__(self, handle, rc, path):
        self.callback(rc)


class DeleteCallback(Callback):

    def __call__(self, handle, rc):
        self.callback(rc)


def timed(f):
    def wrapper(*args, **kwargs):
        start = time.time()
        msg = f(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        if msg.find(Operation.NOT_SUPPORT_MSG) != -1:
            print "%s" % msg
        else:
            print "%s took %8d ms (%5d/sec)" % \
                  (msg, int(elapsed), kwargs["count"] / (elapsed / 1000))
    return wrapper


def child_path(root, i):
    return "%s/session_%d" % (root, i)


@timed
def do_operation(op, s, root, async, count, ephemeral=True, data=None):
    async_results = []
    for i in range(count):
        path = child_path(root, i)
        if async:
            if op == Operation.create:
                cb = CreateCallback()
                zookeeper.acreate(s, path, data, acl,
                                  zookeeper.EPHEMERAL if ephemeral else 0, cb)
            elif op == Operation.get:
                cb = GetCallback()
                zookeeper.aget(s, path, None, cb)
            elif op == Operation.set:
                cb = SetCallback()
                zookeeper.aset(s, path, data, -1, cb)
            elif op == Operation.delete:
                cb = DeleteCallback()
                zookeeper.adelete(s, path, -1, cb)
            async_results.append(cb)
        else:
            if op == Operation.create:
                zookeeper.create(s, path, data, acl,
                                 zookeeper.EPHEMERAL if ephemeral else 0)
            elif op == Operation.get:
                zookeeper.get(s, path)
            elif op == Operation.set:
                zookeeper.set(s, path, data)
            elif op == Operation.delete:
                zookeeper.delete(s, path)

    for cb in async_results:
        cb.wait()

    # only print node type for creation operation
    node_type = ""
    if op == Operation.create:
        node_type = "ephemeral" if ephemeral else "permanent"

    return "%5s %6s %8d %10s znodes " % \
           ("async" if async else "sync", op, count, node_type)


def evaluation(s, root, data, options):
    # create znodes (permanent)
    do_operation(Operation.create, s, root, options.async,
                 count=options.count, ephemeral=False, data=data)

    # set znodes
    do_operation(Operation.set, s, root, options.async,
                 count=options.count, data=data)

    # get znodes
    do_operation(Operation.get, s, root, options.async, count=options.count)

    # delete znodes
    do_operation(Operation.delete, s, root, options.async, count=options.count)

    # create znodes (ephemeral)
    do_operation(Operation.create, s, root, options.async,
                 count=options.count, data=data)

    # set znodes
    do_operation(Operation.set, s, root, options.async,
                 count=options.count, data=data)

    # get znodes
    do_operation(Operation.get, s, root, options.async, count=options.count)

    # delete znodes
    do_operation(Operation.delete, s, root, options.async, count=options.count)


def main():
    data = options.znode_data_size * "D"

    zookeeper.set_debug_level(zookeeper.LOG_LEVEL_WARN)
    s = zookeeper.init(options.server)

    if zookeeper.exists(s, options.root_znode, None):
        children = zookeeper.get_children(s, options.root_znode, None)
        print "delete old entries: %d" % len(children)
        for child in children:
            zookeeper.delete(s, "%s/%s" % (options.root_znode, child))
    else:
        zookeeper.create(s, options.root_znode, "zkpy root znode", acl, 0)

    evaluation(s, options.root_znode, data, options)

    zookeeper.close(s)

    print("Performance test complete")

if __name__ == "__main__":
    sys.exit(main())
