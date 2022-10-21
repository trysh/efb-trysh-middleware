# coding=utf-8
import asyncio
import io
import json
import logging
import math
import os
import queue
import re
import tempfile
import threading
import time
import uuid
from gettext import translation
from typing import Optional

import ehforwarderbot.chat as efbchat
# import pyppeteer
import requests
# from selenium import webdriver
# import selenium.webdriver.common.by as by
# import selenium.webdriver.remote.webelement as webele
# import selenium.webdriver.support.expected_conditions as ec
# import selenium.webdriver.support.wait as webwait
# import asyncio
# from pyppeteer import launch
from PIL import Image
from ehforwarderbot import Message, Middleware, MsgType, coordinator, utils
from pkg_resources import resource_filename

from .__version__ import __version__ as version

# from ruamel.yaml import YAML

# from ehforwarderbot import EFBMiddleware, coordinator
# from efb_telegram_master import TelegramChannel
# from efb_telegram_master.whitelisthandler import WhitelistHandler

# yaml = YAML()
# c_host = 'https://www.hubi.pub'

logging.basicConfig(level='WARN',
                    format='File "%(filename)s", line %(lineno)d | %(asctime)s.%(msecs)03d | %(message)s',
                    datefmt='%m%d %H:%M:%S')
lg = logging.getLogger('')


#
# def find_ele(wd: webdriver, xpath: str) -> webele.WebElement:
#     wait = webwait.WebDriverWait(wd, 50)
#     return wait.until(ec.presence_of_element_located((by.By.XPATH, xpath)))


class TryshMiddleware(Middleware):
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

    chat: efbchat.SystemChat = None
    chatMember: efbchat.ChatMember = None

    # mappings: Dict[Tuple[str, str], str] = {}

    # key: str = None
    # password: str = None
    # always_trust: bool = True
    # binary: str = "gpg"
    # server: str = "pgp.mit.edu"
    # encrypt_all: bool = False

    Me: efbchat.Chat = None
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
            pass
            # config = yaml.load(open(config_path))
            # # self.key = config['key']
            # # self.always_trust = config.get('always_trust', self.always_trust)
            # # self.binary = config.get('binary', self.binary)
            # # self.password = config.get('password', self.password)
            # # self.server = config.get('server', self.server)
            # self.apikey = config.get('apikey', self.apikey).strip()

        # self.mappings_path = os.path.join(storage_path, "keymap.pkl")
        # if os.path.exists(self.mappings_path):
        #     self.mappings = pickle.load(open(self.mappings_path, 'rb'))

        self.chat = efbchat.SystemChat(
            middleware=self,
            # channel_name=self.middleware_name,
            module_name=self.middleware_name,
            # channel_id=self.middleware_id,
            module_id=self.middleware_id,
            channel_emoji="🤖",
            uid="__trysh.trysh__",
            # chat_name=self.middleware_name,
        )  # EFBChat()
        self.chat.channel_name = self.middleware_name
        self.chat.module_name = self.middleware_name
        self.chat.channel_id = self.middleware_id
        self.chat.module_id = self.middleware_id
        self.chat.channel_emoji = "🤖"
        self.chat.uid = "__trysh.trysh__"
        self.chat.chat_name = self.middleware_name
        # self.chat.chat_type = ChatType.System

        # self.chatMember = efbchat.ChatMember(
        #     chat=self.chat,
        #     middleware=self,
        #     # channel_name=self.middleware_name,
        #     # module_name=self.middleware_name,
        #     # channel_id=self.middleware_id,
        #     # module_id=self.middleware_id,
        #     # channel_emoji="🤖",
        #     uid="__trysh.trysh__",
        #     # chat_name=self.middleware_name,
        # )  # EFBChat()

        self.chat.channel_name = self.middleware_name
        self.chat.module_name = self.middleware_name
        self.chat.channel_id = self.middleware_id
        self.chat.module_id = self.middleware_id
        self.chat.channel_emoji = "🤖"
        self.chat.uid = "__trysh.trysh__"
        self.chat.chat_name = self.middleware_name

        self.logger = logging.getLogger("trysh.trysh")
        self.logger.log(99, f"trysh init ok v:{version}")
        # self.logger.setLevel(99)

        self.t1: threading.Thread = None
        self.t2: threading.Thread = None
        self.t3: threading.Thread = None
        self.t1q: queue.Queue = None
        self.t2q: queue.Queue = queue.Queue()
        self.t3q: queue.Queue = queue.Queue()

    def lg(self, msg):  # , *args, **kwargs):
        self.logger.log(99, msg)  # , *args, **kwargs)

    def process_message(self, message: Message) -> Optional[Message]:
        # self.lg(f"Received:message:{message}\n"
        #         f"chat:{message.chat, message.chat.chat_type}\n"
        #         f"msgtype:{message.mime, message.type, message.filename, message.file}\n"
        #         f"deliver_to:{message.deliver_to}\n"
        #         f"author:{message.author} | target:{message.target} ")

        # 处理"telegram图片长高比>=20.0无法预览"问题
        if message and message.type == MsgType.Image:
            self.handle_tg_img_preview(message)
            return message

        if not message or message.type != MsgType.Text:
            return message

        if not message or not message.chat \
                or 'HUB' in message.chat.__str__().upper() \
                or 'XCLOUD' in message.chat.__str__().upper():
            return message
        # chat:<EFBChat: HUB俱乐部 (7e68e4ef) @ WeChat Slave>

        txt = message.text[:].strip().upper() or ''
        # if False and txt.startswith('/') and len(txt) >= 2:
        #     pass  # coin_re(txt[1:])

        gushiname = "迷の故事"  # "偏锋测试"  #
        chatname = message.chat.__str__().upper()
        if gushiname in chatname:
            if not self.t2:
                self.t2 = threading.Thread(target=tf2, args=(self.t2q, self))
                self.lg(f'故事!thread')
                self.t2.start()
                self.t2q.put_nowait(('3', message))
            else:
                self.t2q.put_nowait(('4', message))
                self.lg(f'故事!thread update')

        if ("“游戏”爱好者" in chatname) or ('显卡“爱好者”' in chatname):
            if not self.t3:
                self.t3 = threading.Thread(target=tf3, args=(self.t3q, self))
                self.t3.start()
                self.t3q.put_nowait(('3', message))
            else:
                self.t3q.put_nowait(('4', message))

        self.coin_re(txt, message)

        return message

    def reply_message(self, message: Message, text: str):
        reply = Message()
        reply.text = text
        # reply.chat = coordinator.slaves[message.chat.channel_id].get_chat(message.chat.chat_uid)
        reply.chat = coordinator.slaves[message.chat.module_id].get_chat(message.chat.uid)
        reply.author = message.chat.make_system_member(
            uid=self.middleware_id,
            name=self.middleware_name,
            middleware=self
        )
        reply.type = MsgType.Text
        # reply.deliver_to = coordinator.master
        reply.deliver_to = coordinator.slaves[message.chat.module_id]
        # reply.target = message
        reply.uid = str(uuid.uuid4())
        r2 = reply
        coordinator.send_message(reply)
        r2.deliver_to = coordinator.master
        coordinator.send_message(r2)

    def reply_message_img(self, message: Message, im3: Image.Image):
        reply = Message()
        # reply.text = text
        # reply.chat = coordinator.slaves[message.chat.channel_id].get_chat(message.chat.chat_uid)
        reply.chat = coordinator.slaves[message.chat.module_id].get_chat(message.chat.uid)
        reply.author = message.chat.make_system_member(
            uid=self.middleware_id,
            name=self.middleware_name,
            middleware=self
        )
        reply.type = MsgType.Image
        reply.mime = 'image/png'
        f = tempfile.NamedTemporaryFile(suffix='.png')
        img_data = io.BytesIO()
        im3.save(img_data, format='png')
        f.write(img_data.getvalue())
        f.file.seek(0)
        reply.file = f
        reply.path = f.name
        reply.filename = os.path.basename(reply.file.name)

        # reply.deliver_to = coordinator.master
        reply.deliver_to = coordinator.slaves[message.chat.module_id]
        # reply.target = message
        reply.uid = str(uuid.uuid4())
        r2 = reply
        coordinator.send_message(reply)

        r2.type = MsgType.Image
        r2.mime = 'image/png'
        f = tempfile.NamedTemporaryFile(suffix='.png')
        img_data = io.BytesIO()
        im3.save(img_data, format='png')
        f.write(img_data.getvalue())
        f.file.seek(0)
        r2.file = f
        r2.path = f.name
        r2.filename = os.path.basename(r2.file.name)
        r2.deliver_to = coordinator.master
        coordinator.send_message(r2)

    # def get_coinimg(self, coin: str, seleurl: str = 'http://127.0.0.1:4444/wd/hub') -> Image.Image:
    #     wd = webdriver.Remote(command_executor=seleurl,
    #                           desired_capabilities={'platform': 'ANY', 'browserName': 'chrome',
    #                                                 'javascriptEnabled': True}, )
    #     wd.set_window_size(1440 - 400, 900)
    #     # wd.get(f'https://www.hubi.pub/#/exchange/{coin.lower()}_usdt')
    #     wd.get(f'https://www.hubi.pub/zh/exchange/{coin.upper()}_USDT')
    #     ifr1 = find_ele(wd, "//iframe")
    #     # time.sleep(1)
    #     # ifr1 = find_ele(wd, "//iframe")
    #     # print(ifr1.location, ifr1.size)
    #     locat1 = ifr1.location
    #     size1 = ifr1.size
    #     wd.switch_to.frame(wd.find_element_by_xpath('//iframe'))
    #     # wd.switch_to.frame('tradingview_f3f48')
    #     find_ele(wd, "//*[@class='chart-markup-table pane']/div/canvas[1]")
    #
    #     logoele = find_ele(wd, "//*[@class='onchart-tv-logo wrapper expanded on-pane']")
    #     wd.execute_script("""
    #     var element = arguments[0];
    #     element.parentNode.removeChild(element);
    #     """, logoele)
    #
    #     time.sleep(0.1)
    #     ele = find_ele(wd, "//*[@class='chart-container active']")
    #     # time.sleep(1)
    #     # ele = find_ele(wd, "//*[@class='chart-container active']")
    #     # wd.save_screenshot('aaa.png')
    #     png = ele.screenshot_as_png
    #     im = Image.open(io.BytesIO(png))
    #     location = ele.location
    #     size = ele.size
    #     # #
    #     # # rele = ele
    #     # # while True:
    #     # #     print('parent', rele.location)
    #     # #     tele = rele.find_element_by_xpath('..')
    #     # #     if tele and getattr(tele, 'location', None):
    #     # #         rele = tele
    #     # #     else:
    #     # #         break
    #     #
    #     # print(location, size)
    #     left = 0  # 203
    #     top = 0 + 5  # 27
    #     right = size['width'] - 5
    #     bottom = size['height'] - 3  # + size1['height']
    #     # print(left, top, right, bottom)
    #     im2: Image.Image = im.crop((left, top, right, bottom))  # defines crop points
    #     # im2.save('aaa.png')  # saves new cropped image
    #     # im.save('bbb.png')  # saves new cropped image
    #     wd.close()
    #     wd.quit()
    #     return im2  # im2
    #     pass

    # def get_coin0(self, coin: str):
    #     url = c_host + '/api/ticker/public/convert/raw'
    #     parameters = {
    #     }
    #     headers = {
    #     }
    #     session = requests.Session()
    #     session.headers.update(headers)
    #     data = None
    #     qus = None
    #     raw = None
    #     locals()
    #     try:
    #         response = session.get(url, params=parameters)
    #         data = json.loads(response.text)
    #         qus = data.get('convert').get('quotes')
    #         raw = data.get('raw')
    #     except (ConnectionError, requests.Timeout, requests.TooManyRedirects, BaseException) as e:
    #         print('http err', e)
    #         return
    #     session.close()
    #
    #     rateusdt2btc = 0.0
    #     for v in qus:
    #         if v.get('from') == 'USDT'.upper() and v.get('to') == 'BTC':
    #             rateusdt2btc = v.get('rate')
    #             break
    #
    #     ratebtc2usd = 0.0
    #     for v in raw:
    #         if v.get('from') == 'BTC' and v.get('to') == 'USD':
    #             ratebtc2usd = v.get('rate')
    #             break
    #
    #     ratebtc2cny = 0.0
    #     for v in raw:
    #         if v.get('from') == 'BTC' and v.get('to') == 'CNY':
    #             ratebtc2cny = v.get('rate')
    #             break
    #
    #     # ratebtc2usd = 0.0
    #     # for v in raw:
    #     #     if v.get('from') == 'BTC' and v.get('to') == 'USD':
    #     #         ratebtc2usd = v.get('rate')
    #     #         break
    #
    #     url = c_host + '/api/public/bos/market/trade/list'
    #     parameters = {
    #         'coin_code': coin,
    #         'price_coin_code': 'USDT',
    #         'partition_by': '01001'
    #     }
    #
    #     session = requests.Session()
    #     try:
    #         response = session.get(url, params=parameters)
    #         data = json.loads(response.text)
    #     except (ConnectionError, requests.Timeout, requests.TooManyRedirects) as e:
    #         print('http err', e)
    #         return
    #     session.close()
    #
    #     cv = 0.0
    #     try:
    #         # cv = data.get('trades')[0].get('price')
    #         cv = data[0].get('price')
    #
    #     except Exception as e:
    #         print('except:', e)
    #     v1 = float(cv) * rateusdt2btc * ratebtc2cny
    #     v2 = float(cv)
    #     # print(cv, cv * rateusdt2btc * ratebtc2usd)
    #     v1 = math.floor(v1 * 1000) / 1000
    #     v2 = math.floor(v2 * 10000) / 10000
    #     try:
    #         v1 = "%.3f" % v1 if v1 < 50 else str(int(v1))
    #         v2 = "%.4f" % v2 if v2 < 10 else str(int(v2))
    #         # return f"btc:{data.data.BTC.quote.CNY.price} yo:{data.data.YO.quote.CNY.price}"
    #         # btcp = int(data.get('data', {}).get('BTC', {}).get('quote', {}).get('CNY', {}).get('price', 0))
    #         # ethp = int(data.get('data', {}).get('ETH', {}).get('quote', {}).get('CNY', {}).get('price', 0))
    #         # eosp = int(data.get('data', {}).get('EOS', {}).get('quote', {}).get('CNY', {}).get('price', 0))
    #         # return f"BTC:{btcp}￥ \nETH:{ethp}￥ \nEOS:{eosp}￥"
    #         return v1, v2
    #     except (ConnectionError, requests.Timeout, requests.TooManyRedirects, BaseException) as e:
    #         self.lg(f"api e:{e}")
    #         return ()

    def get_coin(self, coin: str):
        coinusdt = 0
        if coin.upper() == "USDT":
            coinusdt = 1.0
        else:
            url = 'https://www.binance.com/api/v3/ticker/price'
            # ?symbol=ETHUSDT
            # c_host + '/api/connect/public/rate/quotes'
            parameters = {
                "symbol": coin.upper() + "USDT"
            }
            headers = {
            }
            session = requests.Session()
            session.headers.update(headers)
            data = None
            # qus = None
            # raw = None
            idx = None
            live = None
            locals()
            try:
                response = session.get(url, params=parameters, proxies={"https": "socks5h://10.0.0.203:11080"})
                data = json.loads(response.text)
                # idx = data.get('index', {})
                # live = data.get('live', {})
            except (ConnectionError, requests.Timeout, requests.TooManyRedirects, BaseException) as e:
                self.lg(f'http err:{e}')
                return
            session.close()

            # coinusd = idx.get(coin.upper() + "USD", 0)
            # coinusdt = idx.get(coin.upper() + "USDT", 0)
            coinusdt = float(data.get("price", "0"))
            # usdcny = live.get("USDCNY", 0)

        if coinusdt == 0:
            url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
            parameters = {
                "symbol": coin.upper()
            }
            headers = {
                "X-CMC_PRO_API_KEY": "04d33514-9e00-40d3-8ff9-3c501ffae1ef"
            }
            session = requests.Session()
            session.headers.update(headers)
            data = None
            locals()
            try:
                response = session.get(url, params=parameters, proxies={"https": "socks5h://10.0.0.203:11080"})
                data = json.loads(response.text)
            except (ConnectionError, requests.Timeout, requests.TooManyRedirects, BaseException) as e:
                self.lg(f'http err:{e}')
                return
            session.close()
            coinusdt = data.get("data", {}).get(coin.upper(), [{}])[0].get("quote", {}).get("USD", {}).get("price", 0)

        # # https://www.huobi.com/-/x/general/exchange_rate/list
        # url = 'https://www.huobi.com/-/x/general/exchange_rate/list'
        # parameters = {
        # }
        # headers = {
        # }
        # session = requests.Session()
        # session.headers.update(headers)
        # huobidata = None
        # locals()
        # try:
        #     response = session.get(url, params=parameters)
        #     data = json.loads(response.text)
        #     huobidata = data.get('data', [])
        # except (ConnectionError, requests.Timeout, requests.TooManyRedirects, BaseException) as e:
        #     print('http err2', e)
        #     return
        # session.close()
        # usdt2cny = 0
        # for v in huobidata:
        #     if v.get("name", "") == "usdt_cny":
        #         usdt2cny = v.get("rate", 0)
        #         break

        # url = 'https://c2c.binance.com/bapi/c2c/v2/public/c2c/adv/quoted-price'
        # parameters = {}
        # headers = {}
        # pstdat = {"assets": ["USDT"], "fiatCurrency": "CNY", "fromUserRole": "USER", "tradeType": "SELL"}
        # session = requests.Session()
        # session.headers.update(headers)
        # dats = None
        # locals()
        # try:
        #     response = session.post(url, json=pstdat)
        #     data = json.loads(response.text)
        #     dats = data.get('data', [])
        # except (ConnectionError, requests.Timeout, requests.TooManyRedirects, BaseException) as e:
        #     print('http err2', e)
        #     return
        # session.close()
        # usdt2cny = 0
        # for v in dats:
        #     if v.get("currency", "") == "CNY":
        #         usdt2cny = v.get("referencePrice", 0)
        #         break

        url = 'https://c2c.binance.com/bapi/asset/v1/public/asset-service/product/currency'
        parameters = {}
        headers = {}
        # pstdat = {"assets": ["USDT"], "fiatCurrency": "CNY", "fromUserRole": "USER", "tradeType": "SELL"}
        session = requests.Session()
        session.headers.update(headers)
        dats = None
        locals()
        try:
            response = session.get(url, proxies={"https": "socks5h://10.0.0.203:11080"})
            data = json.loads(response.text)
            dats = data.get('data', [])
        except (ConnectionError, requests.Timeout, requests.TooManyRedirects, BaseException) as e:
            self.lg(f'http err2:{e}')
            return
        session.close()
        usdt2cny = 0
        for v in dats:
            if v.get("pair", "") == "CNY_USD":
                usdt2cny = v.get("rate", 0)
                break

        v1 = usdt2cny * coinusdt
        v2 = coinusdt
        try:
            # print(cv, cv * rateusdt2btc * ratebtc2usd)
            if v2 < 0.002:
                v1 = math.floor(v1 * 100000) / 100000
                v2 = math.floor(v2 * 1000000) / 1000000
                v1 = "%.5f" % v1
                v2 = "%.6f" % v2
            else:
                v1 = math.floor(v1 * 1000) / 1000
                v2 = math.floor(v2 * 10000) / 10000
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

    def coin_re(self, coin: str, message: Message):
        # coins = ('HUB', 'BTC', 'ETH', 'EOS', 'LTC', 'ETC', 'BCH')
        # if coin not in coins:
        #     return
        cm = {
            "姨太": "eth",
            "以太": "eth",
            "以太晃": "eth",
            "大饼": "btc",
            "比特": "btc",
            "孙总的内裤": "eth",
            "屎币": "shib",
        }
        mv = cm.get(coin, "")
        if mv != "":
            coin = mv
        if not re.match('^[a-zA-Z0-9]{2,4}$', coin):
            return
        if re.match('^[0-9]{2,4}$', coin):
            return
        if not self.t1:
            self.t1q = queue.Queue()
            self.t1 = threading.Thread(target=tf1, args=(self.t1q, self))
            self.t1.start()

        self.t1q.put_nowait((coin, message))
        # return
        # rq = self.get_coin(coin)
        # if rq and len(rq) == 2:
        #     self.reply_message(message, f"{coin}: {rq[0]}¥  {rq[1]}$")
        # rt = None
        # try:
        #     rt = self.get_coinimg(coin)
        # except BaseException as e:
        #     self.lg(f'get_coinimg ee:{e}')
        # if rt:
        #     im3 = rt.convert('RGB')
        #     # img_file = io.BytesIO()
        #     # im3.save(img_file, 'JPEG')
        #     # Image.open(img_file)
        #
        #     # f = tempfile.NamedTemporaryFile(suffix='.jpg')
        #     # img_data = io.BytesIO()
        #     # im3.save(img_data, format='jpeg')
        #     # f.write(img_data.getvalue())
        #     # f.file.seek(0)
        #     # with tempfile.NamedTemporaryFile('w+b', suffix=".jpg") as f:
        #     # im3.save(f, 'jpeg')
        #     # fname = f.name
        #     # img_file = open(fname, )
        #     self.reply_message_img(message, im3)

    def handle_tg_img_preview(self, message: Message):
        if not message or not message.file or not message.filename:
            return
        if message.author.uid == self.middleware_id:  # trysh-middleware
            # self.lg('self')
            return
        if message.type != MsgType.Image:
            return

        try:
            message.file.seek(0)
            fbs = message.file.read()
            message.file.seek(0)
            im: Image.Image = Image.open(io.BytesIO(fbs))

            max_size = max(im.size)
            min_size = min(im.size)
            img_ratio = max_size / min_size
            if img_ratio < 10.0:
                return

            im2 = im.copy()
            for _ in range(100):
                max_size = max(im.size)
                min_size = min(im.size)
                img_ratio = max_size / min_size
                if img_ratio >= 10.0:
                    if im.width == min_size:
                        im = im.resize((im.width * 2, im.height), box=(0, 0, 1, 1))
                    else:
                        im = im.resize((im.width, im.height * 2), box=(0, 0, 1, 1))
                    continue
                else:
                    break

            im.paste(im2, (0, 0, im2.width, im2.height))

            im3 = im.convert('RGB')  # im.copy()  #
            reply = Message()
            # reply.text = text
            # reply.chat = coordinator.slaves[message.chat.channel_id].get_chat(message.chat.chat_uid)
            reply.chat = coordinator.slaves[message.chat.module_id].get_chat(message.chat.uid)
            reply.author = message.chat.make_system_member(
                uid=self.middleware_id,
                name=self.middleware_name,
                middleware=self
            )

            reply.type = MsgType.Image
            reply.mime = 'image/png'
            f = tempfile.NamedTemporaryFile(suffix='.png')
            img_data = io.BytesIO()
            im3.save(img_data, format='png')
            f.write(img_data.getvalue())
            f.file.seek(0)
            reply.file = f
            reply.path = f.name
            reply.filename = os.path.basename(reply.file.name)

            # reply.deliver_to = coordinator.master
            reply.deliver_to = coordinator.master
            # reply.target = message
            reply.uid = str(uuid.uuid4())
            coordinator.send_message(reply)

        except BaseException as e:
            self.lg(f'handle_tg_img_preview e:{e}')
        pass


# def test_get_coin():
#     t = TryshMiddleware()
#     t.get_coin('hub')


async def close2(b):
    lg.info('start close2')
    # rr = await page.close()
    # lg.info(f'start close2 {rr}')
    rr = await b.close()
    lg.info(f'start close2 {rr}')


# async def aget_coinimg(coin: str) -> Image.Image:
#     browser = await pyppeteer.launch({
#         'headless': True,  # 无头模式
#         'args': [
#             '--disable-extensions',
#             '--hide-scrollbars',
#             '--disable-bundled-ppapi-flash',
#             '--mute-audio',
#             '--no-sandbox',
#             '--disable-setuid-sandbox',
#             '--disable-gpu',
#             '--disable-infobars',
#         ],
#         # 'dumpio': True,
#         # 'loop': g_loop,
#         'handleSIGHUP': False,
#         'handleSIGTERM': False,
#         'handleSIGINT': False,
#     })
#     lg.info(f'browser:{browser}')
#     size = dict()
#     im: Image.Image = None
#     try:
#         page = await browser.newPage()
#         rr = await page.evaluate("""
#                 () =>{
#                     Object.defineProperties(navigator,{
#                         webdriver:{
#                         get: () => false
#                         }
#                     })
#                 }
#             """)
#
#         await page.setViewport({'width': 1440 - 400, 'height': 900})
#         lg.info(f'0')
#         await page.goto(f'https://www.hubi.pub/zh/exchange/{coin.upper()}_USDT')
#         lg.info(f'a')
#         fra = await page.xpath('//iframe')
#         lg.info(f'b:{fra}')
#         fr = await fra[0].contentFrame()
#         lg.info(f'c{fr}')
#         await fr.waitForSelector('td.chart-markup-table.pane > div > canvas:nth-child(1)')
#         # await page.waitForSelector('td.chart-markup-table.pane > div > canvas:nth-child(1)')
#         lg.info(f'd')
#         logoele = await fr.querySelector('div.onchart-tv-logo')
#         lg.info(f'e{logoele}')
#         await fr.evaluate('(v) => {v.parentNode.removeChild(v);}', logoele)
#         await fr.waitForSelector("tr:nth-child(1) > td.chart-markup-table.pane > div > canvas:nth-child(1)")
#         # rr = await fr.querySelector("tr:nth-child(1) > td.chart-markup-table.pane > div > canvas:nth-child(1)")
#         # lg.info(f'f{rr}')
#         # rr = await (await rr.getProperty('nodeName')).jsonValue()
#         # lg.info(f'g{rr}')
#         rr = await fr.querySelector("div.chart-container.active")
#         lg.info(f'a{rr}')
#         imgdata = await rr.screenshot()  # {'path': 'example.png'})
#         lg.info(f'b{len(imgdata)}')
#         # await asyncio.sleep(3)
#
#         im = Image.open(io.BytesIO(imgdata))
#         lg.info(f'im:{im}')
#         size['width'] = int(await (await rr.getProperty('clientWidth')).jsonValue())
#         size['height'] = int(await (await rr.getProperty('clientHeight')).jsonValue())
#         lg.info(f'size:{size}')
#     except BaseException as e:
#         lg.info(f'get img page ee:{e, type(e)}')
#
#     asyncio.get_running_loop().create_task(close2(browser))
#
#     # location = ele.location
#     # size = ele.size
#     # #
#     # # rele = ele
#     # # while True:
#     # #     print('parent', rele.location)
#     # #     tele = rele.find_element_by_xpath('..')
#     # #     if tele and getattr(tele, 'location', None):
#     # #         rele = tele
#     # #     else:
#     # #         break
#     #
#     # print(location, size)
#
#     if not im:
#         return None
#
#     left = 0  # 203
#     top = 0 + 5  # 27
#     right = size['width'] - 5
#     bottom = size['height'] - 3  # + size1['height']
#     # print(left, top, right, bottom)
#     im2: Image.Image = im.crop((left, top, right, bottom))  # defines crop points
#     lg.info(f'im2:{im2}')
#     return im2
#     pass


async def tf1a(q: queue.Queue, tm: TryshMiddleware):
    while True:
        await asyncio.sleep(0.1)
        try:
            tk = q.get_nowait()
            coin: str = tk[0]
            message: Message = tk[1]
            rq = tm.get_coin(coin)
            if rq and len(rq) == 2 and float(rq[0]) > 0 and float(rq[1]) > 0:
                tm.reply_message(message, f"{rq[0]}¥  {rq[1]}$")  # {coin}:
        except queue.Empty:
            # await asyncio.sleep(0.1)
            continue
        except BaseException as e:
            tm.lg(f'get_coin ee:{e}')
            continue

        # coinimg = await aget_coinimg(coin)
        # rt = None
        # try:
        #     rt = await aget_coinimg(coin)
        # except BaseException as e:
        #     tm.lg(f'get_coinimg ee:{e}')
        # if rt:
        #     try:
        #         im3 = rt.convert('RGB')
        #         # img_file = io.BytesIO()
        #         # im3.save(img_file, 'JPEG')
        #         # Image.open(img_file)
        #
        #         # f = tempfile.NamedTemporaryFile(suffix='.jpg')
        #         # img_data = io.BytesIO()
        #         # im3.save(img_data, format='jpeg')
        #         # f.write(img_data.getvalue())
        #         # f.file.seek(0)
        #         # with tempfile.NamedTemporaryFile('w+b', suffix=".jpg") as f:
        #         # im3.save(f, 'jpeg')
        #         # fname = f.name
        #         # img_file = open(fname, )
        #         tm.reply_message_img(message, im3)
        #     finally:
        #         pass

    pass


def tf1(q: queue.Queue, tm: TryshMiddleware):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(tf1a(q, tm))
    # asyncio.run(main())
    pass


# tf2
def tf2(q: queue.Queue, tm: TryshMiddleware):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(tf2a(q, tm))
    pass


# tf2a
async def tf2a(q: queue.Queue, tm: TryshMiddleware):
    cachemsg: Message = None
    while True:
        await asyncio.sleep(0.1)
        try:
            tk = q.get_nowait()
            # coin: str = tk[0]
            if tk[1]:
                # tm.lg(f'!udp: {tk[1]}')
                cachemsg = tk[1]
        except queue.Empty:
            # await asyncio.sleep(0.1)
            pass
        except BaseException as e:
            _ = e
            # tm.lg(f'get_coin ee:{e}')
            # continue
            pass
        if not cachemsg:
            continue
            # rq = tm.get_coin(coin)
            # if rq and len(rq) == 2 and float(rq[0]) > 0 and float(rq[1]) > 0:
        ct = time.localtime()
        if 0 <= ct.tm_wday <= 4 and ct.tm_hour == 7 and ct.tm_min == 0:
            tm.reply_message(cachemsg, f"3点啦")
            await asyncio.sleep(61)


# tf3
def tf3(q: queue.Queue, tm: TryshMiddleware):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(tf3a(q, tm))
    # asyncio.run(main())
    pass


# tf3a
async def tf3a(q: queue.Queue, tm: TryshMiddleware):
    cachemsg: Message = None
    lastckt = time.time()
    lastgh = 0
    while True:
        await asyncio.sleep(0.1)
        try:
            tk = q.get_nowait()
            # coin: str = tk[0]
            if tk[1]:
                tm.lg(f'!udp2')
                cachemsg = tk[1]
        except queue.Empty:
            pass
        except BaseException as e:
            _ = e
            pass
        if not cachemsg:
            continue
        if time.time() - lastckt < 61:
            continue
        tm.lg(f'start ck')
        gc = tm.get_coin("ETH")
        lastckt = time.time()
        if not gc or len(gc) < 2 or float(gc[1]) <= 0:
            tm.lg(f'gc:{gc}')
            continue
        gh = int(int(gc[1]) / 100)
        if gh <= 0:
            continue
        if lastgh == 0:
            lastgh = gh
            continue
        if gh > lastgh:
            tm.reply_message(cachemsg, f"姨太突破{gh * 100}啦,现报{gc[1]}")
            await asyncio.sleep(3600)
        elif gh < lastgh:
            tm.reply_message(cachemsg, f"姨太跌破{lastgh * 100}啦,现报{gc[1]}")
            await asyncio.sleep(3600)
        else:
            tm.lg(f"gh:{gh} lastgh:{lastgh} gc:{gc}")
            continue
        lastgh = gh
        await asyncio.sleep(30)
        continue
