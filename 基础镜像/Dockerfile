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