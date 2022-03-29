import requests
from bs4 import BeautifulSoup
import pandas

class NoWorkingProxy(Exception):
    pass

class RotatingIPSession(requests.Session):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.proxy_pool = set()
        self.proxy = str()
        self.__build_proxy_pool__()

    def __build_proxy_pool__(self):
        #print("Fetching proxies...")
        resp = super().get("https://free-proxy-list.net/").text
        soup = BeautifulSoup(resp, 'html.parser')
        table = soup.find("table")
        dfs = pandas.read_html(str(table))
        df = pandas.concat(dfs)
        for proxy in list((df[['IP Address', 'Port']].values)):
            self.proxy_pool.add(str(':'.join(tuple(map(str, tuple(proxy))))))
        self.proxy = list(self.proxy_pool)[0]
        self.proxy_pool = iter(self.proxy_pool)
        #print("Finished fetching proxies.")
    
    def get(self, *args, **kwargs):
        try:
            #print("Testing proxy:", self.proxy)
            resp = super().get(*args, proxies=dict(http=str(self.proxy), https=str(self.proxy)), timeout=1, **kwargs)
            #print("Working Proxy:", self.proxy)
            return resp
        except (StopIteration, requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout) as err:
            if isinstance(err, StopIteration):
                raise NoWorkingProxy()
            else:
                #print("Proxy failed.")
                self.proxy = next(self.proxy_pool)
                return self.get(*args, **kwargs)