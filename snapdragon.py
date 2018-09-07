#!/usr/bin/python3

import argparse
import urllib.parse
from kubernetes import client, config
from kazoo.client import KazooClient


class zkservice(object):
    http_service = "/service"
    dubbo_service = "/dubbo"

    def __init__(self, zk):
        self.zk = zk

    def get_http_nodes(self):
        for name in self.zk.get_children(zkservice.http_service):
            path = zkservice.http_service + "/" + name
            node = zknode(self.zk, name, path)
            if node.is_active():
                yield node

    def get_dubbo_nodes(self):
        for name in self.zk.get_children(zkservice.dubbo_service):
            providers = self.zk.get_children(zkservice.dubbo_service + "/" + name + "/providers/")
            if len(providers) > 0:
                url = urllib.parse.unquote(providers[0])
                i = url.find("://")
                j = url[i + 3:].find(":")
                yield url[i + 3: i + j + 3]

    def get_http_node(self, name):
        if not self.zk.exists(zkservice.http_service + "/" + name):
            self.zk.create(zkservice.http_service + "/" + name)
        return zknode(self.zk, name, zkservice.http_service + "/" + name)

    def exists(self, name):
        if self.zk.exists(zkservice.http_service + "/" + name):
            return name
        if len(name) > 2 and name[-1].isdigit() and name[-2] == "v" and self.zk.exists(zkservice.http_service + "/" + name[:-2]):
            return name[:-2]
        if len(name) > 3 and name[-3:] == "api" and self.zk.exists(zkservice.http_service + "/" + name[:-3]):
            return name[:-3]
        if len(name) > 3 and name[-3:] == "api" and self.zk.exists(zkservice.http_service + "/" + name[:-3] + "service"):
            return name[:-3] + "service"
        return None


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
        return len(self.data) > 0 and not self.data.startswith("tcp://")

    def get_name(self):
        return self.name

    def get_data(self):
        return self.data

    def update(self, target):
        if len(self.nodes) == 0:
            self.zk.create(self.path + "/0", target.encode())
        else:
            self.zk.set(self.path + "/" + self.nodes[0], target.encode())


class k8sservice(object):
    def __init__(self, v1, namespace="dev"):
        self.v1 = v1
        self.namespace = namespace
        self.services = {}
        self.pods = {}
        for item in v1.list_namespaced_service(namespace).items:
            ports = item.spec.ports
            http_port = None
            for port in ports:
                if port.node_port is not None:
                    http_port = str(port.node_port)
            if http_port is not None:
                self.services[item.metadata.name] = http_port

        for item in  v1.list_namespaced_pod(namespace).items:
            self.pods[item.status.pod_ip] = item.metadata.labels['app']

    def get_services(self):
        return self.services.values()

    def get_service(self, name):
        return self.services.get(name)

    def get_pod(self, ip):
        return self.pods.get(ip)


def get_name(url):
    i = url.find("://")
    i = 0 if i < 0 else i + 3
    url = url[i:]
    j = url.find(":")
    j = len(url) if j < 0 else j
    return url[:j]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='timestamp command')
    parser.add_argument('-l', action="store_true", help="list all services")
    parser.add_argument('-a', action="store_true", help="list all aligned services")
    parser.add_argument('-u', action="store_true", help="list all unaligned services")
    parser.add_argument('-p', action="store_true", help="print the updates to be done")
    parser.add_argument('-x', action="store_true", help="execute the updates")

    parser.add_argument('-f', default="10.1.62.23:2181", help="zookeeper(from） url, eg 10.1.62.23:2181")
    parser.add_argument('-t', default="localhost:2181", help="zookeeper(to) url, eg localhost:2181")
    parser.add_argument('-k', default="10.1.62.23", help="endpoint prefix, eg 10.1.62.23")

    namespace = parser.parse_args()

    zk_client_from = KazooClient(hosts=namespace.f)
    zk_client_to = KazooClient(hosts=namespace.t)
    zk_client_from.start()
    zk_client_to.start()

    prefix = namespace.k

    config.load_kube_config()
    v1 = client.CoreV1Api()
    zks_from = zkservice(zk_client_from)
    zks_to = zkservice(zk_client_to)
    k8ss = k8sservice(v1)

    if namespace.l:
        for node in zks_from.get_http_nodes():
            print(node.get_name() + ", " + node.get_data() + ", " + zks_to.get_http_node(node.get_name()).get_data())
    elif namespace.a:
        for node in zks_from.get_http_nodes():
            name = get_name(node.get_data())
            port = k8ss.get_service(name)
            node_to = zks_to.get_http_node(node.get_name())
            if port is not None and node_to.get_data() == prefix + ":" + port:
                print(node.get_name() + ", " + name + ", " + node_to.get_data())
    elif namespace.u:
        for node in zks_from.get_http_nodes():
            name = get_name(node.get_data())
            port = k8ss.get_service(name)
            node_to = zks_to.get_http_node(node.get_name())
            if port is None or node_to.get_data() != prefix + ":" + port:
                print(node.get_name() + ", " + name + ", " + node_to.get_data())
    elif namespace.p:
        for node_from in zks_from.get_http_nodes():
            name = get_name(node_from.get_data())
            port = k8ss.get_service(name)
            node_to = zks_to.get_http_node(node_from.get_name())
            if port is None:
                continue
            if node_to.get_data() != prefix + ":" + port:
                print(node_from.get_name() + " setting from " + node_to.get_data() + " to " + prefix + ":" + port + " of " + name)

        for node_from in zks_from.get_dubbo_nodes():
            pass
    elif namespace.x:
        for node_from in zks_from.get_http_nodes():
            name = get_name(node_from.get_data())
            port = k8ss.get_service(name)
            node_to = zks_to.get_http_node(node_from.get_name())
            if port is None:
                continue
            if node_to.get_data() != prefix + ":" + port:
                print(node_from.get_name() + " setting from " + node_to.get_data() + " to " + prefix + ":" + port + " of " + name)
                node_to.update(prefix + ":" + port)
    else:
        print("zkfrom:" + namespace.f)
        print("zkto:" + namespace.t)
        print("prefix:" + prefix)
