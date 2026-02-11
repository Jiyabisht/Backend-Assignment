from rapidfuzz import fuzz
import re

def normalize_price(price_val):
    if not price_val:
        return 0.0
    # Strip symbols and commas, then convert to float
    clean = re.sub(r'[^\d.]', '', str(price_val))
    try:
        return float(clean)
    except:
        return 0.0

def is_duplicate(name1, name2, threshold=85):
    # Fuzzy token similarity as required by PRD
    return fuzz.token_set_ratio(name1.lower(), name2.lower()) >= threshold