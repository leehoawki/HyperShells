package main

import (
	"context"
	"flag"
	appv1 "k8s.io/api/apps/v1"
	v1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/util/homedir"
	"path/filepath"
)

var (
	application = flag.String("a", "", "Application name")
	version     = flag.String("v", "latest", "Application version")
)

var config *rest.Config
var client *kubernetes.Clientset
var err error

const REPO string = "10.29.3.10:5000"
const NAMESPACE string = "dev"

func main() {
	flag.Parse()

	home := homedir.HomeDir()
	config, err = clientcmd.BuildConfigFromFlags("", filepath.Join(home, ".kube", "config"))
	if err != nil {
		panic(err)
	}

	client, err = kubernetes.NewForConfig(config)
	if err != nil {
		panic(err)
	}

	if *application == "" {
		panic("application is empty")
	}

	println("application=" + *application + ", version=" + *version)
	deployment(*application, *version)
	service(*application)
}

func deployment(application string, version string) {
	deployment := &appv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      application,
			Namespace: NAMESPACE,
			Labels: map[string]string{
				"app":                       application,
				"app.kubernetes.io/name":    application,
				"app.kubernetes.io/version": "v1",
			},
		},
		Spec: appv1.DeploymentSpec{
			Replicas: int32Ptr(1),
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{
					"app":                       application,
					"app.kubernetes.io/name":    application,
					"app.kubernetes.io/version": "v1",
				},
			},
			Template: v1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{
						"app":                       application,
						"app.kubernetes.io/name":    application,
						"app.kubernetes.io/version": "v1",
					},
				},
				Spec: v1.PodSpec{
					Containers: []v1.Container{
						{
							Name:  application,
							Image: REPO + "/" + application + ":" + version,
							Ports: []v1.ContainerPort{
								{
									Name:          "http",
									Protocol:      v1.ProtocolTCP,
									ContainerPort: 8080,
								},
							},
							Env: []v1.EnvVar{
								{
									Name:  "ENV",
									Value: "DEV",
								},
								{
									Name:  "APOLLO_CONFIGSERVICE",
									Value: "http://10.141.48.10:18080/",
								},
							},
							ImagePullPolicy: v1.PullIfNotPresent,
						},
					},
				},
			},
		},
	}

	err = client.AppsV1().Deployments(NAMESPACE).Delete(context.TODO(), application, metav1.DeleteOptions{})
	if err != nil {

	}
	_, err = client.AppsV1().Deployments(NAMESPACE).Create(context.TODO(), deployment, metav1.CreateOptions{})
	if err != nil {
		panic(err)
	}
}

func int32Ptr(i int32) *int32 { return &i }

func service(application string) {
	svc := &v1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:      application,
			Namespace: NAMESPACE,
			Labels: map[string]string{
				"app":                       application,
				"app.kubernetes.io/name":    application,
				"app.kubernetes.io/version": "v1",
			},
		},
		Spec: v1.ServiceSpec{
			Ports: []v1.ServicePort{
				v1.ServicePort{
					Name:     "http-8080",
					Protocol: v1.ProtocolTCP,
					Port:     8080,
					TargetPort: intstr.IntOrString{
						IntVal: 8080,
					},
				},
			},
			Selector: map[string]string{
				"app":                       application,
				"app.kubernetes.io/name":    application,
				"app.kubernetes.io/version": "v1",
			},
		},
	}

	_, err = client.CoreV1().Services(NAMESPACE).Create(context.TODO(), svc, metav1.CreateOptions{})
	if err != nil {

	}
}
