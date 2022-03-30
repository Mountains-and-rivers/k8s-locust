# 基于k8s+locust+boomer的分布式压力测试方案落地
eladmin部署参考：https://github.com/elunez/eladmin

修改后的代码打包至release中

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
    ./configure --prefix=/usr/local/bin/python3 && \
    make && \
    make install && \
    rm -rf /usr/bin/python3 && \
    ln -s /usr/local/bin/python3/bin/python3 /usr/bin/python3 && \
    rm -rf  Python-3.7.3.tgz && \
    rm -rf  Python-3.7.3
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



