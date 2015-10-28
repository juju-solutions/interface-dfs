# Overview

This interface layer handles the communication with HDFS via the `hdfs` interface
protocol.  It is intended for internal use within the Hadoop cluster charms.
For typical usage, [interface-hadoop-plugin][] should be used instead.


# Usage

## Requires

Charms requiring this interface can be clients, DataNodes, or SecondaryNameNodes.
Clients simply depend on HDFS to serve as a distributed file system to them, while
DataNodes and SecondaryNameNodes register to provide additional services back.

This interface layer will set the following states, as appropriate:

  * `{relation_name}.related` The relation is established, but HDFS may not yet
    have provided any connection or service information.

  * `{relation_name}.available` HDFS has provided its connection and service
    information, but is not yet ready to serve as a distributed file system.
    The provided information can be accessed via the following methods:
      * `host()`
      * `port()`
      * `webhdfs_port()`
      * `hosts_map()`

  * `{relation_name}.ready` HDFS is fully ready to serve as a distributed file
    system.

  * `{relation_name}.ssh_key.available` An SSH key is being provided to allow
    tools on the NameNode unit to access this unit.  This will only be set if
    the service has registered itself as a DataNode or a SecondaryNameNode.
    The SSH key can be accessed via the `ssh_key()` method.

For example, a typical client respond to `hdfs.ready`:

```python
@when('flume.installed', 'hdfs.ready')
def hdfs_ready(hdfs):
    utils.update_etc_hosts(hdfs.hosts_map())
    flume.configure(hdfs)
    flume.start()
```

Whereas, a DataNode or SecondaryNameNode would respond to `hdfs.related`
and `hdfs.available` instead:

```python
@when('hdfs.related')
def register_secondary(hdfs):
    hdfs.register_secondary(dist_config.get('port'))

@when('hdfs.available')
def update_etc_hosts(hdfs):
    utils.update_etc_hosts(hdfs.hosts_map())

@when('hadoop.installed', 'hdfs.available')
def configure_secondary(hdfs):
    secondary.configure(hdfs)
    secondary.start()

@when('hdfs.ssh_key.available')
def install_ssh_key(hdfs):
    utils.install_ssh_key(hdfs.ssh_key())

@when_not('hdfs.ssh_key.available')
def remove_ssh_key():
    utils.remove_ssh_key()
```


## Provides

A charm providing this interface is providing the HDFS service.

This interface layer will set the following states, as appropriate:

  * `{relation_name}.client.connected` One or more clients of any type have
    connected.  The charm should call the following methods to provide the
    appropriate information to the clients:
      * `send_spec(spec)`
      * `send_ports(port, webhdfs_port)`
      * `send_hosts_map(hosts_map)`
      * `send_ready()`

  * `{relation_name}.datanode.connected` One or more DataNodes have registered.
    The charm can access the list of registered DataNodes via the `datanodes()`
    method and should send an SSH key via the `send_ssh_key(ssh_key)` method.

  * `{relation_name}.secondary.connected` One or more SecondaryNameNodes have
    registered.  The charm can access the list of registered SecondaryNameNodes
    via the `secondaries()` method and should send an SSH key via the
    `send_ssh_key(ssh_key)` method.

Example:

```python
@when('hdfs.client.connected')
def serve_client(hdfs):
    hdfs.send_spec(utils.build_spec())
    hdfs.send_ports(dist_config.get('port'), dist_config.get('webhdfs_port'))
    hdfs.send_hosts_map(utils.build_hosts_map())

@when('hdfs.client.connected', 'hdfs.datanode.connected')
def check_ready(hdfs):
    if utils.wait_for_hdfs():
        hdfs.send_ready(True)
    else:
        utils.block("HDFS should be ready but isn't")
        hdfs.send_ready(False)

@when('hdfs.datanode.connected')
def register_datanode(hdfs):
    update_slaves(hdfs.datanodes())
    hdfs.send_ssh_key(utils.get_ssh_key())

@when('hdfs.secondary.connected')
def register_secondary(hdfs):
    hdfs.send_ssh_key(utils.get_ssh_key())
```


# Contact Information

- <bigdata@lists.ubuntu.com>


# Hadoop

- [Apache Hadoop](http://hadoop.apache.org/) home page
- [Apache Hadoop bug trackers](http://hadoop.apache.org/issue_tracking.html)
- [Apache Hadoop mailing lists](http://hadoop.apache.org/mailing_lists.html)
- [Apache Hadoop Juju Charm](http://jujucharms.com/?text=hadoop)


[interface-hadoop-plugin]: https://github.com/juju-solutions/interface-hadoop-plugin/
