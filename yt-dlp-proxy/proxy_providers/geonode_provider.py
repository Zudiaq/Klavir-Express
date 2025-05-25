import requests
from proxy_provider import ProxyProvider

class GeonodeProvider(ProxyProvider):
    """
    Fetch proxies from Geonode API
    """
    PROXIES_LIST_URL = "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc&filterUpTime=90&protocols=http,https"

    def fetch_proxies(self):
        """Fetch proxies from Geonode API."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(self.PROXIES_LIST_URL, headers=headers, timeout=10)
        response.raise_for_status()
        proxies_data = response.json()
        
        return_list = []
        for proxy in proxies_data.get('data', []):
            # Skip Russian proxies
            country = proxy.get('country', '').upper()
            if country == 'RU' or country == 'RUSSIA':
                continue
                
            return_list.append({
                "city": proxy.get('city', 'Unknown city'),
                "country": country,
                "host": proxy.get('ip'),
                "port": proxy.get('port'),
                "username": None,
                "password": None
            })
        return return_list