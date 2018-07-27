#!/usr/bin/python3

import argparse
from kubernetes import client, config
from kazoo.client import KazooClient


class zkservice(object):
    service = "/service"

    def __init__(self, zk):
        self.zk = zk

    def get_nodes(self):
        for name in self.zk.get_children(zkservice.service):
            path = zkservice.service + "/" + name
            node = zknode(self.zk, name, path)
            if node.is_active():
                yield node

    def get_aligned_node(self):
        for node in self.get_nodes():
            if node.is_aligned():
                yield node

    def get_unaligned_node(self):
        for node in self.get_nodes():
            if not node.is_aligned():
                yield node

    def exists(self, name):
        if self.zk.exists(zkservice.service + "/" + name):
            return name
        if len(name) > 2 and name[-1].isdigit() and name[-2] == "v" and self.zk.exists(zkservice.service + "/" + name[:-2]):
            return name[:-2]
        if len(name) > 3 and name[-3:] == "api" and self.zk.exists(zkservice.service + "/" + name[:-3]):
            return name[:-3]
        if len(name) > 3 and name[-3:] == "api" and self.zk.exists(zkservice.service + "/" + name[:-3] + "service"):
            return name[:-3] + "service"
        return None

    def get_node(self, name):
        return zknode(zk, name, zkservice.service + "/" + name)


class zknode(object):
    def __init__(self, zk, name, path):
        self.zk = zk
        self.name = name
        self.path = path
        self.nodes = self.zk.get_children(path)
        if len(self.nodes) == 0:
            self.data = ""
        else:
            data, stat = self.zk.get(self.path + "/" + self.nodes[0])
            self.data = data.decode().replace("\n", "")
            self.stat = stat

    def is_active(self):
        return len(self.data) > 0

    def get_name(self):
        return self.name

    def get_data(self):
        return self.data

    def is_aligned(self):
        return self.data.startswith(prefix + ":")

    def update(self, target):
        if len(self.nodes) == 0:
            zk.create(self.path + "/0", target.encode())
        else:
            self.zk.set(self.path + "/" + self.nodes[0], target.encode())


class k8sservice(object):
    def __init__(self, v1, namespace="dev"):
        self.v1 = v1
        self.namespace = namespace
        self.services = v1.list_namespaced_service(namespace)

    def get_services(self):
        for item in self.services.items:
            ports = item.spec.ports
            if len(ports) == 1 and ports[0].node_port is not None and ports[0].node_port > 0:
                yield item.metadata.name, str(ports[0].node_port)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='timestamp command')
    parser.add_argument('-l', action="store_true", help="list all services")
    parser.add_argument('-a', action="store_true", help="list all aligned services")
    parser.add_argument('-u', action="store_true", help="list all unaligned services")
    parser.add_argument('-p', action="store_true", help="print the updates to be done")
    parser.add_argument('-x', action="store_true", help="execute the updates")
    parser.add_argument('-z', default="sy-suz-dev01:2181", help="zookeeper url, eg sy-suz-dev01:2181")
    parser.add_argument('-k', default="10.1.62.23", help="endpoint prefix, eg 10.1.62.23")

    namespace = parser.parse_args()

    zkhost = namespace.z
    prefix = namespace.k

    config.load_kube_config()
    v1 = client.CoreV1Api()
    zk = KazooClient(hosts=zkhost)
    zk.start()
    zks = zkservice(zk)
    k8ss = k8sservice(v1)

    if namespace.l:
        for node in zks.get_nodes():
            print(node.get_name() + ":" + node.get_data())
    elif namespace.a:
        for node in zks.get_aligned_node():
            print(node.get_name() + ":" + node.get_data())
    elif namespace.u:
        for node in zks.get_unaligned_node():
            print(node.get_name() + ":" + node.get_data())
    elif namespace.p:
        for item, port in k8ss.get_services():
            name = zks.exists(item)
            if name is not None:
                node = zks.get_node(name)
                target = prefix + ":" + port
                if target != node.get_data():
                    print(name + " setting from " + node.get_data() + " to " + target + " of " + item)
    elif namespace.x:
        for item, port in k8ss.get_services():
            name = zks.exists(item)
            if name is not None:
                node = zks.get_node(name)
                target = prefix + ":" + port
                if target != node.get_data():
                    print(name + " setting from " + node.get_data() + " to " + target + " of " + item)
                    node.update(target)
    else:
        print("zkhost:" + zkhost)
        print("prefix:" + prefix)
