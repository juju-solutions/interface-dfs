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

import json

from charms.reactive import RelationBase
from charms.reactive import hook
from charms.reactive import scopes


class HDFSRequires(RelationBase):
    scope = scopes.GLOBAL
    auto_accessors = ['ip_addr', 'port', 'webhdfs-port']

    def set_spec(self, spec):
        """
        Set the local spec.

        Should be called after ``{relation_name}.related``.
        """
        conv = self.conversation()
        conv.set_local('spec', json.dumps(spec))

    def spec(self):
        conv = self.conversation()
        return json.loads(conv.get_remote('spec', '{}'))

    def hdfs_ready(self):
        conv = self.conversation()
        return conv.get_remote('hdfs-ready', 'false').lower() == 'true'

    @hook('{requires:hdfs}-relation-joined')
    def joined(self):
        conv = self.conversation()
        conv.set_state('{relation_name}.related')

    @hook('{requires:hdfs}-relation-changed')
    def changed(self):
        conv = self.conversation()
        available = all([self.spec(), self.ip_addr(), self.port(), self.webhdfs_port()])
        spec_matches = self._spec_match()
        ready = self.hdfs_ready()

        conv.toggle_state('{relation_name}.spec.mismatch', available and not spec_matches)
        conv.toggle_state('{relation_name}.ready', available and spec_matches and ready)

    @hook('{requires:hdfs}-relation-{departed,broken}')
    def departed(self):
        self.remove_state('{relation_name}.related')
        self.remove_state('{relation_name}.spec.mismatch')
        self.remove_state('{relation_name}.ready')

    def _spec_match(self):
        conv = self.conversation()
        local_spec = json.loads(conv.get_local('spec', '{}'))
        remote_spec = json.loads(conv.get_remote('spec', '{}'))
        for key, value in local_spec.items():
            if value != remote_spec.get(key):
                return False
