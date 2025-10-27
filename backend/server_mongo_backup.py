from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app
app = FastAPI(title="Sistema de Escalas Distritais")
api_router = APIRouter(prefix="/api")

# Enums
class UserRole(str, Enum):
    PASTOR_DISTRITAL = "pastor_distrital"
    LIDER_IGREJA = "lider_igreja"
    PREGADOR = "pregador"
    CANTOR = "cantor"
    MEMBRO = "membro"

class ScheduleStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    ACTIVE = "active"

class ScheduleItemStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REFUSED = "refused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class GenerationMode(str, Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"

# ===== MODELS =====

class ServiceSchedule(BaseModel):
    day_of_week: str  # 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
    time: str  # '19:00'

class UnavailablePeriod(BaseModel):
    start_date: str
    end_date: str
    reason: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: UserRole
    district_id: Optional[str] = None
    church_id: Optional[str] = None
    is_preacher: bool = False
    is_singer: bool = False
    preacher_score: float = 50.0
    singer_score: float = 50.0
    unavailable_periods: List[UnavailablePeriod] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True

class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: UserRole
    district_id: Optional[str] = None
    church_id: Optional[str] = None
    is_preacher: bool = False
    is_singer: bool = False

class UserLogin(BaseModel):
    username: str
    password: str

class District(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    pastor_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True

class DistrictCreate(BaseModel):
    name: str
    pastor_id: str

class Church(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    district_id: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    leader_id: Optional[str] = None
    service_schedule: List[ServiceSchedule] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True

class ChurchCreate(BaseModel):
    name: str
    district_id: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    leader_id: Optional[str] = None
    service_schedule: List[ServiceSchedule] = []

class ScheduleItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str
    time: str
    preacher_id: Optional[str] = None
    singers: List[str] = []
    status: ScheduleItemStatus = ScheduleItemStatus.PENDING
    refusal_reason: Optional[str] = None
    confirmed_at: Optional[str] = None
    cancelled_at: Optional[str] = None

class Schedule(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    month: int
    year: int
    church_id: str
    district_id: str
    generated_by: str
    generation_mode: GenerationMode
    status: ScheduleStatus = ScheduleStatus.DRAFT
    items: List[ScheduleItem] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ScheduleCreate(BaseModel):
    month: int
    year: int
    church_id: str
    generation_mode: GenerationMode

class ScheduleItemUpdate(BaseModel):
    preacher_id: Optional[str] = None
    singers: Optional[List[str]] = None
    status: Optional[ScheduleItemStatus] = None
    refusal_reason: Optional[str] = None

class Evaluation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    schedule_item_id: str
    church_id: str
    member_type: str  # 'preacher' or 'singer'
    evaluated_user_id: str
    rating: int  # 1-5
    feedback: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EvaluationCreate(BaseModel):
    schedule_item_id: str
    church_id: str
    member_type: str
    evaluated_user_id: str
    rating: int
    feedback: Optional[str] = None

class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str
    title: str
    message: str
    related_id: Optional[str] = None
    status: str = "unread"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SubstitutionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_schedule_item_id: str
    schedule_id: str
    requester_id: str
    target_user_id: str
    reason: str
    status: str = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    responded_at: Optional[str] = None

class SubstitutionRequestCreate(BaseModel):
    original_schedule_item_id: str
    schedule_id: str
    target_user_id: str
    reason: str

class Delegation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    district_id: str
    user_id: str
    delegated_by: str
    permissions: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True

class DelegationCreate(BaseModel):
    district_id: str
    user_id: str
    permissions: List[str]

# ===== AUTH UTILITIES =====

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id, "is_active": True}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Remove password from response
        user.pop('password_hash', None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ===== HELPER FUNCTIONS =====

async def create_notification(user_id: str, type: str, title: str, message: str, related_id: Optional[str] = None):
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        related_id=related_id
    )
    await db.notifications.insert_one(notification.model_dump())

async def send_mock_notification(phone: str, message: str):
    """Mock notification via SMS/WhatsApp"""
    logging.info(f"[MOCK SMS/WhatsApp to {phone}]: {message}")
    # TODO: Integrate with Twilio or WhatsApp Business API

async def is_user_available(user_id: str, date: str) -> bool:
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        return False
    
    for period in user.get('unavailable_periods', []):
        if period['start_date'] <= date <= period['end_date']:
            return False
    return True

async def is_slot_occupied(user_id: str, date: str) -> bool:
    """Check if user is already scheduled on this date"""
    schedules = await db.schedules.find({"status": {"$in": ["confirmed", "active"]}}, {"_id": 0}).to_list(1000)
    for schedule in schedules:
        for item in schedule.get('items', []):
            if item['date'] == date and item['status'] in ['confirmed', 'pending']:
                if item.get('preacher_id') == user_id or user_id in item.get('singers', []):
                    return True
    return False

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Simple distance calculation (in km)"""
    from math import radians, cos, sin, asin, sqrt
    
    if not all([lat1, lon1, lat2, lon2]):
        return 999999  # Large number if coords not available
    
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

# ===== AUTH ROUTES =====

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if username exists
    existing = await db.users.find_one({"username": user_data.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user_dict = user_data.model_dump()
    password = user_dict.pop('password')
    user_dict['password_hash'] = hash_password(password)
    
    user = User(**user_dict)
    await db.users.insert_one(user.model_dump())
    
    return user

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"username": credentials.username, "is_active": True}, {"_id": 0})
    if not user or not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user['id']})
    user.pop('password_hash')
    
    return {"access_token": token, "token_type": "bearer", "user": user}

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: Dict = Depends(get_current_user)):
    return current_user

@api_router.put("/auth/me", response_model=User)
async def update_me(updates: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    allowed_fields = ['name', 'email', 'phone', 'unavailable_periods']
    update_data = {k: v for k, v in updates.items() if k in allowed_fields}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one({"id": current_user['id']}, {"$set": update_data})
    
    updated_user = await db.users.find_one({"id": current_user['id']}, {"_id": 0, "password_hash": 0})
    return updated_user

# ===== DISTRICT ROUTES =====

@api_router.get("/districts", response_model=List[District])
async def get_districts(current_user: Dict = Depends(get_current_user)):
    if current_user['role'] == 'pastor_distrital':
        # Pastor can see all districts
        districts = await db.districts.find({"is_active": True}, {"_id": 0}).to_list(1000)
    else:
        # Others see only their district
        districts = await db.districts.find({"id": current_user.get('district_id'), "is_active": True}, {"_id": 0}).to_list(1000)
    return districts

@api_router.post("/districts", response_model=District)
async def create_district(district_data: DistrictCreate, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] != 'pastor_distrital':
        raise HTTPException(status_code=403, detail="Only Pastor Distrital can create districts")
    
    district = District(**district_data.model_dump())
    await db.districts.insert_one(district.model_dump())
    return district

@api_router.get("/districts/{district_id}", response_model=District)
async def get_district(district_id: str, current_user: Dict = Depends(get_current_user)):
    district = await db.districts.find_one({"id": district_id, "is_active": True}, {"_id": 0})
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    return district

@api_router.put("/districts/{district_id}", response_model=District)
async def update_district(district_id: str, updates: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    if current_user['role'] != 'pastor_distrital':
        raise HTTPException(status_code=403, detail="Only Pastor Distrital can update districts")
    
    updates['updated_at'] = datetime.now(timezone.utc).isoformat()
    await db.districts.update_one({"id": district_id}, {"$set": updates})
    
    district = await db.districts.find_one({"id": district_id}, {"_id": 0})
    return district

@api_router.delete("/districts/{district_id}")
async def delete_district(district_id: str, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] != 'pastor_distrital':
        raise HTTPException(status_code=403, detail="Only Pastor Distrital can delete districts")
    
    await db.districts.update_one({"id": district_id}, {"$set": {"is_active": False}})
    return {"message": "District deleted successfully"}

# ===== CHURCH ROUTES =====

@api_router.get("/churches", response_model=List[Church])
async def get_churches(
    district_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    query = {"is_active": True}
    
    if district_id:
        query['district_id'] = district_id
    elif current_user['role'] != 'pastor_distrital':
        query['district_id'] = current_user.get('district_id')
    
    churches = await db.churches.find(query, {"_id": 0}).to_list(1000)
    return churches

@api_router.post("/churches", response_model=Church)
async def create_church(church_data: ChurchCreate, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    church = Church(**church_data.model_dump())
    await db.churches.insert_one(church.model_dump())
    return church

@api_router.get("/churches/{church_id}", response_model=Church)
async def get_church(church_id: str):
    church = await db.churches.find_one({"id": church_id, "is_active": True}, {"_id": 0})
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    return church

@api_router.put("/churches/{church_id}", response_model=Church)
async def update_church(church_id: str, updates: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    if current_user['role'] not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    updates['updated_at'] = datetime.now(timezone.utc).isoformat()
    await db.churches.update_one({"id": church_id}, {"$set": updates})
    
    church = await db.churches.find_one({"id": church_id}, {"_id": 0})
    return church

@api_router.delete("/churches/{church_id}")
async def delete_church(church_id: str, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    await db.churches.update_one({"id": church_id}, {"$set": {"is_active": False}})
    return {"message": "Church deleted successfully"}

# ===== USER ROUTES =====

@api_router.get("/users", response_model=List[User])
async def get_users(
    district_id: Optional[str] = None,
    church_id: Optional[str] = None,
    is_preacher: Optional[bool] = None,
    is_singer: Optional[bool] = None,
    current_user: Dict = Depends(get_current_user)
):
    query = {"is_active": True}
    
    if current_user['role'] != 'pastor_distrital':
        query['district_id'] = current_user.get('district_id')
    
    if district_id:
        query['district_id'] = district_id
    if church_id:
        query['church_id'] = church_id
    if is_preacher is not None:
        query['is_preacher'] = is_preacher
    if is_singer is not None:
        query['is_singer'] = is_singer
    
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@api_router.get("/users/preachers", response_model=List[User])
async def get_preachers(district_id: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
    query = {"is_active": True, "is_preacher": True}
    
    if district_id:
        query['district_id'] = district_id
    elif current_user['role'] != 'pastor_distrital':
        query['district_id'] = current_user.get('district_id')
    
    preachers = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    return preachers

@api_router.get("/users/singers", response_model=List[User])
async def get_singers(district_id: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
    query = {"is_active": True, "is_singer": True}
    
    if district_id:
        query['district_id'] = district_id
    elif current_user['role'] != 'pastor_distrital':
        query['district_id'] = current_user.get('district_id')
    
    singers = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    return singers

@api_router.post("/users", response_model=User)
async def create_user(user_data: UserCreate, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    existing = await db.users.find_one({"username": user_data.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user_dict = user_data.model_dump()
    password = user_dict.pop('password')
    user_dict['password_hash'] = hash_password(password)
    
    user = User(**user_dict)
    await db.users.insert_one(user.model_dump())
    
    user_response = user.model_dump()
    user_response.pop('password_hash', None)
    return user_response

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str, current_user: Dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id, "is_active": True}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@api_router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, updates: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    # Check permissions
    if current_user['role'] not in ['pastor_distrital', 'lider_igreja'] and current_user['id'] != user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    updates['updated_at'] = datetime.now(timezone.utc).isoformat()
    updates.pop('password', None)  # Don't allow password updates here
    updates.pop('password_hash', None)
    
    await db.users.update_one({"id": user_id}, {"$set": updates})
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    return user

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    await db.users.update_one({"id": user_id}, {"$set": {"is_active": False}})
    return {"message": "User deleted successfully"}

# ===== SCHEDULE ROUTES =====

@api_router.get("/schedules", response_model=List[Schedule])
async def get_schedules(
    month: Optional[int] = None,
    year: Optional[int] = None,
    church_id: Optional[str] = None,
    district_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    query = {}
    
    if current_user['role'] != 'pastor_distrital':
        query['district_id'] = current_user.get('district_id')
    
    if month:
        query['month'] = month
    if year:
        query['year'] = year
    if church_id:
        query['church_id'] = church_id
    if district_id:
        query['district_id'] = district_id
    
    schedules = await db.schedules.find(query, {"_id": 0}).to_list(1000)
    return schedules

@api_router.post("/schedules/generate-auto")
async def generate_schedule_auto(
    month: int,
    year: int,
    district_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Generate automatic schedules for all churches in a district"""
    if current_user['role'] not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Get all churches in district
    churches = await db.churches.find({"district_id": district_id, "is_active": True}, {"_id": 0}).to_list(1000)
    
    # Get all preachers and singers in district
    preachers = await db.users.find({"district_id": district_id, "is_preacher": True, "is_active": True}, {"_id": 0}).to_list(1000)
    singers = await db.users.find({"district_id": district_id, "is_singer": True, "is_active": True}, {"_id": 0}).to_list(1000)
    
    # Sort preachers by score (higher scores get Saturdays)
    preachers_sorted = sorted(preachers, key=lambda x: x['preacher_score'], reverse=True)
    
    generated_schedules = []
    
    for church in churches:
        # Check if schedule already exists
        existing = await db.schedules.find_one({
            "church_id": church['id'],
            "month": month,
            "year": year
        })
        if existing:
            continue  # Skip if already exists
        
        schedule_items = []
        service_days = church.get('service_schedule', [])
        
        if not service_days:
            continue  # Skip churches without configured service days
        
        # Generate items for all days in the month
        from calendar import monthrange
        _, num_days = monthrange(year, month)
        
        preacher_index = 0
        for day in range(1, num_days + 1):
            date_obj = datetime(year, month, day)
            day_of_week = date_obj.strftime('%A').lower()
            
            # Check if this day has a service
            matching_service = None
            for service in service_days:
                if service['day_of_week'] == day_of_week:
                    matching_service = service
                    break
            
            if matching_service:
                date_str = date_obj.strftime('%Y-%m-%d')
                
                # Select preacher (rotating through available preachers)
                preacher = None
                attempts = 0
                while attempts < len(preachers_sorted):
                    candidate = preachers_sorted[preacher_index % len(preachers_sorted)]
                    preacher_index += 1
                    attempts += 1
                    
                    # Check availability
                    if await is_user_available(candidate['id'], date_str) and not await is_slot_occupied(candidate['id'], date_str):
                        preacher = candidate
                        break
                
                if preacher:
                    item = ScheduleItem(
                        date=date_str,
                        time=matching_service['time'],
                        preacher_id=preacher['id'],
                        singers=[],
                        status=ScheduleItemStatus.PENDING
                    )
                    schedule_items.append(item)
        
        # Create schedule
        schedule = Schedule(
            month=month,
            year=year,
            church_id=church['id'],
            district_id=district_id,
            generated_by=current_user['id'],
            generation_mode=GenerationMode.AUTOMATIC,
            status=ScheduleStatus.DRAFT,
            items=schedule_items
        )
        
        await db.schedules.insert_one(schedule.model_dump())
        generated_schedules.append(schedule)
    
    return {"message": f"Generated {len(generated_schedules)} schedules", "schedules": generated_schedules}

@api_router.post("/schedules/manual", response_model=Schedule)
async def create_manual_schedule(
    schedule_data: ScheduleCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Create a manual schedule"""
    if current_user['role'] not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Check if schedule already exists
    existing = await db.schedules.find_one({
        "church_id": schedule_data.church_id,
        "month": schedule_data.month,
        "year": schedule_data.year
    })
    if existing:
        raise HTTPException(status_code=400, detail="Schedule already exists for this month/year")
    
    # Get church info
    church = await db.churches.find_one({"id": schedule_data.church_id}, {"_id": 0})
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    
    # Create empty schedule
    from calendar import monthrange
    _, num_days = monthrange(schedule_data.year, schedule_data.month)
    
    schedule_items = []
    service_days = church.get('service_schedule', [])
    
    for day in range(1, num_days + 1):
        date_obj = datetime(schedule_data.year, schedule_data.month, day)
        day_of_week = date_obj.strftime('%A').lower()
        
        # Check if this day has a service
        matching_service = None
        for service in service_days:
            if service['day_of_week'] == day_of_week:
                matching_service = service
                break
        
        if matching_service:
            date_str = date_obj.strftime('%Y-%m-%d')
            item = ScheduleItem(
                date=date_str,
                time=matching_service['time'],
                preacher_id=None,
                singers=[],
                status=ScheduleItemStatus.PENDING
            )
            schedule_items.append(item)
    
    schedule = Schedule(
        month=schedule_data.month,
        year=schedule_data.year,
        church_id=schedule_data.church_id,
        district_id=church['district_id'],
        generated_by=current_user['id'],
        generation_mode=GenerationMode.MANUAL,
        status=ScheduleStatus.DRAFT,
        items=schedule_items
    )
    
    await db.schedules.insert_one(schedule.model_dump())
    return schedule

@api_router.get("/schedules/{schedule_id}", response_model=Schedule)
async def get_schedule(schedule_id: str):
    schedule = await db.schedules.find_one({"id": schedule_id}, {"_id": 0})
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule

@api_router.put("/schedules/{schedule_id}/items/{item_id}")
async def update_schedule_item(
    schedule_id: str,
    item_id: str,
    updates: ScheduleItemUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Update a specific schedule item"""
    schedule = await db.schedules.find_one({"id": schedule_id}, {"_id": 0})
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Find and update the item
    items = schedule['items']
    item_found = False
    
    for item in items:
        if item['id'] == item_id:
            if updates.preacher_id is not None:
                # Check if preacher is already scheduled elsewhere on this date
                if await is_slot_occupied(updates.preacher_id, item['date']):
                    raise HTTPException(status_code=400, detail="Preacher already scheduled on this date")
                item['preacher_id'] = updates.preacher_id
            
            if updates.singers is not None:
                # Check singers availability
                for singer_id in updates.singers:
                    if await is_slot_occupied(singer_id, item['date']):
                        raise HTTPException(status_code=400, detail=f"Singer {singer_id} already scheduled on this date")
                item['singers'] = updates.singers
            
            if updates.status is not None:
                item['status'] = updates.status
            
            if updates.refusal_reason is not None:
                item['refusal_reason'] = updates.refusal_reason
            
            item_found = True
            break
    
    if not item_found:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    # Update schedule
    schedule['updated_at'] = datetime.now(timezone.utc).isoformat()
    await db.schedules.update_one({"id": schedule_id}, {"$set": {"items": items, "updated_at": schedule['updated_at']}})
    
    return {"message": "Schedule item updated", "schedule": schedule}

@api_router.post("/schedules/{schedule_id}/confirm")
async def confirm_schedule(
    schedule_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Confirm schedule and send notifications"""
    schedule = await db.schedules.find_one({"id": schedule_id}, {"_id": 0})
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Check if all items have preachers assigned
    for item in schedule['items']:
        if not item.get('preacher_id'):
            raise HTTPException(status_code=400, detail=f"Item on {item['date']} has no preacher assigned")
    
    # Update status
    await db.schedules.update_one(
        {"id": schedule_id},
        {"$set": {"status": ScheduleStatus.CONFIRMED, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Send notifications to all members
    church = await db.churches.find_one({"id": schedule['church_id']}, {"_id": 0})
    
    for item in schedule['items']:
        # Notify preacher
        if item.get('preacher_id'):
            preacher = await db.users.find_one({"id": item['preacher_id']}, {"_id": 0})
            if preacher:
                message = f"Você foi escalado para pregar em {church['name']} no dia {item['date']} às {item['time']}"
                await create_notification(
                    preacher['id'],
                    'schedule_assignment',
                    'Nova Escala de Pregação',
                    message,
                    item['id']
                )
                if preacher.get('phone'):
                    await send_mock_notification(preacher['phone'], message)
        
        # Notify singers
        for singer_id in item.get('singers', []):
            singer = await db.users.find_one({"id": singer_id}, {"_id": 0})
            if singer:
                message = f"Você foi escalado para Louvor Especial em {church['name']} no dia {item['date']} às {item['time']}"
                await create_notification(
                    singer['id'],
                    'schedule_assignment',
                    'Nova Escala de Louvor',
                    message,
                    item['id']
                )
                if singer.get('phone'):
                    await send_mock_notification(singer['phone'], message)
    
    return {"message": "Schedule confirmed and notifications sent"}

@api_router.post("/schedule-items/{item_id}/confirm")
async def confirm_participation(item_id: str, current_user: Dict = Depends(get_current_user)):
    """Member confirms participation"""
    # Find schedule containing this item
    schedule = await db.schedules.find_one({"items.id": item_id}, {"_id": 0})
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    # Update item status
    for item in schedule['items']:
        if item['id'] == item_id:
            if item.get('preacher_id') != current_user['id'] and current_user['id'] not in item.get('singers', []):
                raise HTTPException(status_code=403, detail="You are not assigned to this schedule")
            
            item['status'] = ScheduleItemStatus.CONFIRMED
            item['confirmed_at'] = datetime.now(timezone.utc).isoformat()
            break
    
    await db.schedules.update_one({"id": schedule['id']}, {"$set": {"items": schedule['items']}})
    
    return {"message": "Participation confirmed"}

@api_router.post("/schedule-items/{item_id}/refuse")
async def refuse_participation(item_id: str, reason: str, current_user: Dict = Depends(get_current_user)):
    """Member refuses participation"""
    schedule = await db.schedules.find_one({"items.id": item_id}, {"_id": 0})
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    church = await db.churches.find_one({"id": schedule['church_id']}, {"_id": 0})
    district = await db.districts.find_one({"id": schedule['district_id']}, {"_id": 0})
    
    # Update item
    for item in schedule['items']:
        if item['id'] == item_id:
            if item.get('preacher_id') == current_user['id']:
                item['preacher_id'] = None
                member_type = 'pregador'
            elif current_user['id'] in item.get('singers', []):
                item['singers'].remove(current_user['id'])
                member_type = 'cantor'
            else:
                raise HTTPException(status_code=403, detail="You are not assigned to this schedule")
            
            item['status'] = ScheduleItemStatus.REFUSED
            item['refusal_reason'] = reason
            
            # Notify pastor and church leader
            pastor = await db.users.find_one({"id": district['pastor_id']}, {"_id": 0})
            if pastor:
                notification_msg = f"{current_user['name']} ({member_type}) recusou a escala em {church['name']} no dia {item['date']} às {item['time']}. Motivo: {reason}"
                await create_notification(
                    pastor['id'],
                    'schedule_refusal',
                    'Recusa de Escala',
                    notification_msg,
                    item_id
                )
                if pastor.get('phone'):
                    await send_mock_notification(pastor['phone'], notification_msg)
            
            if church.get('leader_id'):
                leader = await db.users.find_one({"id": church['leader_id']}, {"_id": 0})
                if leader:
                    await create_notification(
                        leader['id'],
                        'schedule_refusal',
                        'Recusa de Escala',
                        notification_msg,
                        item_id
                    )
            
            break
    
    await db.schedules.update_one({"id": schedule['id']}, {"$set": {"items": schedule['items']}})
    
    return {"message": "Participation refused"}

@api_router.post("/schedule-items/{item_id}/cancel")
async def cancel_participation(item_id: str, reason: str, current_user: Dict = Depends(get_current_user)):
    """Cancel confirmed participation (up to 2 days before)"""
    schedule = await db.schedules.find_one({"items.id": item_id}, {"_id": 0})
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    for item in schedule['items']:
        if item['id'] == item_id:
            # Check if within 2 days
            item_date = datetime.fromisoformat(item['date'])
            days_until = (item_date - datetime.now(timezone.utc)).days
            
            if days_until < 2:
                raise HTTPException(status_code=400, detail="Cannot cancel within 2 days of the service")
            
            if item['status'] != ScheduleItemStatus.CONFIRMED:
                raise HTTPException(status_code=400, detail="Can only cancel confirmed participation")
            
            item['status'] = ScheduleItemStatus.CANCELLED
            item['cancelled_at'] = datetime.now(timezone.utc).isoformat()
            item['refusal_reason'] = reason
            
            # Clear assignment
            if item.get('preacher_id') == current_user['id']:
                item['preacher_id'] = None
            elif current_user['id'] in item.get('singers', []):
                item['singers'].remove(current_user['id'])
            
            break
    
    await db.schedules.update_one({"id": schedule['id']}, {"$set": {"items": schedule['items']}})
    
    return {"message": "Participation cancelled"}

@api_router.post("/schedule-items/{item_id}/volunteer")
async def volunteer_for_slot(item_id: str, current_user: Dict = Depends(get_current_user)):
    """Volunteer for an empty slot"""
    schedule = await db.schedules.find_one({"items.id": item_id}, {"_id": 0})
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    for item in schedule['items']:
        if item['id'] == item_id:
            # Check if slot is empty
            if item.get('preacher_id'):
                raise HTTPException(status_code=400, detail="Slot is already filled")
            
            # Check availability
            if not await is_user_available(current_user['id'], item['date']):
                raise HTTPException(status_code=400, detail="You are not available on this date")
            
            if await is_slot_occupied(current_user['id'], item['date']):
                raise HTTPException(status_code=400, detail="You are already scheduled on this date")
            
            if current_user.get('is_preacher'):
                item['preacher_id'] = current_user['id']
                item['status'] = ScheduleItemStatus.CONFIRMED
            else:
                raise HTTPException(status_code=400, detail="You must be a preacher to volunteer")
            
            break
    
    await db.schedules.update_one({"id": schedule['id']}, {"$set": {"items": schedule['items']}})
    
    return {"message": "Successfully volunteered for slot"}

@api_router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] not in ['pastor_distrital', 'lider_igreja']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    await db.schedules.delete_one({"id": schedule_id})
    return {"message": "Schedule deleted successfully"}

# ===== EVALUATION ROUTES =====

@api_router.post("/evaluations", response_model=Evaluation)
async def create_evaluation(eval_data: EvaluationCreate):
    """Create evaluation (no login required for members)"""
    # Verify that the service has occurred
    schedule = await db.schedules.find_one({"items.id": eval_data.schedule_item_id}, {"_id": 0})
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    # Find the item
    item = None
    for i in schedule['items']:
        if i['id'] == eval_data.schedule_item_id:
            item = i
            break
    
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    # Check if service has occurred
    item_datetime = datetime.fromisoformat(item['date'])
    if item_datetime > datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Cannot evaluate before the service")
    
    # Create evaluation
    evaluation = Evaluation(**eval_data.model_dump())
    await db.evaluations.insert_one(evaluation.model_dump())
    
    # Update user score
    user = await db.users.find_one({"id": eval_data.evaluated_user_id}, {"_id": 0})
    if user:
        score_field = 'preacher_score' if eval_data.member_type == 'preacher' else 'singer_score'
        current_score = user.get(score_field, 50.0)
        
        # Calculate new score (simple average adjustment)
        rating_impact = (eval_data.rating - 3) * 2  # Scale: -4 to +4
        new_score = max(0, min(100, current_score + rating_impact))
        
        await db.users.update_one(
            {"id": eval_data.evaluated_user_id},
            {"$set": {score_field: new_score}}
        )
    
    return evaluation

@api_router.get("/evaluations/by-user/{user_id}", response_model=List[Evaluation])
async def get_evaluations_by_user(user_id: str, current_user: Dict = Depends(get_current_user)):
    evaluations = await db.evaluations.find({"evaluated_user_id": user_id}, {"_id": 0}).to_list(1000)
    return evaluations

# ===== NOTIFICATION ROUTES =====

@api_router.get("/notifications", response_model=List[Notification])
async def get_notifications(current_user: Dict = Depends(get_current_user)):
    notifications = await db.notifications.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return notifications

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: Dict = Depends(get_current_user)):
    await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user['id']},
        {"$set": {"status": "read"}}
    )
    return {"message": "Notification marked as read"}

@api_router.put("/notifications/mark-all-read")
async def mark_all_notifications_read(current_user: Dict = Depends(get_current_user)):
    await db.notifications.update_many(
        {"user_id": current_user['id'], "status": "unread"},
        {"$set": {"status": "read"}}
    )
    return {"message": "All notifications marked as read"}

# ===== SUBSTITUTION ROUTES =====

@api_router.post("/substitutions", response_model=SubstitutionRequest)
async def create_substitution_request(
    sub_data: SubstitutionRequestCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Request schedule substitution"""
    substitution = SubstitutionRequest(
        **sub_data.model_dump(),
        requester_id=current_user['id']
    )
    
    await db.substitution_requests.insert_one(substitution.model_dump())
    
    # Notify target user
    await create_notification(
        sub_data.target_user_id,
        'substitution_request',
        'Solicitação de Troca de Escala',
        f"{current_user['name']} solicitou trocar a escala com você. Motivo: {sub_data.reason}",
        substitution.id
    )
    
    return substitution

@api_router.post("/substitutions/{sub_id}/accept")
async def accept_substitution(sub_id: str, current_user: Dict = Depends(get_current_user)):
    substitution = await db.substitution_requests.find_one({"id": sub_id}, {"_id": 0})
    if not substitution:
        raise HTTPException(status_code=404, detail="Substitution request not found")
    
    if substitution['target_user_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Update substitution
    await db.substitution_requests.update_one(
        {"id": sub_id},
        {"$set": {"status": "accepted", "responded_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Swap schedule items
    schedule = await db.schedules.find_one({"id": substitution['schedule_id']}, {"_id": 0})
    if schedule:
        for item in schedule['items']:
            if item['id'] == substitution['original_schedule_item_id']:
                if item.get('preacher_id') == substitution['requester_id']:
                    item['preacher_id'] = current_user['id']
                elif substitution['requester_id'] in item.get('singers', []):
                    item['singers'].remove(substitution['requester_id'])
                    item['singers'].append(current_user['id'])
                break
        
        await db.schedules.update_one({"id": schedule['id']}, {"$set": {"items": schedule['items']}})
    
    # Notify requester
    await create_notification(
        substitution['requester_id'],
        'substitution_accepted',
        'Troca Aceita',
        f"Sua solicitação de troca foi aceita por {current_user['name']}",
        sub_id
    )
    
    return {"message": "Substitution accepted"}

@api_router.post("/substitutions/{sub_id}/reject")
async def reject_substitution(sub_id: str, current_user: Dict = Depends(get_current_user)):
    substitution = await db.substitution_requests.find_one({"id": sub_id}, {"_id": 0})
    if not substitution:
        raise HTTPException(status_code=404, detail="Substitution request not found")
    
    if substitution['target_user_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    await db.substitution_requests.update_one(
        {"id": sub_id},
        {"$set": {"status": "rejected", "responded_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await create_notification(
        substitution['requester_id'],
        'substitution_rejected',
        'Troca Recusada',
        f"Sua solicitação de troca foi recusada por {current_user['name']}",
        sub_id
    )
    
    return {"message": "Substitution rejected"}

@api_router.get("/substitutions/pending", response_model=List[SubstitutionRequest])
async def get_pending_substitutions(current_user: Dict = Depends(get_current_user)):
    substitutions = await db.substitution_requests.find(
        {"target_user_id": current_user['id'], "status": "pending"},
        {"_id": 0}
    ).to_list(100)
    return substitutions

# ===== DELEGATION ROUTES =====

@api_router.post("/delegations", response_model=Delegation)
async def create_delegation(
    delegation_data: DelegationCreate,
    current_user: Dict = Depends(get_current_user)
):
    if current_user['role'] != 'pastor_distrital':
        raise HTTPException(status_code=403, detail="Only Pastor Distrital can delegate")
    
    delegation = Delegation(
        **delegation_data.model_dump(),
        delegated_by=current_user['id']
    )
    
    await db.delegations.insert_one(delegation.model_dump())
    return delegation

@api_router.get("/delegations", response_model=List[Delegation])
async def get_delegations(district_id: Optional[str] = None, current_user: Dict = Depends(get_current_user)):
    query = {"is_active": True}
    if district_id:
        query['district_id'] = district_id
    
    delegations = await db.delegations.find(query, {"_id": 0}).to_list(100)
    return delegations

@api_router.delete("/delegations/{delegation_id}")
async def delete_delegation(delegation_id: str, current_user: Dict = Depends(get_current_user)):
    if current_user['role'] != 'pastor_distrital':
        raise HTTPException(status_code=403, detail="Only Pastor Distrital can delete delegations")
    
    await db.delegations.update_one({"id": delegation_id}, {"$set": {"is_active": False}})
    return {"message": "Delegation deleted successfully"}

# ===== ANALYTICS ROUTES =====

@api_router.get("/analytics/dashboard")
async def get_analytics_dashboard(district_id: str, current_user: Dict = Depends(get_current_user)):
    """Get analytics dashboard for pastor"""
    if current_user['role'] != 'pastor_distrital':
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Get statistics
    total_churches = await db.churches.count_documents({"district_id": district_id, "is_active": True})
    total_preachers = await db.users.count_documents({"district_id": district_id, "is_preacher": True, "is_active": True})
    total_singers = await db.users.count_documents({"district_id": district_id, "is_singer": True, "is_active": True})
    
    # Get top preachers
    preachers = await db.users.find(
        {"district_id": district_id, "is_preacher": True, "is_active": True},
        {"_id": 0}
    ).sort("preacher_score", -1).limit(10).to_list(10)
    
    # Get recent evaluations
    evaluations = await db.evaluations.find({}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
    
    return {
        "total_churches": total_churches,
        "total_preachers": total_preachers,
        "total_singers": total_singers,
        "top_preachers": preachers,
        "recent_evaluations": evaluations
    }

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
