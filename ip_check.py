#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import zipfile
from config import Config
import ipaddress
#import pycurl

g_config = Config()

REGEX_IPS = re.compile(
    '^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')


def is_ip(ip_str):
    return REGEX_IPS.match(ip_str)


REGEX_IP_NETWORK = re.compile(
    r'^(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\/([1-9]|[1-2]\d|3[0-2])$')


def is_ip_network(ip_str):
    return REGEX_IP_NETWORK.match(ip_str)


def gen_ip_form_network(ip_str):
    net = ipaddress.ip_network(ip_str)
    hosts = list(net.hosts())
    all_ips = [str(ip) for ip in hosts]
    return all_ips


#def check_speed(ip):
#    with open(g_config.TEST_DOWNLOAD_SAVE_FILE, 'wb') as f:
#        curl = pycurl.Curl()
#        curl.setopt(curl.URL, g_config.TEST_DOWNLOAD_FILE_LINK)
#        curl.setopt(curl.TIMEOUT, g_config.TEST_DOWNLOAD_TIMEOUT)
#        curl.setopt(curl.CONNECTTIMEOUT, g_config.TEST_DOWNLOAD_CONNECTTIMEOUT)
#        curl.setopt(curl.USERAGENT, g_config.USER_AGENT)
#        curl.setopt(curl.IPRESOLVE, curl.IPRESOLVE_V4)
#        curl.setopt(curl.RESOLVE, ['{}:{}:{}'.format(
#            g_config.TEST_DOWNLOAD_DOMAIN, g_config.TEST_DOWNLOAD_DOMAIN_PORT, ip)])
#        curl.setopt(curl.WRITEDATA, f)
#        try:
#            curl.perform()
#        except Exception:
#            pass
#        speed = int(curl.getinfo(curl.SPEED_DOWNLOAD) / 1024)
#        print('  {} 平均下载速度为: {} kB/s'.format(ip, speed))
#        curl.close()
#        if speed > g_config.EXPECTED_SPEED:
#            return True, speed
#        return False, -1


def find_txt_in_dir(dir):
    L = []
    if os.path.isdir(dir):
        for f in os.listdir(dir):
            file = os.path.join(dir, f)
            if os.path.isfile(file) and file.endswith('.txt'):
                L.append(file)
    return L


def filter_ip_valid_internal(ip, nameserver, timeout):
    url = g_config.NS_TEST_SERVER.format(ip)
    try:
        with requests.get(
                url, headers={'Host': nameserver}, timeout=timeout) as r:
            if r.status_code == 200:
                if g_config.NS_TEST_RESPONSE in r.text:
                    return True
                else:
                    return False
            else:
                return False
    except Exception as e:
        return False


def test_ip(ip, nameserver, timeout, max_retry):
    count = max_retry
    status = filter_ip_valid_internal(ip, nameserver, timeout)
    if not status and count > 0:
        count -= 1
        status = filter_ip_valid_internal(ip, nameserver, timeout)
    return ip if status else None


def read_all_ips_form_file(file):
    all_ips = []
    if zipfile.is_zipfile(file):
        all_ips = read_all_ips_form_zipfile(file)
    else:
        with open(file, 'r') as f:
            for line in f.readlines():
                if is_ip(line.strip()):
                    all_ips.append(line.strip())
                elif is_ip_network(line.strip()):
                    all_ips += gen_ip_form_network(line.strip())
    all_ips = list(dict.fromkeys(all_ips))
    # print("在%s中读取到:" % file, "%d 个ip" % len(all_ips))
    return all_ips


def read_all_ips_form_zipfile(file):
    if zipfile.is_zipfile(file):
        zip = zipfile.PyZipFile(file)
        fns_in_zip = zip.namelist()
        txt_files = []
        ip_list = []
        for fn in fns_in_zip:
            if fn.endswith('.txt'):
                txt_files.append(fn)
        if txt_files:
            for txt_file in txt_files:
                try:
                    with zip.open(txt_file) as f:
                        ip = f.readline().decode('utf-8').strip()
                        while ip and is_ip(ip):
                            ip_list.append(ip)
                            ip = f.readline().decode('utf-8').strip()
                except Exception:
                    pass
        ip_list = list(dict.fromkeys(ip_list))
        print("从%s" % file, "\b读取到%d个ip" % len(ip_list))
        return ip_list

    all_ips = []
    with open(file, 'r') as f:
        for line in f.readlines():
            if is_ip(line.strip()):
                all_ips.append(line.strip())
    all_ips = list(dict.fromkeys(all_ips))
    # print("在%s中读取到:" % file, "%d 个ip" % len(all_ips))
    return all_ips


def filter_ip_by_num(all_ips, num):
    if (num > len(all_ips)):
        return all_ips
    indexes = random.sample(range(0, len(all_ips)), num)
    np_all_ips = np.array(all_ips)
    all_ips = np_all_ips[indexes]
    all_ips = [str(i) for i in all_ips]
    return all_ips


def read_all_ips_form_path(path):
    all_ip_files = []
    all_ips = []
    if os.path.isdir(os.path.abspath(path)):
        all_ip_files = find_txt_in_dir(path)
    else:
        all_ip_files.append(path)
    for file in all_ip_files:
        all_ips += read_all_ips_form_file(file)
    all_ips = list(dict.fromkeys(all_ips))
    print("#######共计读取到%d 个ip" % len(all_ips))
    if len(all_ips) > g_config.MAX_FILTER_VALID_IP_COUNT:
        print('ip过多,随机挑选{}个测试可用性'.format(g_config.MAX_FILTER_VALID_IP_COUNT))
        all_ips = filter_ip_by_num(all_ips, g_config.MAX_FILTER_VALID_IP_COUNT)
    return all_ips


def filter_valid_ips(all_ips=[], max_thread_count=10, nameserver="icook.tw", timeout=3, max_retry=1):
    if all_ips:
        print('检测ip 可用性... ...')
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


def write_valid_ips_to_file(passed_ips):
    if passed_ips:
        with open(g_config.VALID_IP_FILE, 'w') as f:
            for ip in passed_ips:
                f.write(ip)
                f.write('\n')
        print('测试通过%d个ip 已导出到' % len(passed_ips), g_config.VALID_IP_FILE)
    else:
        print("没有筛选到可用ip")


def write_better_ips_to_file(better_ips):
    if better_ips:
        print('优选ip为:')
        with open(g_config.BETTER_IP_FILE, 'w') as f:
            for ip, speed in better_ips:
                print('    {}: {} kB/s'.format(ip, speed))
                f.write('{}: {} kB/s'.format(ip, speed))
                f.write('\n')
        print('测试通过%d个优选ip 已导出到' % len(better_ips), g_config.BETTER_IP_FILE)
    else:
        print("没有筛选到优选ip")


def filter_better_ip(ips):
    better_ips = {}
    for i in range(0, len(ips)):
        print('正在测速第{}/{}个ip: {}'.format(i+1, len(ips), ips[i]))
        status, speed = check_speed(ips[i])
        if status:
            better_ips[ips[i]] = speed
    return better_ips


def main():
    print("当前IP列表文件为%s" % g_config.IP_FILE)
    all_ips = read_all_ips_form_path(g_config.IP_FILE)
    passed_ips = filter_valid_ips(all_ips, g_config.THREAD_NUM,
                                  g_config.NAME_SERVER, g_config.TIME_OUT, g_config.MAX_RETRY)
    if len(passed_ips) > g_config.MAX_FILTER_BETTER_IP_COUNT:
        print('可用ip 太多，随机挑选{}个'.format(g_config.MAX_FILTER_BETTER_IP_COUNT))
        passed_ips = filter_ip_by_num(
            passed_ips, g_config.MAX_FILTER_BETTER_IP_COUNT)
    write_valid_ips_to_file(passed_ips)
    if not g_config.TEST_DOWNLOAD_SPEED:
        return
    good_ips = filter_better_ip(passed_ips)
    good_ips = sorted(good_ips.items(), key=lambda kv: kv[1], reverse=True)
    write_better_ips_to_file(good_ips)


if __name__ == '__main__':
    main()
