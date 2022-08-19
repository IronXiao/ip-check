import os
import functools
import re


def singleton(cls):
    """
    将一个类作为单例
    来自 https://wiki.python.org/moin/PythonDecoratorLibrary#Singleton
    """

    cls.__new_original__ = cls.__new__

    @functools.wraps(cls.__new__)
    def singleton_new(cls, *args, **kw):
        it = cls.__dict__.get('__it__')
        if it is not None:
            return it

        cls.__it__ = it = cls.__new_original__(cls, *args, **kw)
        it.__init_original__(*args, **kw)
        return it

    cls.__new__ = singleton_new
    cls.__init_original__ = cls.__init__
    cls.__init__ = object.__init__

    return cls


@singleton
class Config:
    CONFIG_FILE = "env.py"
    IP_FILE = 'cloudflare-daily.zip'
    THREAD_NUM = 10
    MAX_RETRY = 2
    TIME_OUT = 3
    MAX_FILTER_VALID_IP_COUNT = 1500
    MAX_FILTER_BETTER_IP_COUNT = 20
    NAME_SERVER = 'icook.tw'
    VALID_IP_FILE = 'out.txt'
    BETTER_IP_FILE = 'result.txt'
    NS_TEST_SERVER = 'http://{}/cdn-cgi/trace'
    NS_TEST_RESPONSE = 'h={}'.format(NAME_SERVER)
    TEST_DOWNLOAD_DOMAIN = 'cloudflaremirrors.com'
    TEST_DOWNLOAD_DOMAIN_PORT = 443
    TEST_DOWNLOAD_TIMEOUT = 10
    TEST_DOWNLOAD_CONNECTTIMEOUT = 1
    TEST_DOWNLOAD_FILE_PATH = 'archlinux/iso/latest/archlinux-x86_64.iso'
    TEST_DOWNLOAD_FILE_LINK = 'https://{}/{}'.format(
        TEST_DOWNLOAD_DOMAIN, TEST_DOWNLOAD_FILE_PATH)
    TEST_DOWNLOAD_SAVE_FILE = 'down.bin'
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
    EXPECTED_SPEED = 5*1024

    envs = []

    def __init__(self):
        self.init_envs()

    def update_configs(self, envs):
        for key, value in envs:
            setattr(self, key, value)

    def init_envs(self):
        self.envs = EnvLoader.load_with_file(self.CONFIG_FILE)
        self.update_configs(self.envs)


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
