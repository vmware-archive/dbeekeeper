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


class ClientError(Exception):
    """dbeekeeper client error.

    Dbeekeeper raises a ClientError when it encounters a client-side errors.
    Examples of client-side errors are:

    - Trying to delete a non-existent record.
    - Foreign key constraint error.
    - Malformed transaction.

    Client-side errors are *not* considered fatal since they do not affect the
    consistency of dbee.
    """


class DbeeError(Exception):
    """dbee error.

    Dbee raises a DbeeError when it encounters a dbee-side errors. Examples of
    dbee-side errors are:

    - Underlying storage server is down.
    - Failed to write a record to disk because it was full.
    - Out of memory.

    Dbee-side errors *are* considered fatal since they might affect the
    consistency of dbee. When a dbee throws a DbeeError, dbeekeeper
    goes into recovery.
    """
