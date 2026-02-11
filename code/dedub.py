from difflib import SequenceMatcher

def get_similarity(a, b):
    """Calculates the fuzzy similarity ratio between two strings[cite: 19, 37]."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def deduplicate_results(results, threshold=0.7):
    """
    Clusters near-duplicates using fuzzy token similarity.
    If two products are similar, we keep both but could eventually 'merge' them.
    For this MVP, we will group them to highlight the best-by metric[cite: 10, 39].
    """
    unique_results = []
    for item in results:
        is_duplicate = False
        for existing in unique_results:
            # Compare names using the fuzzy threshold [cite: 37]
            if get_similarity(item['name'], existing['name']) > threshold:
                is_duplicate = True
                # If duplicate, we can keep the one with the better price/rating [cite: 39]
                if item['price'] < existing['price']:
                    # Update existing with cheaper price but keep original record link
                    existing['is_merged'] = True 
                break
        if not is_duplicate:
            unique_results.append(item)
    return unique_results