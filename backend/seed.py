import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Same try/except pattern as your main.py
try:
    from backend.database import SessionLocal, engine
    from backend import models
except ImportError:
    from database import SessionLocal, engine
    import models

db = SessionLocal()

apartments = [
    models.Property(id="a1b2c3d4-1111-4000-a000-000000000001", owner_id=1, title="Modern Apartment in Achrafieh", description="Bright 3-bedroom apartment with open-plan living, balcony overlooking the city, and 24/7 security.", price=250000, area=150, bedrooms=3, bathrooms=2, property_type="Apartment", status="Available", address="Achrafieh, Sassine Street", city="Beirut", lat=33.8886, lng=35.5278, main_image="/static/pics/beirut.jpeg"),
    models.Property(id="a1b2c3d4-2222-4000-a000-000000000002", owner_id=1, title="Sea View Apartment in Jounieh", description="Stunning 2-bedroom apartment with panoramic sea views. Fully renovated with modern kitchen.", price=180000, area=120, bedrooms=2, bathrooms=1, property_type="Apartment", status="Available", address="Jounieh, Kaslik Road", city="Jounieh", lat=33.9808, lng=35.6178, main_image="/static/pics/jonieh.jpeg"),
    models.Property(id="a1b2c3d4-3333-4000-a000-000000000003", owner_id=1, title="Cozy Apartment near Byblos Old Souk", description="Charming 2-bedroom apartment steps away from the historic port and old souk.", price=140000, area=100, bedrooms=2, bathrooms=1, property_type="Apartment", status="Available", address="Jbeil, Old Souk Area", city="Jbeil", lat=34.1236, lng=35.6511, main_image="/static/pics/jbeil.jpeg"),
    models.Property(id="a1b2c3d4-4444-4000-a000-000000000004", owner_id=1, title="Spacious Family Apartment in Tripoli", description="Large 4-bedroom apartment in Al-Mina district with city and sea views.", price=120000, area=200, bedrooms=4, bathrooms=2, property_type="Apartment", status="Available", address="Tripoli, Al-Mina Boulevard", city="Tripoli", lat=34.4365, lng=35.8497, main_image="/static/pics/tripoli.jpeg"),
    models.Property(id="a1b2c3d4-5555-4000-a000-000000000005", owner_id=1, title="Renovated Apartment in Saida", description="Newly renovated 3-bedroom apartment near Sidon Sea Castle with modern finishes.", price=95000, area=130, bedrooms=3, bathrooms=1, property_type="Apartment", status="Available", address="Saida, Riad El Solh Street", city="Sidon", lat=33.5633, lng=35.3758, main_image="/static/pics/sidon.jpeg"),
    models.Property(id="a1b2c3d4-6666-4000-a000-000000000006", owner_id=1, title="Luxury Apartment in Batroun", description="Premium 2-bedroom apartment with rooftop access and sea views near restaurants.", price=210000, area=110, bedrooms=2, bathrooms=1, property_type="Apartment", status="Available", address="Batroun, Main Street", city="Batroun", lat=34.2553, lng=35.6581, main_image="/static/pics/batroun.jpeg"),
]

db.add_all(apartments)
db.commit()
db.close()
print("✅ 6 apartments inserted!")