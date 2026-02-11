import requests
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from utils import normalize_price

SCRAPER_API_KEY = '9d64e57c2e9164c4007b0557258d3028'
SCRAPER_API_URL = 'http://api.scraperapi.com'

def fetch_stealth_html(url):
    """Generic stealth fetcher for both Amazon and Flipkart"""
    params = {
        'api_key': SCRAPER_API_KEY,
        'url': url,
        'render': 'true',
        'premium': 'true',
        'country_code': 'in',
        'keep_headers': 'true'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }
    try:
        print(f"DEBUG: Stealth fetching {url}")
        response = requests.get(SCRAPER_API_URL, params=params, headers=headers, timeout=60)
        return response.text if response.status_code == 200 else None
    except Exception as e:
        print(f"Fetch Error: {e}")
        return None

def parse_amazon_html(html):
    if not html: return []
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    
    # 1. Look for all price containers
    price_blocks = soup.find_all('span', {'class': 'a-price'})
    
    for block in price_blocks:
        container = block.find_parent('div', {'data-component-type': 's-search-result'}) or \
                    block.find_parent('div', {'class': 's-result-item'})
        
        if container:
            name_tag = container.select_one('h2 a span') or container.select_one('h2 span')
            price_tag = container.select_one('.a-price .a-offscreen') or block.select_one('.a-price-whole')
            link_tag = container.select_one('h2 a') or container.find('a', href=True)

            if name_tag and price_tag:
                url = link_tag['href'] if link_tag else ""
                products.append({
                    "name": name_tag.text.strip(),
                    "price": normalize_price(price_tag.text),
                    "source": "Amazon",
                    "url": "https://www.amazon.in" + url if url.startswith('/') else url
                })

    # Fallback search if main blocks fail
    if not products:
        potential_prices = soup.find_all(string=re.compile(r'₹'))
        for p in potential_prices[:10]:
            parent = p.find_parent('div')
            name = parent.find_previous('h2') or parent.find_previous('a')
            if name and len(name.text) > 10:
                products.append({
                    "name": name.text.strip()[:60],
                    "price": normalize_price(p),
                    "source": "Amazon",
                    "url": "https://www.amazon.in"
                })
                
    return products

def parse_flipkart_html(html):
    if not html: return []
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    items = soup.select('div[data-id]') or soup.select('div._1AtVbE')
    for item in items:
        price_tag = item.find(string=re.compile(r'₹'))
        name_tag = item.select_one('a[title]') or item.select_one('div.KzY19u') or item.select_one('a.w1Y96B')
        link_tag = item.select_one('a[href]')
        if name_tag and price_tag:
            name_text = name_tag.text.strip()
            if "save extra" in name_text.lower() or len(name_text) < 15:
                continue
            products.append({
                "name": name_text,
                "price": normalize_price(str(price_tag)),
                "source": "Flipkart",
                "url": "https://www.flipkart.com" + link_tag['href'] if link_tag else ""
            })
    return products

def run_concurrent_scrapers(query):
    amazon_url = f"https://www.amazon.in/s?k={query}"
    flipkart_url = f"https://www.flipkart.com/search?q={query}"
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_amazon = executor.submit(fetch_stealth_html, amazon_url)
        future_flipkart = executor.submit(fetch_stealth_html, flipkart_url)
        
        amazon_html = future_amazon.result()
        flipkart_html = future_flipkart.result()

    results = []
    
    if amazon_html:
        amz_results = parse_amazon_html(amazon_html)
        print(f"DEBUG: Found {len(amz_results)} Amazon products")
        results.extend(amz_results)

    if flipkart_html:
        fk_results = parse_flipkart_html(flipkart_html)
        print(f"DEBUG: Found {len(fk_results)} Flipkart products")
        results.extend(fk_results)
            
    return results