def fetch_page(url):
    params = {
        'api_key': SCRAPER_API_KEY,
        'url': url,
        'render': 'true' 
    }
    headers = {'User-Agent': 'PriceSavvyBot/1.0 (GraphicEraAssignment)'}
    
    try:
        print(f"DEBUG: Starting fetch for {url}")
        
        # INCREASED TIMEOUT: ScraperAPI rendering needs ~15-20 seconds
        response = requests.get(
            SCRAPER_API_URL, 
            params=params, 
            headers=headers, 
            timeout=25 # Set to 25 to be safe
        )
        
        # Check for HTTP errors (like 403 or 500)
        response.raise_for_status() 

        # Check for CAPTCHA in the returned HTML
        if "captcha" in response.text.lower() or "robot check" in response.text.lower():
            print(f"!! ALERT: Blocked by anti-bot on {url} !!")
            return None

        print(f"DEBUG: Successfully fetched {url}")
        return response.text
        
    except requests.exceptions.Timeout:
        print(f"ERROR: Timeout fetching {url}. The site took too long to render.")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error fetching {url}: {e}")
        return None