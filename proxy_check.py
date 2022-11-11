#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from unittest import result

def help():
    print("Example:")
    print("", sys.argv[0],"ip:port")

def main():
    if len(sys.argv) != 2:
        help()
        return
    proxy_str = sys.argv[1]
    proxy_elements = proxy_str.split(':')
    ip = proxy_elements[0]
    port = 1080 if len(proxy_elements) == 1 else proxy_elements[1]
    proxy = 'http://{}:{}'.format(ip, port)
    print('Testing proxy:', proxy)
    import requests
    proxies = {
        'http': proxy,
        'https': proxy,
    }
    try:
        req = requests.get('https://google.hk', proxies=proxies, timeout=5)
        status_code = req.status_code
        latency = int(req.elapsed.total_seconds() * 1000)
        req.close()
        result_str = '可用,延迟为{} ms'.format(latency) if status_code == 200 else '不可用'
        print(proxy, result_str)
    except Exception as e:
        print(proxy, '测试异常:', e)



if __name__ == '__main__':
    main()
