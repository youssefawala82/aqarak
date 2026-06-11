from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, Body
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import func
import random
import os
import shutil
import uuid
import re
try:
    from .database import SessionLocal, engine, get_db, Base
    from . import models, schemas
    from .schemas import ChatRequest
except ImportError:
    from database import SessionLocal, engine, get_db, Base
    import models
    import schemas
    from schemas import ChatRequest

app = FastAPI(title="Aqarak Professional API 2026", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "static/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("static/images", exist_ok=True)
os.makedirs("static/pics", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

models.Base.metadata.create_all(bind=engine)

SECRET_KEY = "aqarak_ultra_secure_key_2026"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
# ====================================================================
# ====================================================================

def create_access_token(data: dict):
    """إنشاء توكن JWT صالح لمدة 24 ساعة"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """استخراج المستخدم الحالي من التوكن"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid session",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def create_notification(db: Session, user_id: int, content: str):
    """إنشاء إشعار جديد لمستخدم معين"""
    new_notif = models.Notification(
        user_id=user_id,
        content=content,
        is_read=False
    )
    db.add(new_notif)

# ====================================================================
# ====================================================================

@app.on_event("startup")
def create_admin():
    """إنشاء حساب الأدمن الافتراضي عند تشغيل السيرفر"""
    db = SessionLocal()
    try:
        admin_user = db.query(models.User).filter(models.User.email == "admin@aqarak.com").first()

        if not admin_user:
            admin_user = models.User(
                username="youssef awala",
                email="admin@aqarak.com",
                password=pwd_context.hash("admin"),
                role="admin",
                phone="81772276"
            )
            db.add(admin_user)
        else:
            admin_user.phone = "81772276"

        db.commit()
    finally:
        db.close()

# ====================================================================
# ====================================================================

@app.post("/register/")
async def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    """تسجيل مستخدم جديد"""
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_role = user.role if user.role in ["user", "agent", "admin"] else "user"

    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password=hashed_password,
        role=user_role,
        phone=user.phone
    )
    db.add(db_user)
    db.commit()
    return {"message": "User created successfully"}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """تسجيل الدخول والحصول على توكن JWT"""
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=" Email or Password are Incorrect  ",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }


# ====================================================================
# ====================================================================

@app.get("/users/me")
def get_my_data(current_user: models.User = Depends(get_current_user)):
    """جلب بيانات المستخدم الحالي"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "phone": current_user.phone or "",
        "role": current_user.role,
        "profile_image": current_user.profile_image
    }


@app.put("/users/update-profile")
async def update_profile(
    username: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """تحديث بيانات الملف الشخصي"""
    if username:
        current_user.username = username

    if phone:
        clean_phone = "".join(filter(str.isdigit, phone))
        if len(clean_phone) < 7 or len(clean_phone) > 15:
            raise HTTPException(
                status_code=400,
                detail="Invalid phone number length. Must be between 7 and 15 digits."
            )
        current_user.phone = phone

    try:
        db.commit()
        db.refresh(current_user)
        return {"message": "Profile updated successfully"}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error during update")


@app.post("/users/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """رفع صورة شخصية للمستخدم"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:6]}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        current_user.profile_image = f"/static/images/{unique_filename}"
        db.commit()
        db.refresh(current_user)

        return {"message": "Avatar updated", "url": current_user.profile_image}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error during file upload")


@app.post("/users/change-password")
def change_password(
    data: schemas.PasswordChange,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """تغيير كلمة المرور"""
    if not pwd_context.verify(data.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    current_user.password = pwd_context.hash(data.new_password)

    try:
        db.commit()
        return {"message": "Password changed successfully"}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

# ====================================================================
# ====================================================================

@app.post("/properties/", response_model=schemas.PropertyOut)
def create_property(
    prop_data: schemas.PropertyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """إضافة عقار جديد (للوكلاء والأدمن فقط)"""
    if current_user.role not in ["agent", "admin"]:
        raise HTTPException(status_code=403, detail="غير مسموح لك بإضافة عقارات")

    prop_dict = prop_data.model_dump()
    lat_val = prop_dict.pop("lat", None)
    lng_val = prop_dict.pop("lng", None)

    new_prop = models.Property(
        id=str(uuid.uuid4()),
        owner_id=current_user.id,
        **prop_dict
    )
    if lat_val is not None:
        new_prop.lat = lat_val
    if lng_val is not None:
        new_prop.lng = lng_val
    db.add(new_prop)
    db.commit()
    db.refresh(new_prop)
    return new_prop
@app.get("/properties/", response_model=List[schemas.PropertyOut])
def list_properties(
    city: str = None,
    min_price: float = None,
    max_price: float = None,
    db: Session = Depends(get_db)
):
    """جلب كل العقارات مع فلاتر اختيارية"""
    query = db.query(models.Property)
    if city and city != "All":
        query = query.filter(models.Property.city == city)
    if min_price is not None:
        query = query.filter(models.Property.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Property.price <= max_price)
    return query.all()


@app.get("/my-properties", response_model=List[schemas.PropertyOut])
def get_my_properties(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """جلب عقارات المستخدم الحالي"""
    return db.query(models.Property).filter(
        models.Property.owner_id == current_user.id
    ).all()

@app.get("/properties/similar/{city}")
def get_similar_properties(
    city: str,
    exclude_id: str,
    db: Session = Depends(get_db)
):
    """جلب عقارات مشابهة في نفس المدينة"""
    return db.query(models.Property).filter(
        models.Property.city == city,
        models.Property.id != exclude_id
    ).limit(3).all()
# ====================================================================
# ====================================================================
MARKET_DATA = {
    # ── Greater Beirut — Districts ──────────────────────────────────────────
    "beirut": 2500, "ashrafieh": 3000, "hamra": 2400, "raouche": 3800,
    "verdun": 3200, "down town": 4500, "gemmayzeh": 2800, "koreitem": 3300,
    "mar mikhael": 2600, "badaro": 2200, "ain el mreisseh": 3500,
    "ras beirut": 3000, "tallet el khayyat": 2700, "moussaitbeh": 2000,
    "mazraa": 1800, "tarik el jdideh": 1500, "clemenceau": 3100,
    "sursock": 3400, "sioufi": 2900, "sodeco": 2500,

    # ── South Beirut / Baabda ─────────────────────────────────────────────
    "dahieh": 1100, "hadath": 1300, "hazmieh": 1800, "baabda": 1900,
    "khalde": 1200, "damour": 1200, "choueifat": 950, "naameh": 900,
    "bchamoun": 850, "aramoun": 800, "aley": 1100, "bhamdoun": 950,
    "souk el gharb": 1000, "deir el qamar": 1050, "ain anoub": 900,

    # ── Metn ──────────────────────────────────────────────────────────────
    "jdeideh": 1400, "antelias": 1600, "jal el dib": 1700, "mansourieh": 1400,
    "roumieh": 1600, "bikfaya": 1200, "zalka": 1500, "rabieh": 2800, "mtain": 900,
    "sin el fil": 1500, "dekwaneh": 1300, "beit mery": 1800, "broummana": 2000,
    "baouchrieh": 1200, "bourj hammoud": 1100, "fanar": 1350, "kornet chehwan": 2200,
    "monteverde": 1700, "bsalim": 1600, "naccache": 2500, "yarze": 2400,
    "dora": 1300, "dbayeh": 2200,

    # ── Keserwan ──────────────────────────────────────────────────────────
    "jounieh": 1700, "kaslik": 1900, "ajaltoun": 1100,
    "faraya": 1800, "kfardebian": 1700, "byblos": 1500, "amchit": 1300, "jbeil": 1500,
    "ghazir": 1400, "haret sakher": 1600, "zouk mosbeh": 1500, "zouk mikael": 1400,
    "adma": 2000, "sahel alma": 1800, "tabarja": 1300, "safra": 1500,
    "ballouneh": 1200, "jeita": 1300, "harissa": 1600, "daroun": 1350,

    # ── North Lebanon ─────────────────────────────────────────────────────
    "tripoli": 850, "el mina": 950, "koura": 900, "zgharta": 850,
    "batroun": 1700, "ehden": 1300, "bcharre": 1000, "akkar": 500, "halba": 650,
    "chekka": 800, "enfeh": 750, "amioun": 850, "kousba": 700,
    "douma": 900, "tannourine": 800, "hadchit": 600, "hasroun": 950,
    "tourza": 550, "sir el dinnieh": 500, "kfarhata": 450,

    # ── South Lebanon ─────────────────────────────────────────────────────
    "sidon": 1000, "saida": 1000, "tyre": 1100, "sour": 1100, "nabatieh": 800,
    "jezzin": 950, "ghazieh": 900, "marjayoun": 750, "bint jbeil": 700, "touline": 600,
    "aynatha": 650, "khiam": 650, "hasbaya": 700, "tebnine": 600,
    "deir ez zahrani": 750, "maghdouche": 850, "abra": 950, "hlalieh": 550,
    "jouaya": 600, "arnoun": 500, "kfar tebnit": 550,

    # ── Bekaa Valley ──────────────────────────────────────────────────────
    "zahle": 850, "baalbek": 650, "chtoura": 1000, "bar elias": 750,
    "rashaya": 700, "hermel": 550, "jebb jannine": 800,
    "aanjar": 700, "saghbine": 650, "joub jannine": 800, "machghara": 600,
    "majdel aanjar": 650, "kab elias": 700, "ablah": 600, "rayak": 550,
    "taanayel": 750, "ferzol": 600, "deir el ahmar": 500, "laboueh": 450,

    # ── Chouf ─────────────────────────────────────────────────────────────
    "beiteddine": 1100, "baakline": 900, "chouf": 850, "moukhtara": 950,
    "aitat": 800, "kfarnabrakh": 750, "niha": 700, "chhim": 800,
    "jiye": 950, "rmeileh": 900, "saadiyat": 750, "barja": 700,
}


LEBANESE_REGIONS = list(MARKET_DATA.keys())



@app.get("/properties/{property_id}", response_model=schemas.PropertyOut)
def get_property(property_id: str, db: Session = Depends(get_db)):
    """جلب تفاصيل عقار واحد"""
    prop = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


@app.put("/properties/{property_id}")
async def update_property(
    property_id: str,
    property_data: schemas.PropertyUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """تحديث بيانات عقار"""
    db_prop = db.query(models.Property).filter(models.Property.id == property_id).first()

    if not db_prop:
        raise HTTPException(status_code=404, detail="Property not found")

    if db_prop.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = property_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_prop, key, value)

    db.commit()
    db.refresh(db_prop)
    return {"message": "Property updated successfully", "property_id": db_prop.id}


@app.delete("/properties/{property_id}")
def delete_property(
    property_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """حذف عقار (للمالك أو الأدمن)"""
    prop = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    if prop.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")

    db.delete(prop)
    db.commit()
    return {"detail": "Deleted successfully"}


@app.post("/properties/{property_id}/upload-image/")
def upload_property_image(
    property_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """رفع صورة رئيسية لعقار"""
    prop = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    if prop.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{property_id}_{uuid.uuid4().hex[:6]}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    prop.main_image = f"/static/images/{unique_filename}"
    db.commit()
    return {"status": "success", "url": prop.main_image}



@app.post("/ai/predict-price")
def predict_price(
    area:          float = Form(...),
    city:          str   = Form(...),
    property_type: str   = Form("Apartment"),
    bedrooms:      int   = Form(0),
    bathrooms:     int   = Form(0),
    lat:           float = Form(None),
    lng:           float = Form(None)
):
    """Predict property price based on area, city, type, bedrooms and bathrooms."""

    # Step 1 — Base price per m² from market data
    city_key     = city.lower().strip()
    base_price   = 750
    found_region = "General Lebanon"
    for region, price in MARKET_DATA.items():
        if region in city_key or city_key in region:
            base_price   = price
            found_region = region
            break

    # Step 2 — Property type multiplier
    TYPE_MULTIPLIERS = {
        "apartment":  1.00, "villa":     1.85, "house":     1.50,
        "studio":     0.75, "duplex":    1.60, "penthouse": 2.20,
        "office":     1.30, "shop":      1.15, "land":      0.55,
        "chalet":     1.40, "townhouse": 1.45, "warehouse": 0.90,
        "farm":       0.70,
    }
    type_multiplier = TYPE_MULTIPLIERS.get(property_type.lower().strip(), 1.00)

    # Step 3 — Bedroom & bathroom bonuses
    bedroom_bonus  = 1 + (min(bedrooms,  6) * 0.06)
    bathroom_bonus = 1 + (min(bathrooms, 4) * 0.03)

    # Step 4 — Location bonus (central Beirut premium)
    location_bonus = 1.0
    if lat and lng:
        if 33.88 <= lat <= 33.91 and 35.47 <= lng <= 35.53:
            location_bonus = 1.20

    # Step 5 — Slight market variance ±3%
    variance = random.uniform(0.97, 1.03)

    suggested_price = (
        area * base_price * type_multiplier *
        bedroom_bonus * bathroom_bonus *
        location_bonus * variance
    )

    return {
        "suggested_price":        round(suggested_price, 2),
        "region_detected":        found_region,
        "base_rate_used":         base_price,
        "type_multiplier":        type_multiplier,
        "bedroom_bonus":          f"+{int((bedroom_bonus  - 1) * 100)}%",
        "bathroom_bonus":         f"+{int((bathroom_bonus - 1) * 100)}%",
        "location_bonus_applied": f"+{int((location_bonus - 1) * 100)}%"
    }


PLATFORM_FAQ = {
    "book":        "To book a viewing: open the property you like → click 'Book Viewing' → choose your payment preference → submit. The agent will be notified instantly.",
    "register":    "Click 'Register' at the top of the page. Enter your name, email, and password. You can sign up as a regular seeker or as a real estate agent.",
    "login":       "Click 'Login' and enter your email and password. If you forgot your password, contact support.",
    "favorite":    "Click the heart icon ❤️ on any property to save it to your favorites. View all saved properties from the 'Favorites' page in the navbar.",
    "agent":       "Agents can list properties, edit them, manage received bookings, and contact seekers from their dashboard.",
    "predict":     "The AI price estimator gives you an estimated property value based on city and area size. Open any property and scroll to the AI Analysis section to see it.",
    "contact":     "Open any property's details page and scroll down — you'll find the agent's contact information and a booking button to request a viewing.",
    "installment": "Aqarak supports installment payment plans for 10 to 15 years. When you book a property, select 'Installments' and choose your preferred duration.",
    "map":         "Every property shows its exact location on Google Maps. Open the property details page and click 'View on Map'.",
    "book":        "To book a viewing: open the property you like → click 'Book Viewing' → choose your payment preference → submit. The agent will be notified instantly.",
    "cancel":      "You can cancel a pending booking from your 'My Bookings' page. Confirmed bookings require contacting the agent directly.",
    "search":      "Use the search bar on the home page to filter by city, property type, price range, and number of bedrooms. Results update instantly.",
    "price":       "Property prices on Aqarak are listed in USD. Each listing shows the total price. You can also request an AI price estimate on the details page.",
    "cities":      "Aqarak covers all major Lebanese cities including Beirut, Jounieh, Tripoli, Sidon, Batroun, Jbeil, Zahle, Aley, Broummana, and more.",
    "types":       "We list all property types: Apartments, Villas, Houses, Studios, Duplexes, Penthouses, Offices, Shops, Land, and Chalets.",
    "notification":"You receive a notification when an agent responds to your booking or when new properties matching your interest are added.",
    "profile":     "Go to your Profile page to update your name, phone number, profile photo, and change your password.",
    "safe":        "Aqarak is a listing platform. We recommend meeting agents in public places and verifying property documents before any payment.",
}
 
FAQ_KEYWORDS = {
    "book":         ["book", "booking", "reserve", "viewing", "schedule", "visit", "appointment"],
    "cancel":       ["cancel", "cancellation", "remove booking", "delete booking"],
    "register":     ["register", "sign up", "signup", "create account", "new account", "join"],
    "login":        ["login", "log in", "sign in", "signin", "access account"],
    "favorite":     ["favorite", "favourites", "saved", "heart", "wishlist", "save property"],
    "agent":        ["agent", "seller", "owner", "landlord", "list property", "add property"],
    "predict":      ["predict", "estimate", "valuation", "ai price", "worth", "value", "appraisal"],
    "contact":      ["contact", "call", "phone", "reach", "message agent", "whatsapp"],
    "installment":  ["installment", "installments", "payment plan", "5 years", "10 years", "monthly", "finance"],
    "map":          ["map", "location", "google maps", "where", "directions", "navigate"],
    "search":       ["search", "filter", "find", "look for", "browse", "how to search"],
    "price":        ["price", "cost", "how much", "pricing", "budget", "affordable", "cheap", "expensive"],
    "cities":       ["cities", "city", "areas", "locations", "neighborhoods", "available in"],
    "types":        ["types", "type of property", "villa", "apartment", "studio", "duplex", "penthouse", "land"],
    "notification": ["notification", "alert", "notify", "update", "message"],
    "profile":      ["profile", "account", "username", "photo", "picture", "password", "settings"],
    "safe":         ["safe", "scam", "trust", "secure", "verified", "legit", "reliable"],
}
 
LEBANESE_CITIES = [
    "beirut", "ashrafieh", "hamra", "raouche", "verdun", "down town", "gemmayzeh",
    "koreitem", "mar mikhael", "badaro", "ain el mreisseh", "ras beirut",
    "tallet el khayyat", "moussaitbeh", "mazraa", "tarik el jdideh", "clemenceau",
    "sursock", "sioufi", "sodeco","dahieh", "hadath", "hazmieh", "baabda", "khalde",
    "damour", "choueifat", "naameh", "bchamoun", "aramoun", "aley", "bhamdoun", "souk el gharb",
    "deir el qamar", "ain anoub","jdeideh", "antelias", "jal el dib", "mansourieh", "roumieh", "bikfaya",
    "zalka", "rabieh", "mtain", "sin el fil", "dekwaneh", "beit mery", "broummana",
    "baouchrieh", "bourj hammoud", "fanar", "kornet chehwan", "monteverde", "bsalim",
    "naccache", "yarze", "dora", "dbayeh",
    "jounieh", "kaslik", "ajaltoun", "faraya", "kfardebian", "byblos", "amchit",
    "jbeil", "ghazir", "haret sakher", "zouk mosbeh", "zouk mikael", "adma",
    "sahel alma", "tabarja", "safra", "ballouneh", "jeita", "harissa", "daroun",
    "tripoli", "el mina", "koura", "zgharta", "batroun", "ehden", "bcharre",
    "akkar", "halba", "chekka", "enfeh", "amioun", "kousba", "douma", "tannourine",
    "hadchit", "hasroun", "tourza", "sir el dinnieh", "kfarhata",
    "sidon", "saida", "tyre", "sour", "nabatieh", "jezzin", "ghazieh", "marjayoun",
    "bint jbeil", "touline", "aynatha", "khiam", "hasbaya", "tebnine",
    "deir ez zahrani", "maghdouche", "abra", "hlalieh", "jouaya", "arnoun", "kfar tebnit",
    "zahle", "baalbek", "chtoura", "bar elias", "rashaya", "hermel", "jebb jannine",
    "aanjar", "saghbine", "joub jannine", "machghara", "majdel aanjar", "kab elias",
    "ablah", "rayak", "taanayel", "ferzol", "deir el ahmar", "laboueh",
    "beiteddine", "baakline", "chouf", "moukhtara", "aitat", "kfarnabrakh",
    "niha", "chhim", "jiye", "rmeileh", "saadiyat", "barja",
]
 
PROPERTY_TYPES = [
    "apartment", "villa", "house", "land", "office", "shop", "studio",
    "شقة", "فيلا", "بيت", "أرض", "مكتب", "محل", "ستوديو"
]
 
TYPE_MAP = {
    "أرض": "land", "مكتب": "office", "محل": "shop", "ستوديو": "studio"
}
 
 
def detect_language(text):
    
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    return "ar" if arabic_chars > len(text) * 0.3 else "en"
 
 
def find_city_in_message(message):
    """البحث عن اسم مدينة في الرسالة"""
    msg_lower = message.lower()
    for city in LEBANESE_CITIES:
        if city in msg_lower:
            return city
    return None
 
 
def find_type_in_message(message):
    """البحث عن نوع عقار في الرسالة"""
    msg_lower = message.lower()
    for ptype in PROPERTY_TYPES:
        if ptype in msg_lower:
            return TYPE_MAP.get(ptype, ptype)
    return None
 
 
def find_price_range(message):
    """استخراج نطاق السعر من الرسالة"""
    msg_lower = message.lower()
    
    under_match = re.search(r'(?:under|less than|below|أقل من|تحت)\s*\$?([\d,]+)\s*k?', msg_lower)
    if under_match:
        val = int(under_match.group(1).replace(',', ''))
        if val < 1000:
            val *= 1000  # 200k → 200000
        return (0, val)
    
    above_match = re.search(r'(?:above|more than|over|أكثر من|فوق)\s*\$?([\d,]+)\s*k?', msg_lower)
    if above_match:
        val = int(above_match.group(1).replace(',', ''))
        if val < 1000:
            val *= 1000
        return (val, 99999999)
    
    # "between X and Y"
    between_match = re.search(r'(?:between|بين)\s*\$?([\d,]+)\s*k?\s*(?:and|و|-)\s*\$?([\d,]+)\s*k?', msg_lower)
    if between_match:
        low = int(between_match.group(1).replace(',', ''))
        high = int(between_match.group(2).replace(',', ''))
        if low < 1000: low *= 1000
        if high < 1000: high *= 1000
        return (low, high)
    
    return None
 
 
def match_faq(message):
    """مطابقة الرسالة مع الأسئلة الشائعة"""
    msg_lower = message.lower()
    best_topic = None
    best_score = 0
    
    for topic, keywords in FAQ_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in msg_lower)
        if score > best_score:
            best_score = score
            best_topic = topic
    
    return best_topic if best_score > 0 else None
 
 
# ---------- الـ Endpoint ----------
 
@app.post("/ai/chat")
async def ai_chat(request: ChatRequest, db: Session = Depends(get_db)):

    message = request.message.strip()
    if not message:
        return {"reply": "Please type a message! 😊"}

    msg_lower = message.lower()

    # ===== 1) Greetings =====
    greetings = ["hello", "hi", "hey", "good morning", "good evening", "howdy", "sup", "greetings"]
    if any(g in msg_lower for g in greetings):
        return {"reply": "Hello! 👋 I'm Aqarak's smart assistant. How can I help you today?\n\nYou can ask me about:\n🏠 Properties in any Lebanese city\n💰 Prices and AI valuations\n📋 How to book, search, or register\n❤️ Favorites, installments, and more"}

    # ===== 2) Platform FAQ =====
    faq_topic = match_faq(message)
    if faq_topic:
        return {"reply": PLATFORM_FAQ[faq_topic]}
    
    # ===== 3) Property search =====
    city = find_city_in_message(message)
    prop_type = find_type_in_message(message)
    price_range = find_price_range(message)
    
    # If search keywords detected (city, type, price)
    if city or prop_type or price_range or any(w in msg_lower for w in [
        "property", "properties", "show", "find", "search", "available",
        
        "cheapest", "expensive", "how many", "most expensive", "affordable"
    ]):
        query = db.query(models.Property)
        
        if city:
            query = query.filter(func.lower(models.Property.city).contains(city.lower()))
        if prop_type:
            query = query.filter(func.lower(models.Property.property_type) == prop_type.lower())
        if price_range:
            query = query.filter(
                models.Property.price >= price_range[0],
                models.Property.price <= price_range[1]
            )
        
        properties = query.order_by(models.Property.created_at.desc()).limit(5).all()
        total_count = query.count()
        
        if not properties:
                filters = []
                if city: filters.append(f"in {city.title()}")
                if prop_type: filters.append(f"of type {prop_type}")
                if price_range: filters.append(f"between ${price_range[0]:,} and ${price_range[1]:,}")
                filter_text = " ".join(filters) if filters else ""
                return {"reply": f"No properties found {filter_text} right now 😔\n\nTry:\n• A different city (Beirut, Jounieh, Tripoli...)\n• A wider price range\n• A different property type"}
        
        # Build response
        header = f"🏠 Found {total_count} propert{'y' if total_count == 1 else 'ies'}"
        if city: header += f" in {city.title()}"
        if prop_type: header += f" ({prop_type})"
        header += ":\n\n"
        
        listings = ""
        for i, p in enumerate(properties, 1):
            price_formatted = f"${p.price:,.0f}" if p.price else "Price N/A"
            area_text = f"{p.area} sqm" if p.area else ""
            listings += f"{i}. {p.title or 'Untitled'}\n"
            listings += f"   📍 {p.city or 'N/A'} | 💰 {price_formatted}"
            if area_text:
                listings += f" | 📐 {area_text}"
            listings += "\n"
            if p.bedrooms:
                listings += f"   🛏️ {p.bedrooms} bed"
                if p.bathrooms:
                    listings += f" · 🚿 {p.bathrooms} bath"
                listings += "\n"
            listings += "\n"
        
        if total_count > 5:
            listings += f"... and {total_count - 5} more. Browse the site to see all!"
        
        return {"reply": header + listings}
    
    # ===== 4) Platform stats =====
    if any(w in msg_lower for w in ["stats", "statistics", "how many", "total", "count"]):
        total = db.query(func.count(models.Property.id)).scalar()
        cities = db.query(func.count(func.distinct(models.Property.city))).scalar()
        avg_price = db.query(func.avg(models.Property.price)).scalar()
        reply = f"📊 Aqarak Platform Stats:\n\n"
        reply += f"🏠 Total properties listed: {total}\n"
        reply += f"🌆 Cities covered: {cities}\n"
        if avg_price:
            reply += f"💰 Average listing price: ${avg_price:,.0f}\n"
        return {"reply": reply}
    
    # ===== 5) City price stats =====
    if any(w in msg_lower for w in ["price", "cost", "expensive", "cheap", "affordable", "budget"]):
        city = find_city_in_message(message)
        if city:
            avg = db.query(func.avg(models.Property.price)).filter(func.lower(models.Property.city).contains(city.lower())).scalar()
            count = db.query(func.count(models.Property.id)).filter(func.lower(models.Property.city).contains(city.lower())).scalar()
            min_price = db.query(func.min(models.Property.price)).filter(func.lower(models.Property.city).contains(city.lower())).scalar()
            max_price = db.query(func.max(models.Property.price)).filter(func.lower(models.Property.city).contains(city.lower())).scalar()
            if count > 0:
                reply  = f"💰 Property prices in {city.title()}:\n\n"
                reply += f"📊 Listed properties: {count}\n"
                reply += f"⬇️ Lowest: ${min_price:,.0f}\n"
                reply += f"⬆️ Highest: ${max_price:,.0f}\n"
                reply += f"📈 Average: ${avg:,.0f}\n"
                reply += f"\nFor a precise estimate, try the AI Price Prediction on any property's details page."
                return {"reply": reply}
        return {"reply": "💰 Specify a city for accurate pricing!\n\nExample: 'prices in Beirut' or 'cheapest in Jounieh'"}
    
    # ===== 6) Help =====
    if any(w in msg_lower for w in ["help", "what can you", "what do you do", "commands"]):
        return {"reply": "🤖 I'm Aqarak's assistant! I can help with:\n\n🔍 Property search — try: 'apartments in Beirut'\n💰 Pricing — try: 'prices in Jounieh'\n📋 How to book, register, or use the platform\n❤️ Favorites, installments, and more\n📊 Platform statistics\n\nAsk me anything!"}

    # ===== 7) Default fallback =====
    return {"reply": "🤔 I didn't quite understand that.\n\nTry:\n• 'Show apartments in Beirut'\n• 'Prices in Jounieh'\n• 'How do I book a property?'\n• 'What installment plans are available?'\n\nOr type 'help' to see everything I can do."}
 




# ====================================================================
# ====================================================================

@app.post("/properties/{property_id}/favorite")
def toggle_favorite(
    property_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Toggle property favorite"""
    fav = db.query(models.Favorite).filter(
        models.Favorite.user_id == current_user.id,
        models.Favorite.property_id == property_id
    ).first()

    if fav:
        db.delete(fav)
        db.commit()
        return {"status": "removed"}

    new_fav = models.Favorite(user_id=current_user.id, property_id=property_id)
    db.add(new_fav)
    db.commit()
    return {"status": "added"}


@app.get("/favorites/check/{property_id}")
def check_favorite_status(
    property_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Check if property is favorited"""
    fav = db.query(models.Favorite).filter(
        models.Favorite.user_id == current_user.id,
        models.Favorite.property_id == property_id
    ).first()
    return {"is_favorite": fav is not None}


@app.get("/my-favorites")
def get_my_favorites(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get user favorites list"""
    return db.query(models.Property).join(models.Favorite).filter(
        models.Favorite.user_id == current_user.id
    ).all()


# ====================================================================
# ====================================================================

@app.post("/bookings/create")
def create_booking(
    booking_data: schemas.BookingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a booking request and notify agent"""
    prop = db.query(models.Property).filter(
        models.Property.id == booking_data.property_id
    ).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    new_booking = models.Booking(
        property_id=booking_data.property_id,
        user_id=current_user.id,
        payment_preference=booking_data.payment_preference,
        install_years=booking_data.install_years
    )
    db.add(new_booking)

    notif_text = (
        f"New booking request for '{prop.title}' from user {current_user.username}. "
        f"Payment: {booking_data.payment_preference}"
    )
    create_notification(db, user_id=prop.owner_id, content=notif_text)

    try:
        db.commit()
        return {"message": "Booking request sent and Agent notified successfully"}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process booking and notification")


@app.get("/my-bookings")
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get bookings received on current user properties (for agents/admin)"""
    bookings = db.query(models.Booking).join(models.Property).filter(
        models.Property.owner_id == current_user.id
    ).all()

    return [{
        "id": b.id,
        "client_name": b.user.username if b.user else "Unknown",
        "client_email": b.user.email if b.user else "N/A",
        "client_phone": b.user.phone if b.user else "Not Provided",
        "property_title": b.property.title,
        "payment_preference": b.payment_preference,
        "install_years": b.install_years,
        "status": b.status,
        "date": b.created_at.strftime("%Y-%m-%d %H:%M")
    } for b in bookings]


@app.get("/my-booking-requests")
def get_my_booking_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get bookings made BY the current user as a seeker"""
    bookings = db.query(models.Booking).filter(
        models.Booking.user_id == current_user.id
    ).all()

    return [{
        "id": b.id,
        "property_id": b.property_id,
        "property_title": b.property.title if b.property else "Unknown",
        "property_city": b.property.city if b.property else "",
        "payment_preference": b.payment_preference,
        "install_years": b.install_years,
        "status": b.status,
        "booking_date": b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else None,
        "notes": None
    } for b in bookings]

@app.put("/bookings/{booking_id}/status")
def update_booking_status(
    booking_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Agent/admin confirms or cancels a booking — seeker sees the updated status"""
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
 
    # Only the property owner or admin can update status
    if booking.property.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
 
    new_status = data.get("status", "").lower()
    if new_status not in ["confirmed", "cancelled", "pending"]:
        raise HTTPException(status_code=400, detail="Invalid status")
 
    booking.status = new_status
    db.commit()
 
    # Notify the seeker
    notif_text = (
        f"Your booking for '{booking.property.title}' has been "
        f"{'✅ confirmed' if new_status == 'confirmed' else '❌ cancelled'} by the agent."
    )
    create_notification(db, user_id=booking.user_id, content=notif_text)
    db.commit()
 
    return {"message": f"Booking {new_status} successfully"}


@app.delete("/bookings/{booking_id}")
def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a booking — allowed by the seeker who made it, the property owner, or admin"""
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Request not found")
 
    if (booking.user_id != current_user.id and
        booking.property.owner_id != current_user.id and
        current_user.role != "admin"):
        raise HTTPException(status_code=403, detail="Unauthorized")
 
    db.delete(booking)
    db.commit()
    return {"message": "Request removed"}




# ====================================================================

@app.get("/notifications")
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get current user notifications"""
    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    ).order_by(models.Notification.created_at.desc()).all()

    return [
        {
            "id": n.id,
            "content": n.content,
            "is_read": n.is_read,
            "date": n.created_at.strftime("%Y-%m-%d %H:%M")
        } for n in notifications
    ]


@app.put("/notifications/read-all")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark all notifications as read"""
    db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"status": "success"}




@app.put("/notifications/{notif_id}/read")
def mark_notification_as_read(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark a notification as read"""
    notif = db.query(models.Notification).filter(
        models.Notification.id == notif_id,
        models.Notification.user_id == current_user.id
    ).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"status": "success"}



@app.get("/admin/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get admin dashboard statistics"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access Denied: Admins Only")

    recent_properties = db.query(models.Property).order_by(
        models.Property.created_at.desc()
    ).limit(5).all()

    return {
        "users_count": db.query(models.User).count(),
        "properties_count": db.query(models.Property).count(),
        "favorites_count": db.query(models.Favorite).count(),
        "recent_properties": [
            {
                "id": p.id,
                "title": p.title,
                "price": float(p.price),
                "city": p.city,
                "owner_name": (
                    db.query(models.User.username)
                    .filter(models.User.id == p.owner_id)
                    .scalar() or "Unknown"
                )
            } for p in recent_properties
        ]
    }

@app.post("/admin/add-agent")
def add_agent(
    agent_data: schemas.UserRegister,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Add a new agent (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can add agents")

    existing_user = db.query(models.User).filter(
        models.User.email == agent_data.email
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_agent = models.User(
        username=agent_data.username,
        email=agent_data.email,
        password=pwd_context.hash(agent_data.password),
        phone=agent_data.phone,
        role="agent"
    )

    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)

    return {"message": "Agent created successfully", "agent_id": new_agent.id}


@app.get("/admin/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all users (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    users = db.query(models.User).all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "phone": u.phone,
            "role": u.role,
            "profile_image": u.profile_image
        } for u in users
    ]
@app.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only admins can delete accounts"
        )

    user_to_delete = db.query(models.User).filter(models.User.id == user_id).first()

    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user_to_delete.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the main admin account"
        )

    try:
        db.delete(user_to_delete)
        db.commit()
        return {"message": f"User with ID {user_id} deleted successfully"}
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while deleting the user from the database"
        )
    
@app.get("/admin/bookings-stats")
def get_bookings_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get booking statistics (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access Denied: Admins Only")
 
    all_bookings = db.query(models.Booking).all()
    cash_count = sum(1 for b in all_bookings if b.payment_preference == "Full Cash")
    install_count = sum(1 for b in all_bookings if b.payment_preference == "Installments")
 
    install_years_dist = {}
    for b in all_bookings:
        if b.install_years:
            key = f"{b.install_years}y"
            install_years_dist[key] = install_years_dist.get(key, 0) + 1
 
    return {
        "total_bookings": len(all_bookings),
        "payment_breakdown": {
            "cash": cash_count,
            "installments": install_count
        },
        "installment_years": install_years_dist
    }