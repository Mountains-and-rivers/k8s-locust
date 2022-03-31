
cat /data/scripts/pull_k8s_images.sh
# 内容为
set -o errexit
set -o nounset
set -o pipefail

##这里定义需要下载的版本
KUBE_VERSION=v1.20.15
KUBE_PAUSE_VERSION=3.2
ETCD_VERSION=3.4.13-0
DNS_VERSION=1.7.0

##这是原来被墙的仓库
GCR_URL=k8s.gcr.io

##这里就是写你要使用的仓库,也可以使用gotok8s
DOCKERHUB_URL=registry.cn-hangzhou.aliyuncs.com/google_containers

##这里是镜像列表
images=(
kube-proxy:${KUBE_VERSION}
kube-scheduler:${KUBE_VERSION}
kube-controller-manager:${KUBE_VERSION}
kube-apiserver:${KUBE_VERSION}
pause:${KUBE_PAUSE_VERSION}
etcd:${ETCD_VERSION}
coredns:${DNS_VERSION}
)

## 这里是拉取和改名的循环语句, 先下载, 再tag重命名生成需要的镜像, 再删除下载的镜像
for imageName in ${images[@]} ; do
	  docker pull $DOCKERHUB_URL/$imageName
	    docker tag $DOCKERHUB_URL/$imageName $GCR_URL/$imageName
	      docker rmi $DOCKERHUB_URL/$imageName
      done
