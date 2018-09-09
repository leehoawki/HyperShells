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
            node = http_node(self.zk, name, path)
            if node.is_active():
                yield node

    def get_dubbo_nodes(self):
        for name in self.zk.get_children(zkservice.dubbo_service):
            path = zkservice.dubbo_service + "/" + name
            node = dubbo_node(self.zk, name, path)
            if node.is_active():
                yield node

    def get_http_node(self, name):
        if not self.zk.exists(zkservice.http_service + "/" + name):
            self.zk.create(zkservice.http_service + "/" + name)
        return http_node(self.zk, name, zkservice.http_service + "/" + name)

    def get_dubbo_node(self, name):
        if not self.zk.exists(zkservice.dubbo_service + "/" + name):
            self.zk.create(zkservice.dubbo_service + "/" + name)
        return dubbo_node(self.zk, name, zkservice.dubbo_service + "/" + name)

    def exists(self, name):
        if self.zk.exists(zkservice.http_service + "/" + name):
            return name
        if len(name) > 2 and name[-1].isdigit() and name[-2] == "v" and self.zk.exists(zkservice.http_service + "/" + name[:-2]):
            return name[:-2]
        if len(name) > 3 and name[-3:] == "api" and self.zk.exists(zkservice.http_service + "/" + name[:-3]):
            return name[:-3]
        if len(name) > 3 and name[-3:] == "api" and self.zk.exists(
                zkservice.http_service + "/" + name[:-3] + "service"):
            return name[:-3] + "service"
        return None


class http_node(object):
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


class dubbo_node(object):
    def __init__(self, zk, name, path):
        self.zk = zk
        self.name = name
        self.path = path
        self.url = None
        self.pod_ip = None
        self.pod_port = None
        self.providers = []
        if self.zk.exists(path + "/providers/"):
            self.providers = self.zk.get_children(path + "/providers/")
            if len(self.providers) > 0:
                url = urllib.parse.unquote(self.providers[0])
                i = url.find("://")
                j = url[i + 3:].find(":")
                k = url[i + j + 4:].find("/")
                self.url = url
                self.pod_ip = url[i + 3: i + j + 3]
                self.pod_port = url[i + j + 4: i + j + k + 4]

    def get_name(self):
        return self.name

    def get_simple_data(self):
        if self.pod_ip is not None and self.pod_port is not None:
            return self.pod_ip + ":" + self.pod_port
        return ""

    def get_data(self):
        return self.url

    def is_active(self):
        return len(self.providers) > 0

    def update(self, target):
        if len(self.providers) == 0:
            if not self.zk.exists(self.path + "/providers"):
                self.zk.create(self.path + "/providers/")
            self.zk.create(self.path + "/providers/" + urllib.parse.quote_plus(target))
        else:
            for provider in self.providers:
                self.zk.delete(self.path + "/providers/" + provider)
            self.zk.create(self.path + "/providers/" + urllib.parse.quote_plus(target))


class k8sservice(object):
    def __init__(self, v1, namespace="dev"):
        self.v1 = v1
        self.namespace = namespace
        self.services = {}
        self.pods = {}
        for item in v1.list_namespaced_service(namespace).items:
            ports = item.spec.ports
            http_port = None
            dubbo_port = None
            for port in ports:
                if port.node_port is not None and 31000 < port.node_port < 32000:
                    dubbo_port = str(port.node_port)
                elif port.node_port is not None:
                    http_port = str(port.node_port)
            self.services[item.metadata.name] = (http_port, dubbo_port)
        for item in v1.list_namespaced_pod(namespace).items:
            app = item.metadata.labels.get('app')
            if app is not None:
                self.pods[item.status.pod_ip] = app

    def get_services(self):
        return self.services.values()

    def get_service(self, name):
        return self.services.get(name)

    def get_service_http_port(self, name):
        if self.services.get(name) is not None:
            return self.services.get(name)[0]

    def get_service_dubbo_port(self, name):
        if self.services.get(name) is not None:
            return self.services.get(name)[1]

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
        print("-----------------http-service------------------")
        for node in zks_from.get_http_nodes():
            print(node.get_name() + ", " + node.get_data() + ", " + zks_to.get_http_node(node.get_name()).get_data())
        print("-----------------dubbo-service-----------------")
        for node in zks_from.get_dubbo_nodes():
            print(node.get_name() + ", " + node.get_simple_data() + ", " + zks_to.get_dubbo_node(node.get_name()).get_simple_data())
    elif namespace.a:
        for node in zks_from.get_http_nodes():
            name = get_name(node.get_data())
            port = k8ss.get_service_http_port(name)
            node_to = zks_to.get_http_node(node.get_name())
            if port is not None and node_to.get_data() == prefix + ":" + port:
                print(node.get_name() + ", " + name + ", " + node_to.get_data())
    elif namespace.u:
        for node in zks_from.get_http_nodes():
            name = get_name(node.get_data())
            port = k8ss.get_service_http_port(name)
            node_to = zks_to.get_http_node(node.get_name())
            if port is None or node_to.get_data() != prefix + ":" + port:
                print(node.get_name() + ", " + name + ", " + node_to.get_data())
    elif namespace.p:
        print("-----------------http-service------------------")
        for node_from in zks_from.get_http_nodes():
            name = get_name(node_from.get_data())
            port = k8ss.get_service_http_port(name)
            node_to = zks_to.get_http_node(node_from.get_name())
            if port is None:
                continue
            if node_to.get_data() != prefix + ":" + port:
                print(node_from.get_name() + " setting from " + node_to.get_data() + " to " + prefix + ":" + port + " of " + name)
        print("-----------------dubbo-service-----------------")
        for node_from in zks_from.get_dubbo_nodes():
            service = k8ss.get_pod(node_from.pod_ip)
            port = k8ss.get_service_dubbo_port(service)
            node_to = zks_to.get_dubbo_node(node_from.get_name())
            if service is None or port is None:
                port = str(int(node_from.pod_port) + 12000)
            target = node_from.url.replace(node_from.pod_ip, prefix).replace(node_from.pod_port, port)
            if str(node_to.get_data()) != target:
                print(node_from.get_name() + " setting from " + str(node_to.get_data()) + " to " + target)
    elif namespace.x:
        print("-----------------http-service------------------")
        for node_from in zks_from.get_http_nodes():
            name = get_name(node_from.get_data())
            port = k8ss.get_service_http_port(name)
            node_to = zks_to.get_http_node(node_from.get_name())
            if port is None:
                continue
            if node_to.get_data() != prefix + ":" + port:
                print(node_from.get_name() + " setting from " + node_to.get_data() + " to " + prefix + ":" + port + " of " + name)
                node_to.update(prefix + ":" + port)
        print("-----------------dubbo-service-----------------")
        for node_from in zks_from.get_dubbo_nodes():
            service = k8ss.get_pod(node_from.pod_ip)
            port = k8ss.get_service_dubbo_port(service)
            node_to = zks_to.get_dubbo_node(node_from.get_name())
            if service is None or port is None:
                port = str(int(node_from.pod_port) + 12000)
            target = node_from.url.replace(node_from.pod_ip, prefix).replace(node_from.pod_port, port)
            if str(node_to.get_data()) != target:
                print(node_from.get_name() + " setting from " + str(node_to.get_data()) + " to " + target)
                node_to.update(target)
    else:
        print("zkfrom:" + namespace.f)
        print("zkto:" + namespace.t)
        print("prefix:" + prefix)
