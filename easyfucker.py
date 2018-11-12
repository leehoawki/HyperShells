#!/usr/bin/python3

import argparse
import requests
import json
from kubernetes import client, config


class k8sservice(object):
    def __init__(self, v1, namespace="dev"):
        self.v1 = v1
        self.namespace = namespace
        self.services = {}
        for item in v1.list_namespaced_service(namespace).items:
            ports = item.spec.ports
            for port in ports:
                if port.node_port is not None and 30000 < port.node_port < 31000:
                    self.services[item.metadata.name] = str(port.node_port)

    def get_services(self):
        return self.services

    def get_service(self, name):
        return self.services.get(name)

    def get_service_http_port(self, name):
        if self.services.get(name) is not None:
            return self.services.get(name)[0]


def login(name="admin", password="123456"):
    headers = {'Content-Type': 'application/json'}
    payload = {'name': name, 'password': password}
    return requests.post("http://" + target + "/api/u/login", headers=headers, data=json.dumps(payload)).json()['data']['token']


def create(name, swagger_url, description, url):
    payload = {}
    payload['name'] = name
    payload['url'] = url
    payload['swagger_url'] = swagger_url
    payload['description'] = description
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token}
    requests.post("http://" + target + "/api/project/create", headers=headers, data=json.dumps(payload))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='easy-mock fucker command')
    parser.add_argument('-l', action="store_true", help="list all swaggerable services")
    parser.add_argument('-s', action="store_true", help="create all swaggerable services")
    parser.add_argument('-u', default="admin", help="easymock name")
    parser.add_argument('-p', default="123456", help="easymock password")
    parser.add_argument('-k', default="10.1.62.23", help="k8s host")
    parser.add_argument('-t', default="10.1.62.96:8080", help="easy-mock api target")

    namespace = parser.parse_args()

    config.load_kube_config()
    v1 = client.CoreV1Api()
    k8ss = k8sservice(v1)

    if namespace.l:
        for service, port in k8ss.get_services().items():
            try:
                swagger_url = "http://" + namespace.k + ":" + port + "/v2/api-docs"
                response = requests.get(swagger_url, timeout=1)
                if response.status_code == 200:
                    print(service + ":" + port)
            except Exception as e:
                pass
    elif namespace.s:
        target = namespace.t
        token = login(namespace.u, namespace.p)
        for service, port in k8ss.get_services().items():
            try:
                swagger_url = "http://" + namespace.k + ":" + port + "/v2/api-docs"
                response = requests.get(swagger_url, timeout=1)
                if response.status_code == 200:
                    print("creating easymock project for service:" + service)
                    create(service, swagger_url, '', "/" + service)
            except Exception as e:
                pass
    else:
        parser.print_help()
