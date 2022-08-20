# IP列表输入文件, 
# 可以从https://codeload.github.com/ip-scanner/cloudflare/zip/refs/heads/daily 保存为cloudflare-daily.zip
# 或者使用ip.txt
# 假设ip.txt 是网段的话讲计算出所有子网ip
IP_FILE = 'cloudflare-daily.zip'
# 检查ip 可用性的多线程数量
THREAD_NUM = 100
# 检查ip 可用性重试次数
MAX_RETRY = 1
# 检查ip 可用性连接超时
TIME_OUT = 2
# 检查ip 可用性的域名，只要是使用clouldflare cdn 的网站即可
NAME_SERVER = 'icook.tw'
# 可用ip 输出目录
VALID_IP_FILE = 'hits.txt'
# 优选ip 输出文件，当前无效
BETTER_IP_FILE = 'result.txt'
# 从ip 列表中随机选择的${MAX_FILTER_VALID_IP_COUNT}个ip 用来检测可用性
MAX_FILTER_VALID_IP_COUNT = 2000
# 从可用ip 列表中随机抽选的待测优选${MAX_FILTER_BETTER_IP_COUNT}个ip 用来测试网速
MAX_FILTER_BETTER_IP_COUNT = 200
# 测试下载连接超时，当前无效
TEST_DOWNLOAD_CONNECTTIMEOUT = 1
# 期望网速
EXPECTED_SPEED = 7000
# 下载测试文件名
TEST_DOWNLOAD_SAVE_FILE = 'down.bin'
# 下载时使用的浏览器标识
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
# 下载文件domain
TEST_DOWNLOAD_DOMAIN = 'cloudflaremirrors.com'
# 下载文件的网络端口
TEST_DOWNLOAD_DOMAIN_PORT = 443
# 测试下载总时长
TEST_DOWNLOAD_TIMEOUT = 20
# 下载文件路径
TEST_DOWNLOAD_FILE_PATH = 'archlinux/iso/latest/archlinux-x86_64.iso'
# 是否测试下载速度
TEST_DOWNLOAD_SPEED = False
