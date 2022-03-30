
FROM centos:8

ADD https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tgz .
RUN  yum install -y libffi-devel zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel zlib zlib-devel gcc make  && \
   mkdir -p /usr/local/python3 && \
   cd Python-3.7.3 && \
   ./configure --prefix=/usr/local/bin/python3 && \
   make && \
   make install && \
   rm -rf /usr/bin/python3 && \
   ln -s /usr/local/bin/python3/bin/python3 /usr/bin/python3
