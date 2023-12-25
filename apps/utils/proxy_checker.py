import asyncio
from aiohttp import ClientSession, ClientTimeout
import time
import argparse
from urllib.parse import urlparse
from aiohttp_proxy import ProxyConnector

# List of URLs to be checked
urls = ['http://httpbin.org/get', 'http://www.google.com', "https://icanhazip.com/", "https://jsonip.com/",
        "https://api.seeip.org/jsonip", "https://api.geoiplookup.net/?json=true"]
URLS = ['http://www.google.com', "https://bing.com"]
netloc_models = {
    "www.google.com": "google_delay",
    "bing.com": "bing_delay",
    "icanhazip.com": "icanhazip_delay",
    "jsonip.com": "jsonip_delay",
    "api.seeip.org": "seeip_delay",
    "api.geoiplookup.net": "geoiplookup_delay",
}


# urls = ["https://api.geoiplookup.net/?json=true"]


def read_proxies(proxy_file, batch_size=100):
    with open(proxy_file, 'r') as file:
        batch = []
        for line in file:
            if line.strip():
                batch.append(line.strip())
                if len(batch) == batch_size:
                    yield batch
                    batch = []
        if batch:
            yield batch


async def fetch_using_proxy(url, proxy):
    try:
        # 解析代理URL以获取用户名和密码
        proxy_url = urlparse(proxy)
        connector = ProxyConnector.from_url(proxy)
        start_time = time.perf_counter()
        async with ClientSession(connector=connector, timeout=ClientTimeout(total=5)) as session:
            async with session.get(url, ssl=False) as response:
                await response.read()
                latency = round((time.perf_counter() - start_time) * 1000)  # Latency in milliseconds
                print(f'URL: {url}, Proxy: {proxy}, Latency: {latency}, Status: {response.status}')
                if response.ok and response.status == 200:
                    return url, proxy, latency, True
                else:
                    return url, proxy, 9999999, False
    except Exception as e:
        print(f'Error. URL: {url}, Proxy: {proxy}; Error: {e}')
        latency = 9999999
        return url, proxy, latency, False


def get_proxies(id=None, status=None):
    filter_dict = {}
    if id is not None:
        filter_dict['id'] = id
    if status is not None:
        filter_dict['status'] = status
    proxies = Proxy.objects.filter(**filter_dict).all()
    proxies_dict = {f'http://{p.get_proxy_str()}': p.id for p in proxies}

    return proxies_dict


async def check_proxies_from_db():
    for proxies, id in get_proxies().items():
        tasks = [fetch_using_proxy(url, proxy) for proxy in proxies for url in URLS]
        results = await asyncio.gather(*tasks)
        for url, proxy, latency, success in results:
            if success:
                proxy_obj = Proxy.objects.filter(id=id).first()
                if proxy_obj:
                    model_name = netloc_models.get(urlparse(url).netloc, None)
                    if model_name and hasattr(proxy_obj, model_name):
                        setattr(proxy_obj, model_name, latency)
                        proxy_obj.save()


async def check_proxies(proxy_file, batch_size=100):
    for proxies in read_proxies(proxy_file, batch_size):
        tasks = [fetch_using_proxy(url, proxy) for proxy in proxies for url in URLS]
        results = await asyncio.gather(*tasks)
        url_files = {}
        for url, proxy, latency, success in results:
            success_str = 'successful' if success else 'failed'
            filename = f'{urlparse(url).netloc}_{success_str}_latency.txt'
            if filename not in url_files:
                url_files[filename] = open(filename, 'w')
            file = url_files[filename]
            file.write(f"{proxy},{latency if success else 9999}\n")
        for file in url_files.values():
            file.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='Proxy file path',
                        default='/opt/mentos_shop_backend/logs/http_user_pwd_ip_port.txt')
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_proxies(args.file))
    loop.close()


if __name__ == '__main__':
    main()
