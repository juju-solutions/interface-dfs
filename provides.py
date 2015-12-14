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
from charms.reactive.bus import get_states

from charmhelpers.core import hookenv

from jujubigdata import utils


class HDFSProvides(RelationBase):
    scope = scopes.UNIT

    @hook('{provides:hdfs}-relation-joined')
    def joined(self):
        conv = self.conversation()
        conv.set_state('{relation_name}.client.connected')

    @hook('{provides:hdfs}-relation-changed')
    def changed(self):
        conv = self.conversation()
        if asbool(conv.get_remote('datanode')):
            conv.set_state('{relation_name}.datanode.connected')
        if asbool(conv.get_remote('secondary')):
            conv.set_state('{relation_name}.secondary.connected')

    @hook('{provides:hdfs}-relation-departed')
    def departed(self):
        conv = self.conversation()
        if asbool(conv.get_remote('datanode')):
            conv.add_state('{relation_name}.datanode.leaving')
            conv.remove_state('{relation_name}.datanode.connected')
        if asbool(conv.get_remote('secondary')):
            conv.add_state('{relation_name}.secondary.leaving')
            conv.remove_state('{relation_name}.secondary.connected')
        hookenv.log('Departed states: {}'.format(get_states().keys()))

    @hook('{provides:hdfs}-relation-broken')
    def broken(self):
        conv = self.conversation()
        conv.remove_state('{relation_name}.client.connected')
        conv.remove_state('{relation_name}.datanode.connected')
        conv.remove_state('{relation_name}.secondary.connected')

    def datanodes(self):
        """
        Returns a list of connected DataNodes.

        Output format is::

            [
                {
                    'hostname': hostname_of_unit,  # derived from unit name
                    'ip': resolved_ip,
                },
                # ...
            ]
        """
        datanodes = []
        for conv in self.conversations():
            if asbool(conv.get_remote('datanode')):
                datanodes.append({
                    'hostname': conv.get_remote('hostname'),
                    'ip': utils.resolve_private_address(conv.get_remote('private-address')),
                })
        return datanodes

    def secondaries(self):
        """
        Returns a list of connected Secondary NameNodes.

        Output format is::

            [
                {
                    'hostname': hostname_of_unit,  # derived from unit name
                    'ip': resolved_ip,
                    'port': port,
                },
                # ...
            ]
        """
        secondaries = []
        for conv in self.conversations():
            if asbool(conv.get_remote('secondary')):
                secondaries.append({
                    'hostname': conv.get_remote('hostname'),
                    'ip': utils.resolve_private_address(conv.get_remote('private-address')),
                    'port': conv.get_remote('port'),
                })
        return secondaries

    def send_spec(self, spec):
        for conv in self.conversations():
            conv.set_remote('spec', json.dumps(spec))

    def send_ports(self, port, webhdfs_port):
        for conv in self.conversations():
            conv.set_remote(data={
                'port': port,
                'webhdfs-port': webhdfs_port,
            })

    def send_ready(self, ready=True):
        for conv in self.conversations():
            conv.set_remote('hdfs-ready', ready)

    def send_hosts_map(self, hosts_map):
        for conv in self.conversations():
            conv.set_remote('hosts-map', json.dumps(hosts_map))

    def send_ssh_key(self, ssh_key):
        for conv in self.conversations():
            datanode = asbool(conv.get_remote('datanode'))
            secondary = asbool(conv.get_remote('secondary'))
            if datanode or secondary:
                conv.set_remote('ssh-key', ssh_key)


def asbool(v):
    return (v or '').lower() == 'true'
