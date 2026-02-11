from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

# Initialize the database object [cite: 17]
db = SQLAlchemy()

class Product(db.Model):
    """
    Standardized Product Schema as per PRD requirements [cite: 27, 40]
    """
    # Primary Key for stable product IDs [cite: 27, 54]
    id = db.Column(db.Integer, primary_key=True)
    
    # Normalized name/title (canonicalized for fuzzy matching) [cite: 25, 36]
    name = db.Column(db.String(255), nullable=False)
    
    # Numeric price (float) normalized to a single currency [cite: 25, 35]
    price = db.Column(db.Float, nullable=False)
    
    # Standardized rating on a 0-5 scale [cite: 25, 36]
    rating = db.Column(db.Float, default=0.0)
    
    # Store source name (e.g., 'Amazon' or 'Flipkart') [cite: 31]
    source = db.Column(db.String(50), nullable=False)
    
    # Unique product URL to prevent duplicate entries in storage [cite: 27, 31]
    url = db.Column(db.String(1000), unique=True, nullable=False)
    
    # Timestamp for background refresh/TTL logic [cite: 40, 41]
    last_updated = db.Column(
        db.DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        """Helper to convert model instance to dictionary for JSON responses """
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "rating": self.rating,
            "source": self.source,
            "url": self.url,
            "last_updated": self.last_updated.isoformat()
        }