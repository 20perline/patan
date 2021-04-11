
# import asyncio
# import aiohttp

# url = 'https://2.push2.eastmoney.com/api/qt/ulist/sse?invt=3&pi=0&pz=3&mpi=2000&secids=1.600549,0.300496,0.002230&ut=6d2ffaa6a585d612eda28417681d58fb&fields=f12,f13,f19,f14,f139,f148,f2,f4,f1,f125,f18,f3,f152,f88,f153,f89,f90,f91,f92,f94,f95,f97,f98,f99&po=1'


# async def main():

#     async with aiohttp.ClientSession() as session:
#         async with session.get(url) as response:

#             print("Status:", response.status)
#             print("Content-type:", response.headers['content-type'])

#             html = await response.text()
#             print("Body:", html, "...")

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())