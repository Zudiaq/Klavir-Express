import requests
from bs4 import BeautifulSoup
from proxy_provider import ProxyProvider

class FreeProxyListProvider(ProxyProvider):
    """
    Fetch proxies from Free Proxy List website
    """
    PROXIES_LIST_URL = "https://free-proxy-list.net/"

    def fetch_proxies(self):
        """Fetch proxies from Free Proxy List."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(self.PROXIES_LIST_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'table table-striped table-bordered'})
        
        return_list = []
        if table:
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cols = row.find_all('td')
                if len(cols) >= 8:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    country = cols[3].text.strip()
                    
                    # Skip Russian proxies
                    if country.upper() == 'RU' or country.upper() == 'RUSSIA':
                        continue
                        
                    return_list.append({
                        "city": "Unknown city",
                        "country": country.upper(),
                        "host": ip,
                        "port": port,
                        "username": None,
                        "password": None
                    })
        return return_list