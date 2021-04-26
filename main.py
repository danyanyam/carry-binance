import asyncio
import itertools
from pprint import pprint
import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from itertools import groupby
from get_basis import get_basis, FutureManager
import os


API_TOKEN = os.getenv('TG_TOKEN')
ALL_DATA = None

async def check_sometimes():
    global ALL_DATA
    while True:
        basises = await get_basis()
        ALL_DATA = basises
        expirations = set([i.expire_in for i in basises])
        for days_to_expire in expirations:
            expiration_group = []
            for item in basises:
                if item.expire_in == days_to_expire:
                    expiration_group.append(item)
            print([i.carry for i in expiration_group])

        await asyncio.sleep(15)



def prettifier(x):
    return " · Symbol: {:6s}:\nfutures: {:7.3f}, spot: {:7.3f}, basis: {:2.2f}%, exp: {:3.0f}\n".format(
        x.pair, x.future, x.spot, x.carry, x.expire_in)


async def start_handler(event: types.Message):
    basises = await get_basis()
    expirations = set([i.expire_in for i in basises])

    for days_to_expire in expirations:
        to_show = []
        for item in basises:
            if item.expire_in == days_to_expire:
                to_show.append(prettifier(item))

        message = [f'📅 Contracts, which expire in {days_to_expire} days:\n\n']
        message.extend(to_show)
        await event.answer(
            '\n'.join(message),
            parse_mode=types.ParseMode.HTML
        )


async def watch_exact_handler(event: types.Message):
    global ALL_DATA
    companies = event.text.split(' ')[1:]
    exacts = []
    for i in companies:
        exacts.extend(list(filter(lambda x: x.marginAsset.strip().upper() == i.strip().upper(), ALL_DATA)))
    for i in exacts:
        await event.answer(
                prettifier(i),
                parse_mode=types.ParseMode.HTML
            )
    


async def main():

    bot = Bot(token=API_TOKEN)
    try:
        disp = Dispatcher(bot=bot)
        disp.register_message_handler(
            start_handler, commands={"start", "restart"})
        
        disp.register_message_handler(
            watch_exact_handler, commands={"watch"})

        await disp.start_polling()
    finally:
        await bot.close()


async def wrapper():

    tasks = [
        asyncio.create_task(check_sometimes()),
        asyncio.create_task(main())
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(wrapper())
