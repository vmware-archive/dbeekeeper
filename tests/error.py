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


import dbeekeeper
import unittest


class Error(unittest.TestCase):
    """Import, raise, and catch dbeekeeper errors.

    All the errors should be top-level classes directly under dbeekeeper.
    """

    def raise_clienterror(self):
        raise dbeekeeper.ClientError("client error")

    def raise_dbeeerror(self):
        raise dbeekeeper.DbeeError("dbee error")

    def test_clienterror(self):
        with self.assertRaises(dbeekeeper.ClientError):
            self.raise_clienterror()

    def test_servererror(self):
        with self.assertRaises(dbeekeeper.DbeeError):
            self.raise_dbeeerror()
