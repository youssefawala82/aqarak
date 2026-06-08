from .database import Base
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, Numeric, func
from sqlalchemy.orm import relationship
import datetime
import uuid

# 1. جدول المستخدمين
class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default="user") # user, agent, admin
    phone = Column(String(20), nullable=True)
    profile_image = Column(String(500), nullable=True)

    # العلاقات
    properties = relationship("Property", back_populates="owner")
    favorites = relationship("Favorite", back_populates="user")
    bookings = relationship("Booking", back_populates="user") 
    reviews = relationship("Review", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    search_history = relationship("SearchHistory", back_populates="user")

# 2. جدول العقارات
# ... (نفس البداية في الموديل الخاص بك)

class Property(Base):
    __tablename__ = "properties"
    __table_args__ = {'extend_existing': True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE")) 
    title = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(15, 2), nullable=False)
    area = Column(Float)
    bedrooms = Column(Integer, default=0)
    bathrooms = Column(Integer, default=0)
    property_type = Column(String(50)) 
    status = Column(String(50), default="Available") 
    address = Column(String(500))
    city = Column(String(100))
    
    # إضافة حقول الإحداثيات لضمان عمل الخريطة و AI التنبؤ
    lat = Column(Float, nullable=True) 
    lng = Column(Float, nullable=True)
    
    main_image = Column(String(500), nullable=True) 
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


    # العلاقات
    owner = relationship("User", back_populates="properties")
    # تم إضافة cascade هنا لضمان حذف الصور الإضافية عند حذف العقار
    ai_insight = relationship("AIInsight", back_populates="property", uselist=False)
    reviews = relationship("Review", back_populates="property")
    features = relationship("PropertyFeature", back_populates="property")
    enquiries = relationship("Enquiry", back_populates="property")
    bookings = relationship("Booking", back_populates="property")


# 4. تحليل الذكاء الاصطناعي (AI Insights)
class AIInsight(Base):
    __tablename__ = "ai_insights"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    property_id = Column(String(36), ForeignKey('properties.id', ondelete="CASCADE"), unique=True)
    predicted_price = Column(Numeric(15, 2))
    price_valuation = Column(String(50)) # Underpriced, Fair, Overpriced
    confidence_score = Column(Float)
    
    property = relationship("Property", back_populates="ai_insight")

# 5. المفضلة (Favorites)
class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    property_id = Column(String(36), ForeignKey('properties.id', ondelete="CASCADE"))
    
    user = relationship("User", back_populates="favorites")

# 6. الحجوزات (Bookings)
class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(String(36), ForeignKey("properties.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    payment_preference = Column(String(50), default="Full Cash") 
    install_years = Column(Integer, nullable=True) 
    status = Column(String(50), default="pending") # pending, approved, rejected
    created_at = Column(DateTime, server_default=func.now())

    property = relationship("Property", back_populates="bookings")
    user = relationship("User", back_populates="bookings")

# 7. التقييمات (Reviews)
class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    property_id = Column(String(36), ForeignKey('properties.id', ondelete="CASCADE"))
    rating = Column(Integer) 
    comment = Column(Text)
    
    user = relationship("User", back_populates="reviews")
    property = relationship("Property", back_populates="reviews")

# 8. الاستفسارات (Enquiries)
class Enquiry(Base):
    __tablename__ = "enquiries"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    property_id = Column(String(36), ForeignKey('properties.id', ondelete="CASCADE"))
    sender_name = Column(String(255))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    property = relationship("Property", back_populates="enquiries")

# 9. الإشعارات (Notifications)
class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    content = Column(String(500))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")

# 10. سجل البحث (Search History)
class SearchHistory(Base):
    __tablename__ = "search_history"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    query = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="search_history")

# 11. ميزات العقار (Property Features)
class PropertyFeature(Base):
    __tablename__ = "property_features"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    property_id = Column(String(36), ForeignKey('properties.id', ondelete="CASCADE"))
    feature_name = Column(String(100)) # e.g., "Swimming Pool", "Garden"
    
    property = relationship("Property", back_populates="features")