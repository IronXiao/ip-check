#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import re


class Config:
    CONFIG_FILE = "config.txt"
    IP_FILE = 'all.txt'
    THREAD_NUM = 10
    MAX_RETRY = 2
    TIME_OUT = 3
    NAME_SERVER = "icook.tw"
    OUT_FILE = "out.txt"

    envs = []

    def __init__(self):
        self.init_envs()

    def update_configs(self, envs):
        for key, value in envs:
            setattr(self, key, value)

    def init_envs(self):
        self.envs = EnvLoader.load_with_file(self.CONFIG_FILE)
        self.update_configs(self.envs)


REGEX_IPS = re.compile(
    '^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')


def is_ip(str):
    return REGEX_IPS.match(str)


def test_ip_internal(ip, nameserver, timeout):
    url = 'http://' + ip + '/cdn-cgi/trace'
    try:
        with requests.get(
                url, headers={'Host': nameserver}, timeout=timeout) as r:
            if r.status_code == 200:
                check_str = 'h=' + nameserver
                if check_str in r.text:
                    return True
                else:
                    return False
            else:
                return False
    except Exception as e:
        return False


def test_ip(ip, nameserver, timeout, max_retry):
    count = max_retry
    status = test_ip_internal(ip, nameserver, timeout)
    if not status and count > 0:
        count -= 1
        status = test_ip_internal(ip, nameserver, timeout)
    print("测试ip", ip, "可用" if status else "不可用")
    return ip if status else None


def read_all_ips_form_file(path):
    all_ips = []
    with open(path, 'r') as f:
        for line in f.readlines():
            if is_ip(line.strip()):
                all_ips.append(line.strip())
    all_ips = list(dict.fromkeys(all_ips))
    print("读取到%d 个ip" % len(all_ips))
    return all_ips


def test_ips(all_ips=[], max_thread_count=10, nameserver="icook.tw", timeout=3, max_retry=1):
    if all_ips:
        print('开始测试...')
        thread_pool_executor = ThreadPoolExecutor(
            max_workers=max_thread_count, thread_name_prefix="test_")
        all_task = [thread_pool_executor.submit(
            test_ip, ip, nameserver, timeout, max_retry) for ip in all_ips]
        passed_ips = []
        for future in as_completed(all_task):
            ret = future.result()
            if ret:
                passed_ips.append(ret)
        thread_pool_executor.shutdown(wait=True)
        return passed_ips


def main():
    config = Config()
    print("当前配置文件为%s" % config.IP_FILE)
    all_ips = read_all_ips_form_file(eval("r" + "'" + config.IP_FILE + "'"))
    passed_ips = test_ips(all_ips, config.THREAD_NUM,
                          config.NAME_SERVER, config.TIME_OUT, config.MAX_RETRY)
    if passed_ips:
        with open(config.OUT_FILE, 'w') as f:
            for ip in passed_ips:
                f.write(ip)
                f.write('\n')
        print('测试通过%d个ip 已导出到' % len(passed_ips), config.OUT_FILE)
    else:
        print("没有筛选到可用ip")


class EnvLoader:
    envs = []

    def __init__(self):
        self.envs = []

    @classmethod
    def load_with_file(cls, file):
        self = cls()
        if os.path.exists(file):
            env_content = open(file, encoding='utf8').read()
            content = re.sub(r'^([A-Z]+)_', r'self.\1_',
                             env_content, flags=re.M)
            exec(content)
        return self.envs

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if re.search(r'^[A-Z]+_', key):
            self.envs.append(([key, value]))


if __name__ == '__main__':
    main()
