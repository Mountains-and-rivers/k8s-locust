
FROM centos_base:v1

RUN mkdir -p /usr/local/locust

WORKDIR /usr/local/locust

COPY locustflask.py  /usr/local/locust/locustflask.py

RUN cd /usr/local/locust && \
    pip3 install locust -i http://pypi.douban.com/simple --trusted-host pypi.douban.com && \
    pip3 install prometheus_client -i http://pypi.douban.com/simple --trusted-host pypi.douban.com && \
    ln -s /usr/local/python3/bin/locust /usr/bin/locust

