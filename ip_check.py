#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import sys
import threading
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import zipfile
from config import Config
import ipaddress
import urllib3
import time

g_config = Config()
g_lock = threading.Lock()

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


def thread_sync(fn):
    def fn_do(*args, **kw):
        g_lock.acquire()
        fn(*args, **kw)
        g_lock.release()
    return fn_do


def check_speed(ip):
    size = 0
    download_exit = False
    speed = 0
    stop_signal = False

    def download():
        nonlocal download_exit
        pool = urllib3.HTTPSConnectionPool(
            ip, assert_hostname=g_config.TEST_DOWNLOAD_DOMAIN, server_hostname=g_config.TEST_DOWNLOAD_DOMAIN)
        try:
            r = pool.urlopen('GET', g_config.TEST_DOWNLOAD_FILE_PATH,
                             headers={'Host': g_config.TEST_DOWNLOAD_DOMAIN}, assert_same_host=False,
                             timeout=g_config.TEST_DOWNLOAD_CONNECTTIMEOUT, preload_content=False, retries=g_config.MAX_RETRY)
            nonlocal size
            for chunk in r.stream():
                size += len(chunk)
                if stop_signal:
                    break
            r.release_conn()
        except KeyboardInterrupt:
            os._exit(0)
        except:
            pass
        download_exit = True

    def cal_speed():
        nonlocal speed, size, stop_signal
        original_start = time.time()
        start = time.time()
        old_size = size
        while not download_exit:
            time.sleep(0.1)
            end = time.time()
            if end - start > 0.9:
                cur_size = size
                speed_now = int((cur_size - old_size) / ((end - start) * 1024))
                start = end
                old_size = cur_size
                if speed_now > speed:
                    speed = speed_now
            if end - original_start > g_config.TEST_DOWNLOAD_TIMEOUT:
                stop_signal = True
                break

    t1 = threading.Thread(target=download)
    t2 = threading.Thread(target=cal_speed)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    return speed


def download_file_from_net(url, save_path):
    proxies = {}
    if g_config.PROXY:
        proxies = {
            'http': g_config.PROXY,
            'https': g_config.PROXY,
        }
    print('?????????????????????{}'.format(proxies))
    try:
        r = requests.get(url, stream=True,
                         timeout=g_config.TEST_DOWNLOAD_CONNECTTIMEOUT, proxies=proxies)
        with open(save_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)
        r.close()
    except KeyboardInterrupt:
        os._exit(0)
    except:
        return False
    return True


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
    check_h = g_config.NS_TEST_RESPONSE.format(g_config.NAME_SERVER)
    try:
        with requests.get(
                url, headers={'Host': nameserver}, timeout=timeout) as r:
            if r.status_code == 200:
                if check_h in r.text:
                    return True
                else:
                    return False
            else:
                return False
    except KeyboardInterrupt:
        os._exit(0)
    except Exception as e:
        return False


@thread_sync
def print_msg_sync(str):
    print(str)


def check_rtt(ip):
    url = g_config.NS_TEST_SERVER.format(ip)
    times = []
    count = 0
    while count < g_config.RTT_TEST_TIMES:
        try:
            with requests.get(url, headers={'Host': g_config.RTT_TEST_HOST}, timeout=g_config.RTT_TEST_TIMEOUT) as r:
                if r.status_code == 200:
                    times.append(r.elapsed.total_seconds()*1000)
                else:
                    return None, -1
        except KeyboardInterrupt:
            os._exit(0)
        except Exception:
            return None, -1
        count += 1
    t = int(sum(times)/len(times))
    return ip, t


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
    # print("???%s????????????:" % file, "%d ???ip" % len(all_ips))
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
        return ip_list

    all_ips = []
    with open(file, 'r') as f:
        for line in f.readlines():
            if is_ip(line.strip()):
                all_ips.append(line.strip())
    all_ips = list(dict.fromkeys(all_ips))
    # print("???%s????????????:" % file, "%d ???ip" % len(all_ips))
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
    if not os.path.exists(path):
        print(path, '??????????????????????????????')
        os._exit(0)
    all_ip_files = []
    all_ips = []
    if os.path.isdir(os.path.abspath(path)):
        all_ip_files = find_txt_in_dir(path)
    else:
        all_ip_files.append(path)
    for file in all_ip_files:
        all_ips += read_all_ips_form_file(file)
    all_ips = list(dict.fromkeys(all_ips))
    return all_ips


def filter_valid_ips(all_ips=[], max_thread_count=10, nameserver=g_config.NAME_SERVER, timeout=3, max_retry=1):
    passed_ips = []
    if all_ips:
        print('??????ip?????????, ?????????{}'.format(len(all_ips)))
        thread_pool_executor = ThreadPoolExecutor(
            max_workers=max_thread_count, thread_name_prefix="valid_")
        all_task = [thread_pool_executor.submit(
            test_ip, ip, nameserver, timeout, max_retry) for ip in all_ips]
        for future in as_completed(all_task):
            ret = future.result()
            if ret:
                passed_ips.append(ret)
        thread_pool_executor.shutdown(wait=True)
    print('??????????????????: ??????{}, {} pass'.format(len(all_ips), len(passed_ips)))
    return passed_ips


def filter_ips_by_rtt(all_ips=[]):
    passed_ips = []
    if all_ips:
        print('??????ip rtt, ?????????{}'.format(len(all_ips)))
        thread_pool_executor = ThreadPoolExecutor(
            max_workers=g_config.RTT_TEST_MAX_THREAD_NUM, thread_name_prefix="rtt_")
        all_task = [thread_pool_executor.submit(
            check_rtt, ip) for ip in all_ips]
        for future in as_completed(all_task):
            ip, rtt = future.result()
            if ip:
                print('{} ??????????????? {} ms'.format(ip, rtt))
                if rtt < g_config.RTT_ALLOWED_TIMEOUT:
                    passed_ips.append(ip)
        thread_pool_executor.shutdown(wait=True)
    print('RTT?????????: ??????{}, {} pass'.format(len(all_ips), len(passed_ips)))
    return passed_ips


def write_valid_ips_to_file(passed_ips):
    if passed_ips:
        with open(g_config.VALID_IP_FILE, 'w') as f:
            for ip in passed_ips:
                f.write(ip)
                f.write('\n')
        print('????????????%d???ip ????????????' % len(passed_ips), g_config.VALID_IP_FILE)
    else:
        print("?????????????????????ip")


def write_better_ips_to_file(better_ips):
    if better_ips:
        print('??????ip???:')
        with open(g_config.BETTER_IP_FILE, 'w') as f:
            for ip, speed in better_ips:
                print('    {}: {} kB/s'.format(ip, speed))
                f.write('{}: {} kB/s'.format(ip, speed))
                f.write('\n')
        print('????????????%d?????????ip ????????????' % len(better_ips), g_config.BETTER_IP_FILE)
    else:
        print("?????????????????????ip")


def filter_better_ip(ips):
    better_ips = {}
    for i in range(0, len(ips)):
        print('???????????????{}/{}???ip: {}'.format(i+1, len(ips), ips[i]))
        speed = check_speed(ips[i])
        print('{} ??????????????? {} kB/s'.format(ips[i], speed))
        if speed > g_config.EXPECTED_SPEED:
            better_ips[ips[i]] = speed
    return better_ips


def help():
    print('Usage:', sys.argv[0])
    print('Usage:', sys.argv[0], 'arg1')
    print('arg1 ???????????????', '?????????????????????????????????ip?????????')
    os._exit(0)


def gen_ip_by_args_internal(arg):
    ip_list = []
    if os.path.exists(arg):
        ip_list = read_all_ips_form_path(arg)
    elif arg.startswith('http'):
        print('?????????????????????ip ????????????... ...')
        r = download_file_from_net(arg, g_config.NET_IP_FILE_SAVE_PATH)
        print('???????????????ip ????????????:', '??????' if r else '??????')
        if r:
            ip_list = read_all_ips_form_file(g_config.NET_IP_FILE_SAVE_PATH)
    elif is_ip_network(arg):
        ip_list = gen_ip_form_network(arg)
    elif is_ip(arg):
        ip_list.append(arg)
    else:
        help()
    return ip_list


def gen_ip_list_by_args():
    ip_list = []
    if len(sys.argv) == 1:
        arg = g_config.IP_SOURCE
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
    else:
        help()
    ip_list = gen_ip_by_args_internal(arg)
    if ip_list:
        print('??????????????????{}???ip'.format(len(ip_list)))
        return ip_list
    else:
        print("??????????????????ip ?????????????????????????????????")
        os._exit(0)


def main():
    all_ips = gen_ip_list_by_args()
    if len(all_ips) > g_config.MAX_FILTER_VALID_IP_COUNT:
        print('??????ip ?????????????????????{}???'.format(g_config.MAX_FILTER_VALID_IP_COUNT))
        all_ips = filter_ip_by_num(all_ips, g_config.MAX_FILTER_VALID_IP_COUNT)
    passed_ips = filter_valid_ips(all_ips, g_config.THREAD_NUM,
                                  g_config.NAME_SERVER, g_config.TIME_OUT, g_config.MAX_RETRY)
    if len(passed_ips) > g_config.MAX_FILTER_RTT_IP_COUNT:
        print('??????ip ?????????????????????{}???'.format(g_config.MAX_FILTER_RTT_IP_COUNT))
        passed_ips = filter_ip_by_num(
            passed_ips, g_config.MAX_FILTER_RTT_IP_COUNT)
    if g_config.RTT_TEST_ENABLED:
        passed_ips = filter_ips_by_rtt(passed_ips)
    if len(passed_ips) > g_config.MAX_FILTER_BETTER_IP_COUNT:
        print('??????ip ?????????????????????{}???'.format(g_config.MAX_FILTER_BETTER_IP_COUNT))
        passed_ips = filter_ip_by_num(
            passed_ips, g_config.MAX_FILTER_BETTER_IP_COUNT)
    write_valid_ips_to_file(passed_ips)
    good_ips = filter_better_ip(passed_ips)
    good_ips = sorted(good_ips.items(), key=lambda kv: kv[1], reverse=True)
    write_better_ips_to_file(good_ips)


if __name__ == '__main__':
    main()
