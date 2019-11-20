import json

import requests

import efb_trysh_middleware as etm

c_host = 'https://www.hubi.pub'


def main():
    t = etm.TryshMiddleware()
    # print(t.get_coin('btc'))
    rt = None
    try:
        rt = t.get_coinimg('btc', seleurl='http://127.0.0.1:4444/wd/hub')
    except BaseException as e:
        t.lg(f'get_coinimg ee:{e}')
    if rt:
        im3 = rt.convert('RGB')
        with open('temp_.png', 'wb') as f:
            im3.save(f, format='png')

    return

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

    ratebtc2usd = 0.0
    for v in raw:
        if v.get('from') == 'BTC' and v.get('to') == 'USD':
            ratebtc2usd = v.get('rate')
            break

    url = c_host + '/api/public/bos/market/trade/list'
    parameters = {
        'coin_code': 'HUB',
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

    cv = 0.0
    try:
        cv = data.get('trades')[0].get('price')
    except Exception as e:
        print('except:', e)
    v1 = cv * rateusdt2btc * ratebtc2cny
    v2 = cv
    print(v1, v2)

    # url = c_host + '/api/public/bos/market/rate/latest'
    # parameters = {
    #     'coin_code': 'USDT',
    # }
    #
    # session = requests.Session()
    # # session.headers.update(headers)
    # ratecny2 = 0.0
    # try:
    #     response = session.get(url, params=parameters)
    #     data = json.loads(response.text)
    #     ratecny2 = data[0].get('cnyRate')
    # except (ConnectionError, requests.Timeout, requests.TooManyRedirects, BaseException) as e:
    #     print('http err', e)
    #     return
    # print(cv*ratecny2)

    return
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


if __name__ == '__main__':
    main()


def test_t1():
    t = etm.TryshMiddleware()
    t.get_coin('hub')
