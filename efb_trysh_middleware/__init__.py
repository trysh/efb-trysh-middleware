# coding=utf-8
import io
import json
import logging
import math
import os
import tempfile
import time
import uuid
from gettext import translation

import requests
import selenium.webdriver.common.by as by
import selenium.webdriver.remote.webelement as webele
import selenium.webdriver.support.expected_conditions as ec
import selenium.webdriver.support.wait as webwait
# import asyncio
# from pyppeteer import launch
from PIL import Image
from ehforwarderbot import ChatType, EFBChat, EFBMiddleware, EFBMsg, MsgType, coordinator, utils
from pkg_resources import resource_filename
from ruamel.yaml import YAML
from selenium import webdriver
from typing import Optional

from .__version__ import __version__ as version

# from ehforwarderbot import EFBMiddleware, coordinator
# from efb_telegram_master import TelegramChannel
# from efb_telegram_master.whitelisthandler import WhitelistHandler

yaml = YAML()
c_host = 'https://www.hubi.pub'


def find_ele(wd: webdriver, xpath: str) -> webele.WebElement:
    wait = webwait.WebDriverWait(wd, 30)
    return wait.until(ec.presence_of_element_located((by.By.XPATH, xpath)))


class TryshMiddleware(EFBMiddleware):
    """
    Configuration:

    .. code-block: yaml

        key: BD6B65EC00638DC9083781D5D4B65BB1A106200A
        password: test
        always_trust: true
        binary: /usr/bin/gpg
        server: pgp.mit.edu
    """
    middleware_id: str = "trysh.trysh"
    middleware_name: str = "trysh Middleware"
    __version__: str = version

    chat: EFBChat = None

    # mappings: Dict[Tuple[str, str], str] = {}

    # key: str = None
    # password: str = None
    # always_trust: bool = True
    # binary: str = "gpg"
    # server: str = "pgp.mit.edu"
    # encrypt_all: bool = False

    Me: EFBChat = None
    apikey: str = ""

    translator = translation("efb_trysh_middleware",
                             resource_filename("efb_trysh_middleware", "locale"),
                             fallback=True)
    _ = translator.gettext

    def __init__(self, instance_id: str = None):
        super().__init__(instance_id)
        storage_path = utils.get_data_path(self.middleware_id)
        config_path = utils.get_config_path(self.middleware_id)
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
        if not os.path.exists(config_path):
            # raise EFBException(self._("GnuPG middleware is not configured."))
            pass
        else:
            config = yaml.load(open(config_path))
            # self.key = config['key']
            # self.always_trust = config.get('always_trust', self.always_trust)
            # self.binary = config.get('binary', self.binary)
            # self.password = config.get('password', self.password)
            # self.server = config.get('server', self.server)
            self.apikey = config.get('apikey', self.apikey).strip()

        # self.mappings_path = os.path.join(storage_path, "keymap.pkl")
        # if os.path.exists(self.mappings_path):
        #     self.mappings = pickle.load(open(self.mappings_path, 'rb'))

        self.chat = EFBChat()
        self.chat.channel_name = self.middleware_name
        self.chat.module_name = self.middleware_name
        self.chat.channel_id = self.middleware_id
        self.chat.module_id = self.middleware_id
        self.chat.channel_emoji = "🤖"
        self.chat.chat_uid = "__trysh.trysh__"
        self.chat.chat_name = self.middleware_name
        self.chat.chat_type = ChatType.System

        self.logger = logging.getLogger("trysh.trysh")
        self.logger.debug("trysh init ok")
        # self.logger.setLevel(99)

    def lg(self, msg):  # , *args, **kwargs):
        self.logger.log(99, msg)  # , *args, **kwargs)

    def process_message(self, message: EFBMsg) -> Optional[EFBMsg]:
        self.lg(f"Received:{message} | author:{message.author} | chat:{message.chat} | target:{message.target} | \
 chatt:{message.chat.chat_type} | cmd:{message.commands}")
        # self.lg("Received message: %s |author:%s |chat:%s |type:%s |target:%s",
        #         message, message.author, message.chat, message.type, message.target)
        # if not message.type == MsgType.Text:
        #     return message
        coins = ('HUB', 'BTC', 'ETH', 'EOS')

        def coin_re(coin: str):
            if coin in coins:
                rq = self.get_coin(coin)
                if rq and len(rq) == 2:
                    self.reply_message(message, f"{coin}: {rq[0]}¥  {rq[1]}$")
                rt = None
                try:
                    rt = self.get_coinimg(coin)
                except BaseException as e:
                    self.lg(f'get_coinimg ee:{e}')
                if rt:
                    im3 = rt.convert('RGB')
                    # img_file = io.BytesIO()
                    # im3.save(img_file, 'JPEG')
                    # Image.open(img_file)
                    fname = ''
                    locals()
                    with tempfile.NamedTemporaryFile('w+t', suffix=".jpg") as f:
                        im3.save(f, 'JPEG')
                        fname = f.name
                        # img_file = open(fname, )
                        self.reply_message_img(message, f, fname)

        if message.type == MsgType.Text:
            txt = message.text[:].strip().upper() or ''
            # if False and txt.startswith('/') and len(txt) >= 2:
            #     pass  # coin_re(txt[1:])
            if txt in coins:
                coin_re(txt)
        # if message.type == MsgType.Text:
        #     txt = message.text[:].strip().lower() or ''
        #     if txt == 'disnot':
        #         print('disnot')
        return message

    def reply_message(self, message: EFBMsg, text: str):
        reply = EFBMsg()
        reply.text = text
        # reply.chat = coordinator.slaves[message.chat.channel_id].get_chat(message.chat.chat_uid)
        reply.chat = coordinator.slaves[message.chat.module_id].get_chat(message.chat.chat_uid)
        reply.author = self.chat
        reply.type = MsgType.Text
        # reply.deliver_to = coordinator.master
        reply.deliver_to = coordinator.slaves[message.chat.module_id]
        # reply.target = message
        reply.uid = str(uuid.uuid4())
        r2 = reply
        coordinator.send_message(reply)
        r2.deliver_to = coordinator.master
        coordinator.send_message(r2)

    def reply_message_img(self, message: EFBMsg, img, fpath):
        reply = EFBMsg()
        # reply.text = text
        reply.file = img
        reply.path = fpath
        # reply.chat = coordinator.slaves[message.chat.channel_id].get_chat(message.chat.chat_uid)
        reply.chat = coordinator.slaves[message.chat.module_id].get_chat(message.chat.chat_uid)
        reply.author = self.chat
        reply.type = MsgType.Image
        reply.mime = 'image/gif'
        # reply.deliver_to = coordinator.master
        reply.deliver_to = coordinator.slaves[message.chat.module_id]
        # reply.target = message
        reply.uid = str(uuid.uuid4())
        r2 = reply
        coordinator.send_message(reply)
        r2.deliver_to = coordinator.master
        coordinator.send_message(r2)

    def get_coinimg(self, coin: str) -> Image.Image:
        wd = webdriver.Remote(command_executor='http://127.0.0.1:4444/wd/hub',
                              desired_capabilities={'platform': 'ANY', 'browserName': 'chrome',
                                                    'javascriptEnabled': True}, )
        wd.set_window_size(1440, 600)
        wd.get(f'https://www.hubi.pub/#/exchange/{coin.lower()}_usdt')
        ifr1 = find_ele(wd, "//iframe")
        time.sleep(1)
        ifr1 = find_ele(wd, "//iframe")
        # print(ifr1.location, ifr1.size)
        locat1 = ifr1.location
        size1 = ifr1.size
        wd.switch_to.frame(wd.find_element_by_xpath('//iframe'))
        # wd.switch_to.frame('tradingview_f3f48')
        ele = find_ele(wd, "//*[@class='chart-container active']")
        time.sleep(1)
        ele = find_ele(wd, "//*[@class='chart-container active']")
        # wd.save_screenshot('aaa.png')
        png = wd.get_screenshot_as_png()
        im = Image.open(io.BytesIO(png))
        location = ele.location
        size = ele.size
        # print(location, size)
        left = location['x'] + 500
        top = location['y'] + locat1['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height'] + locat1['y']  # + size1['height']
        # print(left, top, right, bottom)
        im2: Image.Image = im.crop((left, top, right, bottom))  # defines crop points
        # im2.save('aaa.png')  # saves new cropped image
        # im.save('bbb.png')  # saves new cropped image
        wd.close()
        return im2
        pass

    def get_coin(self, coin: str):
        url = c_host + '/api/ticker/public/convert/raw'
        parameters = {
        }
        headers = {
        }
        session = requests.Session()
        session.headers.update(headers)
        data = None
        qus = None
        raw = None
        locals()
        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
            qus = data.get('convert').get('quotes')
            raw = data.get('raw')
        except (ConnectionError, requests.Timeout, requests.TooManyRedirects, BaseException) as e:
            print('http err', e)
            return
        session.close()

        rateusdt2btc = 0.0
        for v in qus:
            if v.get('from') == 'USDT'.upper() and v.get('to') == 'BTC':
                rateusdt2btc = v.get('rate')
                break

        ratebtc2usd = 0.0
        for v in raw:
            if v.get('from') == 'BTC' and v.get('to') == 'USD':
                ratebtc2usd = v.get('rate')
                break

        ratebtc2cny = 0.0
        for v in raw:
            if v.get('from') == 'BTC' and v.get('to') == 'CNY':
                ratebtc2cny = v.get('rate')
                break

        # ratebtc2usd = 0.0
        # for v in raw:
        #     if v.get('from') == 'BTC' and v.get('to') == 'USD':
        #         ratebtc2usd = v.get('rate')
        #         break

        url = c_host + '/api/public/bos/market/trade/list'
        parameters = {
            'coin_code': coin,
            'price_coin_code': 'USDT',
            'partition_by': '01001'
        }

        session = requests.Session()
        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
        except (ConnectionError, requests.Timeout, requests.TooManyRedirects) as e:
            print('http err', e)
            return
        session.close()

        cv = 0.0
        try:
            cv = data.get('trades')[0].get('price')
        except Exception as e:
            print('except:', e)
        v1 = cv * rateusdt2btc * ratebtc2cny
        v2 = cv
        # print(cv, cv * rateusdt2btc * ratebtc2usd)
        v1 = math.floor(v1 * 1000) / 1000
        v2 = math.floor(v2 * 10000) / 10000
        try:
            v1 = "%.3f" % v1 if v1 < 50 else str(int(v1))
            v2 = "%.4f" % v2 if v2 < 10 else str(int(v2))
            # return f"btc:{data.data.BTC.quote.CNY.price} yo:{data.data.YO.quote.CNY.price}"
            # btcp = int(data.get('data', {}).get('BTC', {}).get('quote', {}).get('CNY', {}).get('price', 0))
            # ethp = int(data.get('data', {}).get('ETH', {}).get('quote', {}).get('CNY', {}).get('price', 0))
            # eosp = int(data.get('data', {}).get('EOS', {}).get('quote', {}).get('CNY', {}).get('price', 0))
            # return f"BTC:{btcp}￥ \nETH:{ethp}￥ \nEOS:{eosp}￥"
            return v1, v2
        except (ConnectionError, requests.Timeout, requests.TooManyRedirects, BaseException) as e:
            self.lg(f"api e:{e}")
            return ()

# def test_get_coin():
#     t = TryshMiddleware()
#     t.get_coin('hub')
