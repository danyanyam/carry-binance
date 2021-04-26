import asyncio
import aiohttp
from pprint import pprint
from dataclasses import dataclass
import pandas as pd
import datetime
from typing import List


@dataclass
class Future:
    symbol: str
    marginAsset: str
    baseAsset: str
    pair: str

    future: float
    spot: float
    
    expire_in: str = None
    carry: None = None

    def __post_init__(self):
        self.carry = round(100 * (self.future - self.spot) / self.spot, 2)
        self.expire_in = (datetime.datetime.strptime(self.symbol.split('_')[-1], "%y%m%d") - datetime.datetime.now()).days    


@dataclass
class FutureManager:
    futures: List[Future]
    
    def __post_init__(self):
        self.futures = list(sorted(self.futures, key=lambda x: x.carry, reverse=True))
        
    def get_best(self):
        return self.futures
    
        


async def get_all_futures():
    link = 'https://dapi.binance.com/dapi/v1/exchangeInfo'
    response = await fetch_api(link)
    return response


async def get_future_price(symbol):

    link = 'https://dapi.binance.com/dapi/v1/depth'
    response = await fetch_api(link, params={'symbol': symbol})
    future_price = float(response['asks'][0][0])
    return future_price


async def get_spot_price(symbol):
    link = 'https://api.binance.com/api/v3/depth'
    answer = await fetch_api(link, params={'symbol': symbol})    
    spot_price = float(answer['asks'][0][0])
    return spot_price


async def fetch_api(link, params={}):
    async with aiohttp.ClientSession() as session:
        async with session.get(link, params=params) as response:
            return await response.json()


async def request_wrapper(item):
    symbol = item['symbol']
    marginAsset = item['marginAsset']
    baseAsset = item['baseAsset']
    pair = item['pair']

    tasks = [asyncio.create_task(get_future_price(symbol)),
             asyncio.create_task(get_spot_price(f"{item['marginAsset']}USDT"))]

    future, spot = await asyncio.gather(*tasks)

    return Future(
        symbol=symbol,
        marginAsset=marginAsset,
        baseAsset=baseAsset,
        pair=pair,
        future=future,
        spot=spot
    )


async def get_basis():
    all_futures = await get_all_futures()
    expiry = [item for item in all_futures['symbols']
              if not item['symbol'].endswith('_PERP')]
    
    tasks = [
        asyncio.create_task(request_wrapper(item)) for item in expiry
    ]
    
    all_results = await asyncio.gather(*tasks)
    
    return all_results


    

if __name__ == "__main__":
    asyncio.run(get_basis())
