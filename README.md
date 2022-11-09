# ip-check

## 使用方法

1. 复制env.py.eample 到env.py 并修改

   ```python
   # IP列表输入文件,
   # 可以从https://codeload.github.com/ip-scanner/cloudflare/zip/refs/heads/daily 保存为${NET_IP_FILE_SAVE_NAME}.${SOURCE_TYPE}
   # 或者使用ip.txt
   # 假设ip.txt 是网段的话讲计算出所有子网ip
   IP_SOURCE = 'ip.txt'
   # 网络下载ip 资源文件的代理
   PROXY = None
   # 网络资源ip 文件本地存储路径
   NET_IP_FILE_SAVE_PATH = 'download.bin'
   # 检查ip 可用性的多线程数量
   THREAD_NUM = 100
   # 检查ip 可用性重试次数
   MAX_RETRY = 3
   # 检查ip 可用性连接超时
   TIME_OUT = 3
   # 检查ip 可用性的域名，只要是使用clouldflare cdn 的网站即可
   NAME_SERVER = 'icook.tw'
   # 可用ip 输出目录
   VALID_IP_FILE = 'hits.txt'
   # 优选ip 输出文件，当前无效
   BETTER_IP_FILE = 'result.txt'
   # 从ip 列表中随机选择的${MAX_FILTER_VALID_IP_COUNT}个ip 用来检测可用性
   MAX_FILTER_VALID_IP_COUNT = 1000
   # 从可用ip 列表中随机抽选的待测优选${MAX_FILTER_BETTER_IP_COUNT}个ip 用来测试网速
   MAX_FILTER_BETTER_IP_COUNT = 200
   # 从可用ip 列表中随机抽选的待测优选${MAX_FILTER_RTT_IP_COUNT}个ip 用来测试RTT
   MAX_FILTER_RTT_IP_COUNT = 100
   # 是否测试RTT
   RTT_TEST_ENABLED = True
   # rtt 测试 配置
   RTT_TEST_HOST = 'www.cloudflare.com'
   # RTT 测试请求超时
   RTT_TEST_TIMEOUT = 5
   # RTT 测试多线程数量
   RTT_TEST_MAX_THREAD_NUM = 20
   # 允许的RTT 延时
   RTT_ALLOWED_TIMEOUT = 2500
   # 设置每个ip 的RTT 测试次数
   RTT_TEST_TIMES = 2
   # 测试下载连接超时
   TEST_DOWNLOAD_CONNECTTIMEOUT = 5
   # 期望网速
   EXPECTED_SPEED = 7000
   # 下载文件domain
   TEST_DOWNLOAD_DOMAIN = 'cloudflaremirrors.com'
   # 测试下载总时长
   TEST_DOWNLOAD_TIMEOUT = 15
   # 下载文件路径
   TEST_DOWNLOAD_FILE_PATH = '/archlinux/iso/latest/archlinux-x86_64.iso'
   ```

2. 按照操作系统选择脚本运行

   - **windows**

     ```bash
     ip_check.exe
     ip_check.exe arg1
     arg1 可选参数为 文件、目录、下载链接、ip、网段
     ```

   - **linux**
   
     ```shell
     chmod +x ip_check
     ./ip_check
     ./ip_check arg1
     arg1 可选参数为 文件、目录、下载链接、ip、网段
     ```

## TODO

- [x] 使用python完成测速逻辑（当前pycurl 在windows 上无法使用）
- [ ] ~~windows批处理实现对测速结果排序（不太熟悉batch 脚本语言）~~

## 引用说明

- [better-cloudflare-ip](https://github.com/badafans/better-cloudflare-ip) ：copy了脚本实现
- [cloudflare](https://github.com/ip-scanner/cloudflare)：可用ip 列表
- [CloudflareSpeedTest](https://github.com/XIU2/CloudflareSpeedTest)：copy 了cloudflare ip网段
- [https://bulianglin.com/](https://bulianglin.com/archives/cfcf.html): 参考了ip 可用性检查
