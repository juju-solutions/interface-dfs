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

from charmhelpers.core import hookenv


class HDFSRequires(RelationBase):
    scope = scopes.GLOBAL
    auto_accessors = ['port', 'webhdfs-port', 'ssh-key']

    def local_hostname(self):
        return hookenv.local_unit().replace('/', '-')

    def spec(self):
        return json.loads(self.get_remote('spec', '{}'))

    def host(self):
        return self.get_remote('private-address')

    def hosts_map(self):
        return json.loads(self.get_remote('hosts-map', '{}'))

    def hdfs_ready(self):
        return self.get_remote('hdfs-ready', 'false').lower() == 'true'

    @hook('{requires:hdfs}-relation-joined')
    def joined(self):
        self.set_state('{relation_name}.related')

    @hook('{requires:hdfs}-relation-changed')
    def changed(self):
        if all([self.spec(), self.host(), self.port(), self.webhdfs_port()]):
            self.set_state('{relation_name}.available')
        else:
            self.remove_state('{relation_name}.available')

        if self.local_hostname() in self.hosts_map().values():
            self.set_state('{relation_name}.registered')
        else:
            self.remove_state('{relation_name}.registered')

        if all([self.spec(), self.host(), self.port(), self.webhdfs_port(), self.hdfs_ready()]):
            self.set_state('{relation_name}.ready')
        else:
            self.remove_state('{relation_name}.ready')

        if self.ssh_key():
            self.set_state('{relation_name}.ssh_key.available')
        else:
            self.remove_state('{relation_name}.ssh_key.available')

    @hook('{requires:hdfs}-relation-{departed,broken}')
    def departed(self):
        self.remove_state('{relation_name}.related')
        self.remove_state('{relation_name}.available')
        self.remove_state('{relation_name}.registered')
        self.remove_state('{relation_name}.ready')
        self.remove_state('{relation_name}.ssh_key.available')

    def register_datanode(self):
        self.set_remote(
            datanode=True,
            hostname=hookenv.local_unit().replace('/', '-'),
        )

    def register_secondary(self, port):
        self.set_remote(
            secondary=True,
            hostname=hookenv.local_unit().replace('/', '-'),
            port=port,
        )
