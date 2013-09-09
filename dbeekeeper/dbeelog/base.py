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


class Base(object):
    """Abstract base class for distributed transaction log, or 'dbeelog'."""
    __metaclass__ = abc.ABCMeta

    def __init__(self, dbeelog_id, client_id, min_checkpoints=3):
        """Constructor

        Classes that inherit from this class must call this method from their
        constructors.

        Args:
            dbeelog_id
                A string that uniquely identifies this dbeelog within a
                dbeekeeper instance.

            client_id:
                A string that uniquely identifies the client within this
                dbeelog. The caller is responsible for ensuring the uniqueness.

            min_checkpoints:
                Minimum number of checkpoints before dbeelog can truncate a
                transaction.

                Dbeelog must not truncate a transaction if it hasn't been
                checkpointed by $min_checkpoints clients. Clients are
                identified by client_id passed to the constructor.

                Dbeelog must retain at least $min_checkpoints most recent
                checkpoints. For example, say min_checkpoints is set to 3, and
                5 clients have called the checkpoint() methods:

                    client1 => transaction5
                    client2 => transaction1
                    client3 => transaction3
                    client4 => transaction6
                    client5 => transaction4

                Then the get_checkpoints() should contain at least these 3
                checkpoints:

                    client1 => transaction5
                    client4 => transaction6
                    client5 => transaction4
        """
        self._dbeelog_id = dbeelog_id
        self._client_id = client_id
        self._min_checkpoints = min_checkpoints

    @property
    def dbeelog_id(self):
        return self._dbeelog_id

    @property
    def client_id(self):
        return self._client_id

    @property
    def min_checkpoints(self):
        return self._min_checkpoints

    @abc.abstractmethod
    def append(self, transaction, callback):
        """Append a dbee transaction to this log.

        Args:
            transaction: transaction to append in string.
            callback: Callback to invoke when the operation finishes. This
                      function must take 2 arguments, error and transactionid.
                      If the operation succeeded, the first argument is set to
                      None and second argument is a string that contains the ID
                      for the transaction that got appended to the log. If the
                      operation failed, the first argument is an Exception that
                      explains why the operation failed, and the second
                      argument is set to None.

        Returns:
            None

        Raises:
            This method must not raise any dbeekeeper error. All the dbeekeeper
            errors must be passed in the callback
        """

    @abc.abstractmethod
    def subscribe(self, from_transaction_id, receive_func):
        """Subscribe to this dbeelog for new entries.

        Dbeelog calls the callback once for each new transaction. For any given
        client, its callback must be invoked from a single thread in the same
        order these transactions got appended.

        If a same client calls the subscribe() method multiple times, only the
        last subscription will be valid.

        Args:
            from_transaction_id:
                Start receiving transactions from this transaction id. Pass an
                empty string to start from the end of the log.

            receive_func:
                Function to receive a new transaction. The function must take 3
                arguments:
                1. error - If not None, the subscription is no longer valid.
                   You won't receive any more transactions.
                2. transaction_id
                3. client_id - client that appended this transaction.
                4. transaction

        Returns:
            True if successful. False otherwise.

        Raises:
            dbeekeeper.ClientError
            dbeekeeper.DbeeLogError
        """

    @abc.abstractmethod
    def checkpoint(self, transaction_id, callback):
        """Checkpoint this log.

        Call this method to notify dbeelog that you have persisted all the
        transactions up to and including the given transaction ID to disk.

        Args:
            transaction_id:
                Specify that the caller has persisted all the transactions up
                to and including this transaction to disk.

            callback:
                Callback to invoke when the operation finishes. This function
                must take 2 arguments, error and a transaction_id. If the
                operation succeeded, the first argument is set to None and
                second argument is a transaction_id that was passed to the
                checkpoint() method. If the operation failed, the first
                argument is an Exception that explains why the operation
                failed, and the second argument is set to None.

        Returns:
            None

        Raises:
            This method must not raise any dbeekeeper error. All the dbeekeeper
            errors must be passed in the callback
        """

    @abc.abstractmethod
    def get_checkpoints(self, callback):
        """Get current checkpoints as a map from client_id to transaction_id.

        Args:
            callback: Callback to invoke when the operation finishes. This
                      function must take 2 arguments, error and a map. If the
                      operation succeeded, the first argument is set to
                      None and second argument is a map from client id to
                      transaction id. If the operation failed, the first
                      argument is an Exception that explains why the operation
                      failed, and the second argument is set to None.

        Returns:
            None

        Raises:
            This method must not raise any dbeekeeper error. All the dbeekeeper
            errors must be passed in the callback
        """
