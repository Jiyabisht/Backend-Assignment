from flask import Flask, request, jsonify
from cachetools import TTLCache
from scrapers import run_concurrent_scrapers
from models import db, Product
from datetime import datetime, timezone
from difflib import SequenceMatcher
import os

app = Flask(__name__)

# TTL Cache: 10-minute window for recent queries [cite: 21, 48]
search_cache = TTLCache(maxsize=100, ttl=600)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'products.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def get_similarity(a, b):
    """Fuzzy matching as per requirements[cite: 19, 37]."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def deduplicate_results(results, threshold=0.7):
    """Clusters and merges near-duplicates using fuzzy logic."""
    unique_results = []
    for item in results:
        is_duplicate = False
        for existing in unique_results:
            if get_similarity(item['name'], existing['name']) > threshold:
                is_duplicate = True
                # Keep the cheaper option if they are near-duplicates [cite: 35]
                if item['price'] < existing['price']:
                    existing['price'] = item['price']
                    existing['source'] = item['source']
                break
        if not is_duplicate:
            unique_results.append(item)
    return unique_results

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=20, type=int)

    if not query:
        return jsonify({"error": "Missing query"}), 400
    
    # Check cache or scrape
    if query not in search_cache:
        raw_results = run_concurrent_scrapers(query)
        all_results = deduplicate_results(raw_results)
        
        with app.app_context():
            for item in all_results:
                if not item.get('url'): continue
                existing = Product.query.filter_by(url=item['url']).first()
                if not existing:
                    new_prod = Product(
                        name=item['name'], price=item['price'],
                        source=item['source'], url=item['url']
                    )
                    db.session.add(new_prod)
            db.session.commit()
        search_cache[query] = True

    # Fetch from DB to ensure IDs are present
    db_products = Product.query.filter(Product.name.contains(query)).all()
    db_products.sort(key=lambda x: x.price) 
    
    # Calculate Pagination
    total_results = len(db_products)
    total_pages = (total_results + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = db_products[start:end]

    return jsonify({
        "results": [p.to_dict() for p in paginated_items],
        "metadata": {
            "page": page,
            "per_page": per_page,
            "total_results": total_results,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "next_page": f"/search?q={query}&page={page+1}" if page < total_pages else None
        }
    })

@app.route('/products/<int:id>', methods=['GET'])
def get_product_detail(id):
    """Returns normalized record and last_updated timestamp[cite: 40, 67]."""
    product = Product.query.get(id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    return jsonify({
        "id": product.id, 
        "name": product.name,
        "price": product.price, 
        "rating": product.rating,
        "source": product.source, 
        "url": product.url,
        "last_updated": product.last_updated.isoformat() if product.last_updated else None
    })

@app.route('/compare', methods=['GET'])
def compare_products():
    # 1. Properly extract IDs from the request 
    ids_param = request.args.get('ids', '')
    if not ids_param:
        return jsonify({"error": "Provide product IDs"}), 400
        
    # Convert string IDs to integers safely [cite: 65]
    try:
        ids = [int(i.strip()) for i in ids_param.split(',') if i.strip()]
    except ValueError:
        return jsonify({"error": "Invalid ID format"}), 400

    # 2. Query the database [cite: 27, 39]
    products = Product.query.filter(Product.id.in_(ids)).all()
    
    if not products:
        # Structured error for no results as per PRD [cite: 44, 68]
        return jsonify({"error": "No products found"}), 404

    # 3. Highlight the best-by metric (price) 
    cheapest = min(products, key=lambda x: x.price)

    return jsonify({
        "comparison": [
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "rating": p.rating,
                "source": p.source,
                "url": p.url,
                "is_cheapest": p.id == cheapest.id
            } for p in products
        ]
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)