# 基于k8s+locust+boomer的分布式压力测试方案
eladmin部署参考：https://github.com/elunez/eladmin

修改后的代码打包至release中

主要修改了验证码生成部分，进程启动，固定验证码

## 一，环境信息

| 节点     | k8s节点 | os         | IP             | 服务                      | SDK                              |
| -------- | ------- | ---------- | -------------- | ------------------------- | -------------------------------- |
| master   | true    | centos8.3  | 192.168.31.243 |                           |                                  |
| worker01 | true    | centos8.3  | 192.168.31.230 | mysql-5.7.35，redis-3.0.7 |                                  |
| worker02 | true    | centos8.3  | 192.168.31.28  |                           |                                  |
| worker03 | true    | centos8.3  | 192.168.31.132 | eladmin                   |                                  |
| win11-pc | false   | windows 11 | 192.168.31.217 | nginx/eladmin-web         | node/v16.14.0  jdk/1.8.0_321-b07 |

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/1.png)

## 二，搭建集群

```
参考：https://github.com/Mountains-and-rivers/mongo-replica-set

问题解决：
1，国内镜像拉取失败
kubeadm config images list

# 输出结果, 这些都是K8S的必要组件, 但是由于被墙, 是不能直接docker pull下来的
k8s.gcr.io/kube-apiserver:v1.20.15
k8s.gcr.io/kube-controller-manager:v1.20.15
k8s.gcr.io/kube-scheduler:v1.20.15
k8s.gcr.io/kube-proxy:v1.20.15
k8s.gcr.io/pause:3.2
k8s.gcr.io/etcd:3.4.13-0
k8s.gcr.io/coredns:1.7.0
编写pull脚本

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

参考：https://www.jianshu.com/p/51542b0b239b
```

## 三，组件部署

### 1，单机部署mysql

```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-local
spec:
  capacity:
    storage: 5Gi
  volumeMode: Filesystem
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  storageClassName: local-storage
  local:
    path: /var/lib/mysql  # worker01节点上的目录
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - worker01
---
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: mysql-sre
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: local-storage
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: mysql-config-sre
data:
  mysqld.cnf: |
        [mysqld]
        pid-file        = /var/run/mysqld/mysqld.pid
        socket          = /var/run/mysqld/mysqld.sock
        datadir         = /var/lib/mysql
        log-error      = /var/log/mysql/error.log
        bind-address   = 0.0.0.0
        # Disabling symbolic-links is recommended to prevent assorted security risks
        symbolic-links=0
        max_connections=1000
        default_storage_engine=innodb
        skip_external_locking
        lower_case_table_names=1
        skip_host_cache
        skip_name_resolve
        character_set_server=utf8
        sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION'
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql-sre-database
  labels:
    app: mysql-sre
spec:
  selector:
    matchLabels:
      app: mysql-sre
  template:
    metadata:
      labels:
        app: mysql-sre
    spec:
      containers:
      - name: mysql
        image: mysql:5.7
        imagePullPolicy: IfNotPresent
        args:
        - --default_authentication_plugin=mysql_native_password
        - --character-set-server=utf8mb4
        - --collation-server=utf8mb4_unicode_ci
        ports:
        - containerPort: 3306
          name: dbport
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: MyNewPass4!
        - name: MYSQL_DATABASE
          value: eladmin
        - name: MYSQL_USER
          value: authbase
        - name: MYSQL_PASSWORD
          value: MyNewPass4!
        volumeMounts:
        - name: db-data
          mountPath: /var/lib/mysql
        - name: mysql-config
          mountPath: /etc/mysql/conf.d/  
      volumes:
      - name: db-data
        persistentVolumeClaim:
          claimName: mysql-sre
      - name: mysql-config
        configMap:
          name: mysql-config-sre
---
apiVersion: v1
kind: Service
metadata:
  name: mysql-sre
spec:
  type: NodePort
  ports:
  - name: mysqlport
    protocol: TCP
    port: 3306
    targetPort: dbport
    nodePort: 30106
  selector:
    app: mysql-sre
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-local-backup
spec:
  capacity:
    storage: 5Gi
  volumeMode: Filesystem
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  storageClassName: local-storage-backup
  local:
    path: /mysql-backup  # worker01节点上的目录
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - worker01
---
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: mysql-sre-backup
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: local-storage-backup
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage-backup
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
---
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: mysql-sre-backup
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: mysql-backup
            imagePullPolicy: IfNotPresent
            image: mysql:5.7
            env:
            - name: MYSQL_BACKUP_USER
              value: root
            - name: MYSQL_BACKUP_USER_PASSWORD
              value: MyNewPass4!
            - name: MYSQL_HOST
              value: mysql-sre
            command:
            - /bin/sh
            - -c
            - |
              set -ex
              mysqldump --host=MYSQL_HOST --user=MYSQL_BACKUP_USER \
                        --password=$MYSQL_BACKUP_USER_PASSWORD \
                        --routines --databases appdb --single-transaction \
                        > /mysql-backup/mysql-`date +"%Y%m%d"`.sql
            volumeMounts:
            - name: mysql-backup
              mountPath: /mysql-backup
          restartPolicy: OnFailure
          volumes:
          - name: mysql-backup
            persistentVolumeClaim:
              claimName: mysql-sre-backup
```

操作：

```
rm -rf {/var/lib/mysql,/mysql-backup}
mkdir -p {/var/lib/mysql,/mysql-backup}
kubectl apply -f mysql.yaml
```

连接测试：

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/2.png)

### 2，单机部署redis

```
kind: ConfigMap
apiVersion: v1
metadata:
  name: redis-config
  labels:
    app: redis
data:
  redis.conf: |-
    dir /srv
    port 6379
    bind 0.0.0.0
    appendonly yes
    daemonize no
    #protected-mode no
    requirepass MyNewPass4!
    pidfile /srv/redis-6379.pid
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  labels:
    app: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:3.0.7
        command:
          - "sh"
          - "-c"
          - "redis-server /usr/local/redis/redis.conf"
        ports:
        - containerPort: 6379
        resources:
          limits:
            cpu: 1000m
            memory: 1024Mi
          requests:
            cpu: 1000m
            memory: 1024Mi
        livenessProbe:
          tcpSocket:
            port: 6379
          initialDelaySeconds: 300
          timeoutSeconds: 1
          periodSeconds: 10
          successThreshold: 1
          failureThreshold: 3
        readinessProbe:
          tcpSocket:
            port: 6379
          initialDelaySeconds: 5
          timeoutSeconds: 1
          periodSeconds: 10
          successThreshold: 1
          failureThreshold: 3
        volumeMounts:
        - name: config
          mountPath:  /usr/local/redis/redis.conf
          subPath: redis.conf
      volumes:
      - name: config
        configMap:
          name: redis-config
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  labels:
    app: redis
spec:
  type: NodePort
  ports:
    - name: tcp
      port: 6379
      nodePort: 30379
  selector:
    app: redis
```

操作：

```
kubectl apply -f redis.yaml
```

连接测试：

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/3.png)

## 四，制作基础镜像

```
FROM centos:8
RUN curl -o Python-3.7.3.tgz https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tgz && \
    tar -xzvf Python-3.7.3.tgz && \
    curl -o /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-8.repo  && \
    sed -i -e "s|mirrors.cloud.aliyuncs.com|mirrors.aliyun.com|g " /etc/yum.repos.d/CentOS-*  && \
    sed -i -e "s|releasever|releasever-stream|g" /etc/yum.repos.d/CentOS-*  && \
    yum clean all && yum makecache  && \
    yum install -y libffi-devel zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel zlib zlib-devel gcc make && \
    mkdir -p /usr/local/python3 && \
    cd Python-3.7.3 && \
    ./configure --prefix=/usr/local/python3 && \
    make && \
    make install && \
    ln -s /usr/local/python3/bin/python3 /usr/bin/python3 && \
    ln -s /usr/local/python3/bin/pip3 /usr/bin/pip3 && \
    rm -rf  /Python-3.7.3.tgz && \
    rm -rf  /Python-3.7.3
ADD jdk-8u202-linux-x64.tar.gz /usr/local
ENV JAVA_HOME /usr/local/jdk1.8.0_202
ENV PATH $PATH:$JAVA_HOME/bin
ENV CLASSPATH .:$JAVA_HOME/lib/dt.jar:$JAVA_HOME/lib/tools.jar
```

操作：

```
docker build -t centos_base:v1 .
```

## 五，部署eladmin

### 1，后端部署

修改连接参数：

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/4.png)
![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/5.png)

maven打包

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/6.png)

制作镜像：

```
FROM centos_base:v1

RUN mkdir -p /usr/local/test

COPY eladmin-system-2.6.jar  /usr/local/test/app.jar

ENTRYPOINT ["java","-jar","/usr/local/test/app.jar"]
```

刷sql脚本：

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/7.png)

打包上传到docker hub

```
[root@master javaDocker]# docker login
#输入用户名
#输入密码
[root@master javaDocker]# docker build -t mangseng/eladmin:v1 .
Sending build context to Docker daemon  116.1MB
Step 1/4 : FROM centos_base:v1
 ---> 54c0f6884bbb
Step 2/4 : RUN mkdir -p /usr/local/test
 ---> Using cache
 ---> 45e8089a5224
Step 3/4 : COPY eladmin-system-2.6.jar  /usr/local/test/app.jar
 ---> 342c845daeae
Step 4/4 : ENTRYPOINT ["java","-jar","/usr/local/test/app.jar"]
 ---> Running in 94fc557e8f55
Removing intermediate container 94fc557e8f55
 ---> 23f92bb9c1c2
Successfully built 23f92bb9c1c2
Successfully tagged mangseng/eladmin:v1
[root@master javaDocker]# docker push mangseng/eladmin:v1
The push refers to repository [docker.io/mangseng/eladmin]
364af3b1d0d9: Pushed 
1ac9fbb1cb18: Pushed 
8cd156f7b9b9: Pushed 
63dfcbd7b345: Pushed 
74ddd0ec08fa: Pushed 
v1: digest: sha256:1d9c01c176214b9444a4b7dc6f0303d6010df18615c32af913fc7a54e8dfff5e size: 1375
```

创建部署模板eladmin-deployment.yaml：

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deploy
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
      release: stabel
  template:
    metadata:
      labels:
        app: myapp
        release: stabel
        env: test
    spec:
      containers:
        - name: myapp
          image: 'mangseng/eladmin:v1'
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8888
---
apiVersion: v1
kind: Service
metadata:
  name: myapp
  namespace: default
spec:
  type: NodePort
  selector:
    app: myapp
    release: stabel
  ports:
    - name: http
      port: 8888
      targetPort: 8888
      nodePort: 30080
```

操作;

```
kubectl apply -f eladmin-deployment.yaml
```

2，前端部署

修改配置

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/8.png)

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/9.png)

执行打包命令:

```
> npm run build:prod
> eladmin-web@2.6.0 build:prod
> vue-cli-service build


\  Building for production...

 WARNING  Compiled with 2 warnings                                                                                                                                                                       22:42:52

 warning  

asset size limit: The following asset(s) exceed the recommended size limit (244 KiB).
This can impact web performance.
Assets: 
  static/img/background.53576a46.jpeg (429 KiB)
  static/css/app.f957a9d3.css (256 KiB)
  static/js/chunk-408d3874.164a4fcf.js (1.47 MiB)
  static/js/chunk-a6b42588.bebc5096.js (308 KiB)
  static/js/chunk-elementUI.98d8dfd0.js (675 KiB)
  static/js/chunk-libs.4e37e4de.js (2.9 MiB)

 warning  

entrypoint size limit: The following entrypoint(s) combined asset size exceeds the recommended limit (244 KiB). This can impact web performance.
Entrypoints:
  app (4.01 MiB)
      static/js/runtime.909294b9.js
      static/js/chunk-elementUI.98d8dfd0.js
      static/css/chunk-libs.6f07664f.css
      static/js/chunk-libs.4e37e4de.js
      static/css/app.f957a9d3.css
      static/js/app.74fd8561.js


  File                                      Size             Gzipped

  dist\static\js\chunk-libs.4e37e4de.js     2973.09 KiB      975.88 KiB
  dist\static\js\chunk-408d3874.164a4fcf    1508.60 KiB      500.21 KiB
  .js
  dist\static\js\chunk-elementUI.98d8dfd    675.26 KiB       166.56 KiB
  0.js
  dist\static\js\chunk-a6b42588.bebc5096    307.67 KiB       71.24 KiB
  .js
  dist\static\js\app.74fd8561.js            195.20 KiB       64.59 KiB
  dist\static\js\chunk-7ef2f1aa.4e1f9279    85.30 KiB        26.02 KiB
  .js
  dist\static\js\chunk-438dae0e.d73eb72a    24.80 KiB        9.25 KiB
  .js
  dist\static\js\chunk-4071e530.7bda46b4    20.26 KiB        5.83 KiB
  .js
  dist\static\js\chunk-56f1db2e.a0051723    20.00 KiB        5.70 KiB
  .js
  dist\static\js\chunk-56c1d4b3.62c9772e    5.50 KiB         2.21 KiB
  .js
  dist\static\js\chunk-e2e2b866.79325294    1.54 KiB         0.73 KiB
  .js
  dist\static\js\chunk-df1ff892.4ed5d48e    1.39 KiB         0.80 KiB
  .js
  dist\static\js\chunk-2d230834.9c7f6c73    0.36 KiB         0.27 KiB
  .js
  dist\static\css\app.f957a9d3.css          255.85 KiB       39.07 KiB
  dist\static\css\chunk-408d3874.00f359c    33.19 KiB        6.44 KiB
  2.css
  dist\static\css\chunk-438dae0e.79c947a    16.06 KiB        2.21 KiB
  7.css
  dist\static\css\chunk-a6b42588.b3fc20a    14.27 KiB        3.03 KiB
  6.css
  dist\static\css\chunk-libs.6f07664f.cs    5.75 KiB         1.87 KiB
  s
  dist\static\css\chunk-e2e2b866.cfe6404    4.64 KiB         0.83 KiB
  a.css
  dist\static\css\chunk-4071e530.9b1e801    3.22 KiB         0.80 KiB
  d.css
  dist\static\css\chunk-df1ff892.73d0e5d    0.73 KiB         0.29 KiB
  e.css
  dist\static\css\chunk-56c1d4b3.3fb1aad    0.66 KiB         0.33 KiB
  a.css
  dist\static\css\chunk-56f1db2e.c6ced85    0.24 KiB         0.17 KiB
  e.css

  Images and other types of assets omitted.

 DONE  Build complete. The dist directory is ready to be deployed.
 INFO  Check out deployment instructions at https://cli.vuejs.org/guide/deployment.html
```

nginx部署前端文件：

nginx.conf:

```
#user  nobody;
worker_processes  1;

#error_log  logs/error.log;
#error_log  logs/error.log  notice;
#error_log  logs/error.log  info;

#pid        logs/nginx.pid;


events {
    worker_connections  1024;
}


http {
    include       mime.types;
    default_type  application/octet-stream;
    sendfile        on;
    keepalive_timeout  65;

    server {
        listen       80;
        server_name  localhost;
        location / {
            root   D:/nginx-1.18.0/nginx-1.18.0/dist;
            index  index.html;
        }
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   html;
        }
    }
}
```

3, 验证

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/10.png)

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/11.png)

## 六，部署dashboard 

当前部署dashboard版本:v2.2.0,注意检查dashboard版本与kubernetes版本兼容性

```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.2.0/aio/deploy/recommended.yaml
```

#或者下载yaml文件手动修改service部分

```
spec:  type: NodePort  ports:    - port: 443      targetPort: 8443      nodePort: 30443  selector:    k8s-app: kubernetes-dashboard
```

访问

```
https://192.168.31.243:30443/
```

创建登陆用户

```
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kubernetes-dashboard
```

操作：

```
kubectl apply -f dashboard-adminuser.yaml
```


说明：上面创建了一个叫admin-user的服务账号，并放在kubernetes-dashboard 命名空间下，并将cluster-admin角色绑定到admin-user账户，这样admin-user账户就有了管理员的权限。默认情况下，kubeadm创建集群时已经创建了cluster-admin角色，我们直接绑定即可。

查看admin-user账户的token

```
kubectl -n kubernetes-dashboard describe secret $(kubectl -n kubernetes-dashboard get secret | grep admin-user | awk '{print $1}')
```

把获取到的Token复制到登录界面的Token输入框中，成功登陆dashboard

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/12.png)

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/13.png)

通过ingress方式将dashboard暴露到集群外是更好的选择，需要自行部署，参考：

 trafik

contour

nginx-ingress

metallb

### dashboard超时

默认dashboard登录超时时间是15min，可以为dashboard容器增加-- token-ttl参数自定义超时时间： 参考： https://github.com/kubernetes/dashboard/blob/master/docs/common/dashboard-arguments.md

修改yaml配置超时时间12h:

```
 more recommended.yaml...          args:            - --auto-generate-certificates            - --namespace=kubernetes-dashboard            - --token-ttl=43200...
更新配置:
```

 kubectl apply -f recommended.yaml
其他说明:

整个dashboard可以对大部分资源进行性能监控，修改和删除操作，可自行体验

dashboard支持删除node节点，可以选择cluster，node列表中执行操作

dashboard支持暗黑模式，可以在settings中设置



七 部署集群监控Prometheus&Grafana
-----------------------------------
Kube-promethues 版本： 0.7.0

Kubernetes 版本： 1.20

由于它的文件都存放在项目源码的 manifests 文件夹下，所以需要进入其中进行启动这些 kubernetes 应用 yaml 文件。又由于这些文件堆放在一起，不利于分类启动，所以这里将它们分类。

 Prometheus Operator 源码

```
wget https://github.com/coreos/kube-prometheus/archive/v0.7.0.tar.gz
```

解压

```
tar -zxvf v0.6.0.tar.gz
```

进入源码的 manifests 文件夹：

```
cd kube-prometheus-0.7.0/manifests/
```

创建文件夹并且将 yaml 文件分类：

```
# 创建文件夹
mkdir -p node-exporter alertmanager grafana kube-state-metrics prometheus serviceMonitor adapter
# 移动 yaml 文件，进行分类到各个文件夹下
mv *-serviceMonitor* serviceMonitor/
mv grafana-* grafana/
mv kube-state-metrics-* kube-state-metrics/
mv alertmanager-* alertmanager/
mv node-exporter-* node-exporter/
mv prometheus-adapter* adapter/
mv prometheus-* prometheus/
```

修改Service端口设置

vim prometheus/prometheus-service.yaml

```

apiVersion: v1
kind: Service
metadata:
  labels:
    prometheus: k8s
  name: prometheus-k8s
  namespace: monitoring
spec:
  type: NodePort
  ports:
  - name: web
    port: 9090
    targetPort: web
    nodePort: 32101
  selector:
    app: prometheus
    prometheus: k8s
  sessionAffinity: ClientIP
```

修改 Grafana Service

vim grafana/grafana-service.yaml

```
apiVersion: v1
kind: Service
metadata:
  labels:
    app: grafana
  name: grafana
  namespace: monitoring
spec:
  type: NodePort
  ports:
  - name: http
    port: 3000
    targetPort: http
    nodePort: 32102
  selector:
    app: grafana
```

安装Prometheus Operator

```
kubectl apply -f setup/
```

这会创建一个名为 monitoring 的命名空间，以及相关的 CRD 资源对象声明和 Prometheus Operator 控制器。前面中我们介绍过 CRD 和 Operator 的使用，当我们声明完 CRD 过后，就可以来自定义资源清单了，但是要让我们声明的自定义资源对象生效就需要安装对应的 Operator 控制器，这里我们都已经安装了，所以接下来就可以来用 CRD 创建真正的自定义资源对象了。其实在 manifests 目录下面的就是我们要去创建的 Prometheus、Alertmanager 以及各种监控对象的资源清单

安装其它组件
没有特殊的定制需求我们可以直接一键安装：

```
 kubectl apply -f adapter/
 kubectl apply -f alertmanager/
 kubectl apply -f node-exporter/
 kubectl apply -f kube-state-metrics/
 kubectl apply -f grafana/
 kubectl apply -f prometheus/
 kubectl apply -f serviceMonitor/
```

查看Prometheus & Grafana

访问http://192.168.31.243:32101/

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/14.png)

访问http://192.168.31.243:32102/

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/15.png)

默认用户名:admin

默认密码:admin

## 八，编写locust脚本

locustflask.py master节点

```
from locust import HttpUser, task, constant,SequentialTaskSet,TaskSet,events
import logging as log
import json

import six
from itertools import chain

from flask import request, Response
from locust import stats as locust_stats, runners as locust_runners
from locust import events
from prometheus_client import Metric, REGISTRY, exposition

# This locustfile adds an external web endpoint to the locust master, and makes it serve as a prometheus exporter.
# Runs it as a normal locustfile, then points prometheus to it.
# locust -f prometheus_exporter.py --master

# Lots of code taken from [mbolek's locust_exporter](https://github.com/mbolek/locust_exporter), thx mbolek!


class LocustCollector(object):
    registry = REGISTRY

    def __init__(self, environment, runner):
        self.environment = environment
        self.runner = runner

    def collect(self):
        # collect metrics only when locust runner is spawning or running.
        runner = self.runner

        if runner and runner.state in (locust_runners.STATE_SPAWNING, locust_runners.STATE_RUNNING):
            stats = []
            for s in chain(locust_stats.sort_stats(runner.stats.entries), [runner.stats.total]):
                stats.append({
                    "method": s.method,
                    "name": s.name,
                    "num_requests": s.num_requests,
                    "num_failures": s.num_failures,
                    "avg_response_time": s.avg_response_time,
                    "min_response_time": s.min_response_time or 0,
                    "max_response_time": s.max_response_time,
                    "current_rps": s.current_rps,
                    "median_response_time": s.median_response_time,
                    "ninetieth_response_time": s.get_response_time_percentile(0.9),
                    # only total stats can use current_response_time, so sad.
                    # "current_response_time_percentile_95": s.get_current_response_time_percentile(0.95),
                    "avg_content_length": s.avg_content_length,
                    "current_fail_per_sec": s.current_fail_per_sec
                })

            # perhaps StatsError.parse_error in e.to_dict only works in python slave, take notices!
            errors = [e.to_dict() for e in six.itervalues(runner.stats.errors)]

            metric = Metric('locust_user_count', 'Swarmed users', 'gauge')
            metric.add_sample('locust_user_count', value=runner.user_count, labels={})
            yield metric

            metric = Metric('locust_errors', 'Locust requests errors', 'gauge')
            for err in errors:
                metric.add_sample('locust_errors', value=err['occurrences'],
                                  labels={'path': err['name'], 'method': err['method'],
                                          'error': err['error']})
            yield metric

            is_distributed = isinstance(runner, locust_runners.MasterRunner)
            if is_distributed:
                metric = Metric('locust_slave_count', 'Locust number of slaves', 'gauge')
                metric.add_sample('locust_slave_count', value=len(runner.clients.values()), labels={})
                yield metric

            metric = Metric('locust_fail_ratio', 'Locust failure ratio', 'gauge')
            metric.add_sample('locust_fail_ratio', value=runner.stats.total.fail_ratio, labels={})
            yield metric

            metric = Metric('locust_state', 'State of the locust swarm', 'gauge')
            metric.add_sample('locust_state', value=1, labels={'state': runner.state})
            yield metric

            stats_metrics = ['avg_content_length', 'avg_response_time', 'current_rps', 'current_fail_per_sec',
                             'max_response_time', 'ninetieth_response_time', 'median_response_time',
                             'min_response_time',
                             'num_failures', 'num_requests']

            for mtr in stats_metrics:
                mtype = 'gauge'
                if mtr in ['num_requests', 'num_failures']:
                    mtype = 'counter'
                metric = Metric('locust_stats_' + mtr, 'Locust stats ' + mtr, mtype)
                for stat in stats:
                    # Aggregated stat's method label is None, so name it as Aggregated
                    # locust has changed name Total to Aggregated since 0.12.1
                    if 'Aggregated' != stat['name']:
                        metric.add_sample('locust_stats_' + mtr, value=stat[mtr],
                                          labels={'path': stat['name'], 'method': stat['method']})
                    else:
                        metric.add_sample('locust_stats_' + mtr, value=stat[mtr],
                                          labels={'path': stat['name'], 'method': 'Aggregated'})
                yield metric


# prometheus监听端口
@events.init.add_listener
def locust_init(environment, runner, **kwargs):
    print("locust init event received")
    if environment.web_ui and runner:
        @environment.web_ui.app.route("/export/prometheus")
        def prometheus_exporter():
            registry = REGISTRY
            encoder, content_type = exposition.choose_encoder(request.headers.get('Accept'))
            if 'name[]' in request.args:
                registry = REGISTRY.restricted_registry(request.args.get('name[]'))
            body = encoder(registry)
            return Response(body, content_type=content_type)

        REGISTRY.register(LocustCollector(environment, runner))

@events.test_start.add_listener
def on_start(**kwargs):
    log.info("A test will start...")

@events.test_stop.add_listener
def on_stop(**kwargs):
    log.info("A test is ending...")

# 该类中的任务执行顺序是 index ---> login  Task 可以加到类上
WEB_HEADER = None

# 无序并发任务
class SetTask(TaskSet):
    @task(1)
    def getLogDetail(self):
        deatil_url = "/auth/online?page=0&size=10&sort=id%2Cdesc"
        with self.client.request(method='GET',
                                 url=deatil_url,
                                 headers=WEB_HEADER,
                                 name='获取日志详情') as response:
            log.info(response.text)
    @task
    def stop(self):
        self.interrupt()
# 有序并发任务
class FlaskTask(SequentialTaskSet): #该类下没有智能提示
    # 登录获取 token，拼接后续请求头
    def on_start(self):
        res = self.client.request(method='GET', url="/auth/code",name="获取验证码")
        uuid = res.json()['uuid']
        headers = {
            "content-type": "application/json;charset=UTF-8",
        }
        datda_info = {
            "code": "15",
            "password": "B0GdcVWB+XtTwsyBjzoRkn8VnSgtPVKpl8mp7AuQ+BTeU030grUkRwmOHXFCjEhKXB7yezBS7dFEJ63ykR2piQ==",
            "username": "admin",
            "uuid": uuid
        }
        with self.client.request(method='POST',url="/auth/login", headers=headers, catch_response=True,data=json.dumps(datda_info),name="获取token") as response:
            self.token = response.json()['token']
            if response.status_code == 200:
                self.token = response.json()['token']
                response.success()
            else:
                response.failure("获取token失败")
            global WEB_HEADER
            WEB_HEADER = {
                "Authorization": self.token
            }
    #嵌套无序并发任务
    tasks = [SetTask]
    @task #关联登录成功后的token，也即 前一个业务返回的业务需要传递给后续的请求
    def getUserDetail(self):
        deatil_url = "/api/dictDetail?dictName=user_status&page=0&size=9999"
        with self.client.request(method='GET',
                                 url=deatil_url,
                                 headers=WEB_HEADER,
                                 name='获取用户详情') as response:
            log.info(response.text)

def function_task():
    log.info("This is the function task")

class FlaskUser(HttpUser):
    host = 'http://192.168.31.243:30080'  # 设置根地址
    wait_time = constant(1)  # 每次请求的延时时间
    #wait_time = between(1,3)  # 等待时间1~3s
    tasks = [FlaskTask] # 指定测试任务
```

locustflask.py worker 节点

```
from locust import HttpUser, task, constant,SequentialTaskSet,TaskSet,events
import logging as log
import json

import six
from itertools import chain

from flask import request, Response
from locust import stats as locust_stats, runners as locust_runners
from locust import events
from prometheus_client import Metric, REGISTRY, exposition

# This locustfile adds an external web endpoint to the locust master, and makes it serve as a prometheus exporter.
# Runs it as a normal locustfile, then points prometheus to it.
# locust -f prometheus_exporter.py --master

# Lots of code taken from [mbolek's locust_exporter](https://github.com/mbolek/locust_exporter), thx mbolek!


class LocustCollector(object):
    registry = REGISTRY

    def __init__(self, environment, runner):
        self.environment = environment
        self.runner = runner

    def collect(self):
        # collect metrics only when locust runner is spawning or running.
        runner = self.runner

        if runner and runner.state in (locust_runners.STATE_SPAWNING, locust_runners.STATE_RUNNING):
            stats = []
            for s in chain(locust_stats.sort_stats(runner.stats.entries), [runner.stats.total]):
                stats.append({
                    "method": s.method,
                    "name": s.name,
                    "num_requests": s.num_requests,
                    "num_failures": s.num_failures,
                    "avg_response_time": s.avg_response_time,
                    "min_response_time": s.min_response_time or 0,
                    "max_response_time": s.max_response_time,
                    "current_rps": s.current_rps,
                    "median_response_time": s.median_response_time,
                    "ninetieth_response_time": s.get_response_time_percentile(0.9),
                    # only total stats can use current_response_time, so sad.
                    # "current_response_time_percentile_95": s.get_current_response_time_percentile(0.95),
                    "avg_content_length": s.avg_content_length,
                    "current_fail_per_sec": s.current_fail_per_sec
                })

            # perhaps StatsError.parse_error in e.to_dict only works in python slave, take notices!
            errors = [e.to_dict() for e in six.itervalues(runner.stats.errors)]

            metric = Metric('locust_user_count', 'Swarmed users', 'gauge')
            metric.add_sample('locust_user_count', value=runner.user_count, labels={})
            yield metric

            metric = Metric('locust_errors', 'Locust requests errors', 'gauge')
            for err in errors:
                metric.add_sample('locust_errors', value=err['occurrences'],
                                  labels={'path': err['name'], 'method': err['method'],
                                          'error': err['error']})
            yield metric

            is_distributed = isinstance(runner, locust_runners.MasterRunner)
            if is_distributed:
                metric = Metric('locust_slave_count', 'Locust number of slaves', 'gauge')
                metric.add_sample('locust_slave_count', value=len(runner.clients.values()), labels={})
                yield metric

            metric = Metric('locust_fail_ratio', 'Locust failure ratio', 'gauge')
            metric.add_sample('locust_fail_ratio', value=runner.stats.total.fail_ratio, labels={})
            yield metric

            metric = Metric('locust_state', 'State of the locust swarm', 'gauge')
            metric.add_sample('locust_state', value=1, labels={'state': runner.state})
            yield metric

            stats_metrics = ['avg_content_length', 'avg_response_time', 'current_rps', 'current_fail_per_sec',
                             'max_response_time', 'ninetieth_response_time', 'median_response_time',
                             'min_response_time',
                             'num_failures', 'num_requests']

            for mtr in stats_metrics:
                mtype = 'gauge'
                if mtr in ['num_requests', 'num_failures']:
                    mtype = 'counter'
                metric = Metric('locust_stats_' + mtr, 'Locust stats ' + mtr, mtype)
                for stat in stats:
                    # Aggregated stat's method label is None, so name it as Aggregated
                    # locust has changed name Total to Aggregated since 0.12.1
                    if 'Aggregated' != stat['name']:
                        metric.add_sample('locust_stats_' + mtr, value=stat[mtr],
                                          labels={'path': stat['name'], 'method': stat['method']})
                    else:
                        metric.add_sample('locust_stats_' + mtr, value=stat[mtr],
                                          labels={'path': stat['name'], 'method': 'Aggregated'})
                yield metric


# prometheus监听端口
@events.init.add_listener
def locust_init(environment, runner, **kwargs):
    print("locust init event received")
    if environment.web_ui and runner:
        @environment.web_ui.app.route("/export/prometheus")
        def prometheus_exporter():
            registry = REGISTRY
            encoder, content_type = exposition.choose_encoder(request.headers.get('Accept'))
            if 'name[]' in request.args:
                registry = REGISTRY.restricted_registry(request.args.get('name[]'))
            body = encoder(registry)
            return Response(body, content_type=content_type)

        REGISTRY.register(LocustCollector(environment, runner))

@events.test_start.add_listener
def on_start(**kwargs):
    log.info("A test will start...")

@events.test_stop.add_listener
def on_stop(**kwargs):
    log.info("A test is ending...")

# 该类中的任务执行顺序是 index ---> login  Task 可以加到类上
WEB_HEADER = None

# 无序并发任务
class SetTask(TaskSet):
    @task(1)
    def getLogDetail(self):
        deatil_url = "/auth/online?page=0&size=10&sort=id%2Cdesc"
        with self.client.request(method='GET',
                                 url=deatil_url,
                                 headers=WEB_HEADER,
                                 name='获取日志详情') as response:
            log.info(response.text)
    @task
    def stop(self):
        self.interrupt()
# 有序并发任务
class FlaskTask(SequentialTaskSet): #该类下没有智能提示
    # 登录获取 token，拼接后续请求头
    def on_start(self):
        res = self.client.request(method='GET', url="/auth/code",name="获取验证码")
        uuid = res.json()['uuid']
        headers = {
            "content-type": "application/json;charset=UTF-8",
        }
        datda_info = {
            "code": "15",
            "password": "B0GdcVWB+XtTwsyBjzoRkn8VnSgtPVKpl8mp7AuQ+BTeU030grUkRwmOHXFCjEhKXB7yezBS7dFEJ63ykR2piQ==",
            "username": "admin",
            "uuid": uuid
        }
        with self.client.request(method='POST',url="/auth/login", headers=headers, catch_response=True,data=json.dumps(datda_info),name="获取token") as response:
            self.token = response.json()['token']
            if response.status_code == 200:
                self.token = response.json()['token']
                response.success()
            else:
                response.failure("获取token失败")
            global WEB_HEADER
            WEB_HEADER = {
                "Authorization": self.token
            }
    #嵌套无序并发任务
    tasks = [SetTask]
    @task #关联登录成功后的token，也即 前一个业务返回的业务需要传递给后续的请求
    def getUserDetail(self):
        deatil_url = "/api/dictDetail?dictName=user_status&page=0&size=9999"
        with self.client.request(method='GET',
                                 url=deatil_url,
                                 headers=WEB_HEADER,
                                 name='获取用户详情') as response:
            log.info(response.text)

def function_task():
    log.info("This is the function task")

class FlaskUser(HttpUser):
    host = 'http://192.168.31.243:30080'  # 设置根地址
    wait_time = constant(1)  # 每次请求的延时时间
    #wait_time = between(1,3)  # 等待时间1~3s
    tasks = [FlaskTask] # 指定测试任务
```

在worker节点启动master 和 worker

终端1

```
locust -f locustflask.py --master
```

终端2

```
locust -f locustflask.py --worker  --master-host=192.168.31.243
```

### 九，metrics注册到prometheus

prometheus_exporter.yaml

```
apiVersion: v1
kind: Endpoints
metadata:
  name: locust-data
subsets:
- addresses:
  - ip: 192.168.31.243
  ports:
  - port: 8089
    name: locust
---
apiVersion: v1
kind: Service
metadata:
  name: locust-data
  labels:
    app: locust-data
spec:
  ports:
  - port: 8089
    targetPort: 8089
    name: locust
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  labels:
    app: prometheus
    prometheus: prometheus
  name: locust-data
spec:
  endpoints:
  - interval: 1s
    path: /export/prometheus
    targetPort: 8089
    port: locust
  jobLabel: k8s-app
  namespaceSelector:
    matchNames:
    - default
  selector:
    matchLabels:
      app: locust-data
```

操作

```
kubectl apply -f prometheus_exporter.yaml
```

验证

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/15.png)

## 十，prometheus配置到grafana数据源

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/16.png)

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/17.png)

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/18.png)

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/19.png)

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/20.png)

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/21.png)

至此，locust测试的数据就可以用grafana展示了

## 十一，k8s部署locust master worker

master 镜像制作

````
FROM centos_base:v1

RUN mkdir -p /usr/local/locust

WORKDIR /usr/local/locust

COPY locustflask.py  /usr/local/locust/locustflask.py

RUN cd /usr/local/locust && \
    pip3 install locust -i http://pypi.douban.com/simple --trusted-host pypi.douban.com && \
    pip3 install prometheus_client -i http://pypi.douban.com/simple --trusted-host pypi.douban.com && \
    ln -s /usr/local/python3/bin/locust /usr/bin/locust

ENTRYPOINT ["locust","-f","/usr/local/locust/locustflask.py","--master"]
````

操作

```
docker build -t mangseng/locust:master .
docker push  mangseng/locust:master
```



worker 镜像制作

```

FROM centos_base:v1

RUN mkdir -p /usr/local/locust

WORKDIR /usr/local/locust

COPY locustflask.py  /usr/local/locust/locustflask.py

RUN cd /usr/local/locust && \
    pip3 install locust -i http://pypi.douban.com/simple --trusted-host pypi.douban.com && \
    pip3 install prometheus_client -i http://pypi.douban.com/simple --trusted-host pypi.douban.com && \
    ln -s /usr/local/python3/bin/locust /usr/bin/locust
```

操作

```
docker build -t mangseng/locust:worker .
docker push  mangseng/locust:worker
```



部署master

```
kind: Deployment
apiVersion: apps/v1
metadata:
  name: locust-master-controller
  labels:
    k8s-app: locust-master
spec:
  selector:
    matchLabels:
      k8s-app: locust-master
  replicas: 1
  template:
    metadata:
      labels:
        k8s-app: locust-master
        name: locust-master
    spec:
      containers:
        - name: locust-master
          image: mangseng/locust:master
          ports:
            - name: loc-master-web
              containerPort: 8089
              protocol: TCP
            - name: loc-master-p1
              containerPort: 5557
              protocol: TCP

---
kind: Service
apiVersion: v1
metadata:
  name: locust-master
spec:
  type: NodePort
  selector:
    k8s-app: locust-master
  ports:
    - port: 8089
      targetPort: loc-master-web
      nodePort: 32109
      protocol: TCP
      name: loc-master-web
    - port: 5557
      targetPort: loc-master-p1
      protocol: TCP
      name: loc-master-p1

```

操作

```
kubectl apply -f master-deployment.yaml
```

部署worker

```
---
kind: Deployment
apiVersion: apps/v1
metadata:
  name: locust-slave-controller
  labels:
    k8s-app: locust-slave
spec:
  selector:
    matchLabels:
      k8s-app: locust-slave
  replicas: 1
  template:
    metadata:
      labels:
        k8s-app: locust-slave
        name: locust-slave
    spec:
      containers:
        - name: locust-slave
          image: mangseng/locust:worker
          command: ["locust", "-f", "locustflask.py", "--worker","--master-host=locust-master"]
```

操作

```
kubectl apply -f worker-deployment.yaml
```

访问 http://192.168.31.243:32109/ 启动测试

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/22.png)

对接grafana

```
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: locust-metrics
  namespace: monitoring
spec:
  selector:
    matchLabels:
      k8s-app: locust-master
  namespaceSelector:
    matchNames:
    - default
  podMetricsEndpoints:
  - port: loc-master-web
    path: /export/prometheus
```

操作

```
kubectl apply -f prometheus_exporter.yaml
```

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/23.png)

![image](https://github.com/Mountains-and-rivers/k8s-locust/blob/main/images/24.png)



# 参考

https://blog.csdn.net/tfs411082561/article/details/78416569

https://el-admin.vip/pages/010101/

https://blog.51cto.com/forever8/2787167

https://blog.csdn.net/qq_41522024/article/details/123780040

https://www.coder4.com/archives/7491

https://www.programminghunter.com/article/88221818180/

https://testerhome.com/topics/24828

https://cloud.tencent.com/developer/article/1813370

https://www.cnblogs.com/51kata/p/5262301.html

https://www.qikqiak.com/k8strain2/monitor/operator/custom/

https://www.qikqiak.com/k8s-book/docs/59.%E8%87%AA%E5%AE%9A%E4%B9%89Prometheus%20Operator%20%E7%9B%91%E6%8E%A7%E9%A1%B9.html

https://cloud.tencent.com/document/product/1416/55995

https://github.com/myzhan/boomer/blob/master/prometheus_exporter.py

https://www.jianshu.com/p/4340d8e80fdc
