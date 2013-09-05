# Copyright 2013 VMware, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import abc


class Base(Exception):
    """Abstract base class for dbeekeeper local storage, or 'dbee'.

    A dbee instance must be accessed from a single thread.

    Dbee transactions must be idempotent. Much like ZooKeeper snapshots, dbee
    snapshots are 'fuzzy', meaning that transactions that were executed during
    snapshotting may or may not be included in the snapshot. During recovery,
    dbeekeeper executes all the transactions since the beginning of the
    snapshot it's recoverying from in the same order they were applied
    originally.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def execute(self, transaction):
        """Execute a transaction.

        This method is *not* responsible for persisting transaction to disk.
        The caller must maintain a transaction log until it takes a snapshot.

        Args:
            transaction: transaction to execute in string.

        Returns:
            None

        Raises:
            dbeekeeper.DbeeError:
                DbeeError is considered fatal since it might affet consistency
                of dbee. When dbee throws a DbeeError, dbeekeeper goes into
                recovery mode.
            dbeekeeper.ClientError:
                ClientError is *not* considered fatal since it does not affect
                consistency of dbee. Dbeekeeper simply pass ClientErrors back
                to the client.
        """

    @abc.abstractmethod
    def snapshot(self, filename, callback):
        """Take a snapshot of this dbee asynchronously.

        This method must not block. It should initiate snapshotting in a
        separate thread/process and return without waiting for the snapshotting
        to finish. Dbee must reject any other incoming snapshot/restore
        requests during the snapshot by raising a ClientError.

        The resulting snapshot must contain all the transactions this dbee
        successfully executed before the snapshot() was called. For incoming
        execute requests during the snapshot, dbee must either:

        a. Block them until the snapshotting finishes.
        b. Accept the transactions. These transactions may or may not be in the
           resulting snapshot. It is the caller's responsibility to maintain
           a log for these transactions until the next snapshot() call finishes
           successfully.

        Args:
            filename: filename to use for the snapshot.
            callback: function to call when the snapshotting completes. This
                      function must take 2 arguemnts, error and filename. If
                      snapshotting succeeded, the first argument is set to None
                      and the second argument is a string that contains
                      filename of the resulting snapshot. If snapshotting
                      failed, the first argument is an Exception and the second
                      argument is set to None.

        Returns:
            None

        Raises:
            This method must not raise any dbeekeeper error. All the dbeekeeper
            errors must be passed in the callback
        """

    @abc.abstractmethod
    def restore(self, filename):
        """Restore dbee from a snapshot.

        This method must block until the restore operation completes.

        Args:
            filename: Snapshot file to restore from.

        Returns:
            None

        Raises:
            dbeekeeper.DbeeError:
        """
