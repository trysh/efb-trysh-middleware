import json

import requests


def main():
    url = 'https://www.hubi.pub/api/public/bos/market/rate/latest'
    '''
    [{"coinCode":"HUB","btcRate":0.0000031374,"usdtRate":0.0342230000,"cnyRate":0.23952335470000,"btcRateStr":null,"usdtRateStr":null,"cnyRateStr":null}]
    '''
    # ''https://www.hubi.pub/api/public/bos/market/symbol/info/mobile'
    parameters = {
        'coin_code': 'HUB',  # 'symbol': coin + '_usdt',
        # 'partition_by': '01001',
    }
    headers = {
        # 'Accepts': 'application/json',
        # 'X-CMC_PRO_API_KEY': self.apikey,
    }
    session = requests.Session()
    session.headers.update(headers)
    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        # self.lg(f"api:{data}")
        print(data)
        # exit(0)
        v = data[0] if len(data) >= 1 else {}
        v1 = float(v.get('cnyRate', 0.0))
        v1 = "%.3f" % v1 if v1 < 10 else str(int(v1))
        v2 = float(v.get('usdtRate', 0.0))
        v2 = "%.4f" % v2 if v2 < 10 else str(int(v2))
        print(v1, v2)
        # return f"btc:{data.data.BTC.quote.CNY.price} yo:{data.data.YO.quote.CNY.price}"
        # btcp = int(data.get('data', {}).get('BTC', {}).get('quote', {}).get('CNY', {}).get('price', 0))
        # ethp = int(data.get('data', {}).get('ETH', {}).get('quote', {}).get('CNY', {}).get('price', 0))
        # eosp = int(data.get('data', {}).get('EOS', {}).get('quote', {}).get('CNY', {}).get('price', 0))
        # return f"BTC:{btcp}￥ \nETH:{ethp}￥ \nEOS:{eosp}￥"
        return
    except (ConnectionError, requests.Timeout, requests.TooManyRedirects) as e:
        return


if __name__ == '__main__':
    main()
