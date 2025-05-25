import requests
from proxy_provider import ProxyProvider

class ProxyScrapeProvider(ProxyProvider):
    """
    Fetch proxies from ProxyScrape API
    """
    PROXIES_LIST_URL = "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&format=json"

    def fetch_proxies(self):
        """Fetch proxies from ProxyScrape."""
        response = requests.get(self.PROXIES_LIST_URL, timeout=10)
        response.raise_for_status()
        proxies_data = response.json()
        
        return_list = []
        for proxy in proxies_data.get('data', []):
            return_list.append({
                "city": proxy.get('city', 'Unknown city'),
                "country": proxy.get('country', 'Unknown').upper(),
                "host": proxy.get('ip'),
                "port": proxy.get('port'),
                "username": None,
                "password": None
            })
        return return_list