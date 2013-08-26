#!/usr/bin/env python

import datetime
import time
import os
import sys
from optparse import OptionParser
from kazoo.client import KazooClient


class Operation():
    create = "create"
    get = "get"
    set = "set"
    delete = "delete"
    NOT_SUPPORT_MSG = "NOT SUPPORTED"


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
def do_operation(op, s, root, async, batch_size, count,
                 ephemeral=True, data=None):
    if not batch_size:
        async_results = []
        for i in range(count):
            if async:
                if op == Operation.create:
                    r = s.create_async(child_path(root, i), data,
                                       ephemeral=ephemeral)
                elif op == Operation.get:
                    r = s.get_async(child_path(root, i))
                elif op == Operation.set:
                    r = s.set_async(child_path(root, i), data)
                elif op == Operation.delete:
                    r = s.delete_async(child_path(root, i))
                async_results.append(r)
            else:
                if op == Operation.create:
                    s.create(child_path(root, i), data, ephemeral=ephemeral)
                elif op == Operation.get:
                    s.get(child_path(root, i))
                elif op == Operation.set:
                    s.set(child_path(root, i), data)
                elif op == Operation.delete:
                    s.delete(child_path(root, i))
        for r in async_results:
            # is this the right way to know an async request is complete?
            r.get()
    else:
        batches = (count - 1) / batch_size + 1
        async_results = []
        for i in range(batches):
            t = s.transaction()
            end = batch_size * (i + 1) if i < (batches - 1) else count
            for j in range(batch_size * i, end):
                if op == Operation.create:
                    t.create(child_path(root, j), data, ephemeral=ephemeral)
                elif op == Operation.get:
                    # no get operation in batch transaction
                    return "%5s %6s %8d %10s znodes batch size %5d  %s" % \
                           ("async" if async else "sync", op, count, "",
                            batch_size, Operation.NOT_SUPPORT_MSG)
                elif op == Operation.set:
                    t.set_data(child_path(root, j), data)
                elif op == Operation.delete:
                    t.delete(child_path(root, j))
            if async:
                r = t.commit_async()
                async_results.append(r)
            else:
                t.commit()
        for r in async_results:
            # is this the right way to know an async request is complete?
            r.get()

    # only print node type for creation operation
    node_type = ""
    if op == Operation.create:
        node_type = "ephemeral" if ephemeral else "permanent"

    return "%5s %6s %8d %10s znodes batch size %5d " % \
           ("async" if async else "sync", op, count, node_type, batch_size)


def evaluation(s, root, data, options):
    # create znodes (permanent)
    do_operation(Operation.create, s, root, options.async, options.batch_size,
                 count=options.count, ephemeral=False, data=data)

    # set znodes
    do_operation(Operation.set, s, root, options.async,
                 options.batch_size, count=options.count, data=data)

    # get znodes
    do_operation(Operation.get, s, root, options.async,
                 options.batch_size, count=options.count)

    # delete znodes
    do_operation(Operation.delete, s, root, options.async,
                 options.batch_size, count=options.count)

    # create znodes (ephemeral)
    do_operation(Operation.create, s, root, options.async, options.batch_size,
                 count=options.count, data=data)

    # set znodes
    do_operation(Operation.set, s, root, options.async,
                 options.batch_size, count=options.count, data=data)

    # get znodes
    do_operation(Operation.get, s, root, options.async,
                 options.batch_size, count=options.count)

    # delete znodes
    do_operation(Operation.delete, s, root, options.async,
                 options.batch_size, count=options.count)


def parse_options(args):
    parser = OptionParser(usage="usage: %prog [options]")
    parser.add_option("", "--server", dest="server", default="localhost:2181",
                      help="zookeeper server (default %default)")
    parser.add_option("", "--root_znode", dest="root_znode",
                      default="/zk-benchmark-kazoo",
                      help="root znode for the evaluation")
    parser.add_option("", "--znode_data_size", dest="znode_data_size",
                      type="int", default=20,
                      help="data size for each znode (default %default)")
    parser.add_option("", "--count", dest="count",
                      type="int", default=10000,
                      help="the number of znodes in each test run")
    parser.add_option("", "--batch_size", dest="batch_size",
                      type="int", default=0,
                      help="number of operations in each transaction "
                           "(default %default means no batch operation)")
    parser.add_option("", "--sync",
                      action="store_false", dest="async", default=True,
                      help="using synchronous api")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="verbose logging")
    return parser.parse_args(args)


def main():
    (options, args) = parse_options(sys.argv[1:])

    data = options.znode_data_size * "D"

    s = KazooClient(options.server)
    s.start()

    if s.exists(options.root_znode):
        children = s.get_children(options.root_znode)
        print "delete old entries: %d" % len(children)
        for child in children:
            s.delete("%s/%s" % (options.root_znode, child))
    else:
        s.create(options.root_znode, "kazoo root znode")

    evaluation(s, options.root_znode, data, options)

    s.stop()

    print("Performance test complete")

if __name__ == "__main__":
    sys.exit(main())
