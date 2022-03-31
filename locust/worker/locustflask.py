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
            log.info("11111111111111111111111111111111111")
            #log.info(response.text)
    @task
    def stop(self):
        log.info("33333333333333333333333333333333")
        self.interrupt()
# 有序序并发任务
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
            log.info("22222222222222222222222222222222222222")
            log.info(response.text)

def function_task():
    log.info("This is the function task")

class FlaskUser(HttpUser):
    host = 'http://192.168.31.243:30080'  # 设置根地址
    wait_time = constant(1)  # 每次请求的延时时间
    #wait_time = between(1,3)  # 等待时间1~3s
    tasks = [FlaskTask] # 指定测试任务

