from datetime import datetime, timedelta
from flask import Flask, jsonify
from models import db, Product
from scrapers import fetch_single_product_update # You'll add this to scrapers.py

@app.route('/products/<int:id>', methods=['GET'])
def get_product_detail(id):
    # 1. Fetch from Database
    product = Product.query.get_or_404(id)
    
    # 2. Check if data is stale (Older than 10 minutes)
    # PRD Requirement: Trigger refresh if stale beyond TTL [cite: 41]
    is_stale = datetime.utcnow() > (product.last_updated + timedelta(minutes=10))
    
    if is_stale:
        print(f"Product {id} is stale. Refreshing data...")
        # Scrape only this specific URL to save time/resources
        updated_info = fetch_single_product_update(product.url, product.source)
        
        if updated_info:
            product.price = updated_info['price']
            product.rating = updated_info['rating']
            product.last_updated = datetime.utcnow()
            db.session.commit()

    # 3. Return full normalized record [cite: 40]
    return jsonify({
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "rating": product.rating,
        "source": product.source,
        "url": product.url,
        "last_updated": product.last_updated.isoformat()
    })