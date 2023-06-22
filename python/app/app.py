import socketserver
import time
import requests

from kubernetes import client, config
from http.server import BaseHTTPRequestHandler
from kubernetes.client.rest import ApiException
from pprint import pprint

class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Catch all incoming GET requests"""
        if self.path == "/healthz":
            self.healthz()
        elif self.path == "/k8s_api_status":
            self.check_api_status()
        elif self.path == "/get_pods":
            self.get_all_services()
        elif self.path == "/deployments_pod_status":
            self.check_deployment_pods_status()
        else:
            self.send_error(404)

    def healthz(self):
        """Responds with the health status of the application"""
        self.respond(200, "ok")

    def respond(self, status: int, content: str):
        """Writes content and status code to the response socket"""
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()

        self.wfile.write(bytes(content, "UTF-8"))

    def check_deployment_pods_status(self):
        """Checks the status of the deployment pods"""
        try:
            config.load_kube_config()
            v1 = client.AppsV1Api()
            deployments = v1.list_deployment_for_all_namespaces().items
            for deployment in deployments:
                deployment_name = deployment.metadata.name
                configured_replicas = deployment.spec.replicas

                # Get the current status of the deployment
                status = deployment.status
                available_replicas = status.available_replicas

                # Compare the available replicas with the desired replicas
                print(f"Deployment {deployment_name} has {available_replicas} available replicas out of {configured_replicas} configured.")
        except requests.exceptions.RequestException as e:
            return "Failed to connect to Kubernetes API and check the deployment status: {}".format(e)


    def get_all_services(self):
        try:
            config.load_kube_config()
            # Create an instance of the Kubernetes API client
            v1 = client.CoreV1Api()
            #configuration = v1.client.Configuration()
            services = v1.list_service_for_all_namespaces()
            for service in services.items:
                print("Service name: {}".format(service.metadata.name))

            return v1.list_service_for_all_namespaces().items
        except requests.exceptions.RequestException as e:
            return "Failed to connect to Kubernetes API: {}".format(e)

    def check_api_status(self):
        """Checks the status of the Kubernetes API """
        try:
            config.load_kube_config()
            response = requests.get("http://127.0.0.1:8080/")
            if response.status_code == 200:
                return "Kubernetes API is reachable and healthy"
            else:
                return "Kubernetes API returned an error: {}".format(response.status_code)
        except requests.exceptions.RequestException as e:
            return "Failed to connect to Kubernetes API: {}".format(e)


def api_status_check():
    """ 
    Returns a message periodically for the status of K8s API connection.
    """
    while True:
        is_connected = get_kubernetes_version()

        if is_connected:
            print("Connected to k8s API server")
        else:
            print("Failed to connect to k8s API server")

        time.sleep(5)


def get_kubernetes_version(api_client: client.ApiClient) -> str:
    """
    Returns a string GitVersion of the Kubernetes server defined by the api_client.
    If it can't connect an underlying exception will be thrown.
    """
    version = client.VersionApi(api_client).get_code()
    return version.git_version


def start_server(address):
    """
    Launches an HTTP server with handlers defined by AppHandler class and blocks until it's terminated.

    Expects an address in the format of `host:port` to bind to.

    Throws an underlying exception in case of error.
    """
    try:
        host, port = address.split(":")
    except ValueError:
        print("invalid server address format")
        return

    with socketserver.TCPServer((host, int(port)), AppHandler) as httpd:
        print("Server listening on {}".format(address))
    #    api_status_check()
        httpd.serve_forever()


