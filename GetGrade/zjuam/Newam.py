import re
import time
import qrcode
import requests
import urllib3
from requests.adapters import HTTPAdapter, Retry
import json
class ZJUAccount:
    """
    PC端登录浙大通行证
    """
    def __init__(self, username, password):
        """
        初始化
        :param username: 用户名（学号）
        :param password: 密码
        """
        self.username = username
        self.password = password
        self.http = urllib3.PoolManager()
        retries = Retry(total=5,
                backoff_factor=0.1,
                status_forcelist=[ 500, 502, 503, 504 ])

        #self.mount('https://', HTTPAdapter(max_retries=retries))

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.16; rv:84.0) Gecko/20100101 Firefox/84.0',
        }
        self.login_url = 'https://zjuam.zju.edu.cn/cas/login'
        self.pubkey_url = 'https://zjuam.zju.edu.cn/cas/v2/getPubKey'

    def login(self):
        """
        登录函数
        :return: session
        """
        # 获取公钥
        r=self.http.request('GET', self.pubkey_url)
        pubkey=json.loads(r.data.decode('utf-8'))
        #pubkey = self.session.get(self.pubkey_url).json()
        #self.session.keep_alive = False
        exponent, modulus = pubkey['exponent'], pubkey['modulus']

        data = {
            'username': self.username,
            'password': self._rsa_encrypt(self.password, exponent, modulus),
            'execution': self._get_execution(),
            'authcode': '',
            '_eventId': 'submit'
        }
        resp = r = self.http.request('POST','http://httpbin.org/post',fields=data)

        # 登录成功，获取姓名
        if self.check_login():
            #print(re.search('nick: \'(.*?)\'', resp.text).group(1), '登录成功!')
            return self.session
        else:
            print('登录失败。')
            return

    def _rsa_encrypt(self, password, exponent, modulus):
        """
        RSA加密函数
        :param password: 原始密码
        :param exponent: 十六进制 exponent
        :param modulus: 十六进制 modulus
        :return: RSA 加密后的密码
        """
        password_bytes = bytes(password, 'ascii')
        password_int = int.from_bytes(password_bytes, 'big')
        e_int = int(exponent, 16)
        m_int = int(modulus, 16)
        result_int = pow(password_int, e_int, m_int)
        return hex(result_int)[2:].rjust(128, '0')

    def _get_execution(self):
        """
        从页面HTML中获取 execution 的值
        :return: execution 的值
        """
        resp=self.http.request('GET', self.login_url)
        return re.search('name="execution" value="(.*?)"', resp.data).group(1)

    def check_login(self):
        """
        检查登录状态，访问登录页面出现跳转则是已登录，
        :return: bool
        """
        #resp = self.session.get(self.login_url, allow_redirects=False)
        resp=self.http.request('GET', self.login_url,allow_redirects=False)
        if resp.status_code == 302:
            return True
        return False



if __name__ == '__main__':
    zju = ZJUAccount('', '')
    # x = ZJUAccountScanqr()
    sess = zju.login()
