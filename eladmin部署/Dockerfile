
FROM centos_base:v1

RUN mkdir -p /usr/local/test

COPY eladmin-system-2.6.jar  /usr/local/test/app.jar

ENTRYPOINT ["java","-jar","/usr/local/test/app.jar"]
