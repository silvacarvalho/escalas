#!/usr/bin/env python3
"""
Script to seed the database with initial test data
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / 'backend'))

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

# Load environment
backend_dir = Path(__file__).parent.parent / 'backend'
load_dotenv(backend_dir / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_database():
    print("🌱 Seeding database...")
    
    # Clear existing data
    print("Clearing existing data...")
    await db.users.delete_many({})
    await db.districts.delete_many({})
    await db.churches.delete_many({})
    await db.schedules.delete_many({})
    await db.evaluations.delete_many({})
    await db.notifications.delete_many({})
    await db.substitution_requests.delete_many({})
    await db.delegations.delete_many({})
    
    # Create Districts
    print("Creating districts...")
    district1_id = str(uuid.uuid4())
    district2_id = str(uuid.uuid4())
    
    # Create Pastor Distrital
    pastor1_id = str(uuid.uuid4())
    pastor2_id = str(uuid.uuid4())
    
    pastor1 = {
        "id": pastor1_id,
        "username": "pastor1",
        "password_hash": pwd_context.hash("pastor123"),
        "name": "Pastor João Silva",
        "email": "pastor.joao@example.com",
        "phone": "+5511999999999",
        "role": "pastor_distrital",
        "district_id": district1_id,
        "church_id": None,
        "is_preacher": True,
        "is_singer": False,
        "preacher_score": 85.0,
        "singer_score": 50.0,
        "unavailable_periods": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    
    pastor2 = {
        "id": pastor2_id,
        "username": "pastor2",
        "password_hash": pwd_context.hash("pastor123"),
        "name": "Pastor Carlos Mendes",
        "email": "pastor.carlos@example.com",
        "phone": "+5511988888888",
        "role": "pastor_distrital",
        "district_id": district2_id,
        "church_id": None,
        "is_preacher": True,
        "is_singer": False,
        "preacher_score": 90.0,
        "singer_score": 50.0,
        "unavailable_periods": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    
    await db.users.insert_many([pastor1, pastor2])
    
    district1 = {
        "id": district1_id,
        "name": "Distrito Norte",
        "pastor_id": pastor1_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    
    district2 = {
        "id": district2_id,
        "name": "Distrito Sul",
        "pastor_id": pastor2_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    
    await db.districts.insert_many([district1, district2])
    
    # Create Churches
    print("Creating churches...")
    church1_id = str(uuid.uuid4())
    church2_id = str(uuid.uuid4())
    church3_id = str(uuid.uuid4())
    
    leader1_id = str(uuid.uuid4())
    leader2_id = str(uuid.uuid4())
    
    churches = [
        {
            "id": church1_id,
            "name": "Igreja Central",
            "district_id": district1_id,
            "address": "Rua Principal, 100",
            "latitude": -23.550520,
            "longitude": -46.633308,
            "leader_id": leader1_id,
            "service_schedule": [
                {"day_of_week": "wednesday", "time": "19:00"},
                {"day_of_week": "saturday", "time": "09:00"}
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        },
        {
            "id": church2_id,
            "name": "Igreja do Bairro Alto",
            "district_id": district1_id,
            "address": "Avenida das Flores, 250",
            "latitude": -23.560520,
            "longitude": -46.643308,
            "leader_id": leader2_id,
            "service_schedule": [
                {"day_of_week": "saturday", "time": "10:00"},
                {"day_of_week": "sunday", "time": "19:00"}
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        },
        {
            "id": church3_id,
            "name": "Igreja Vila Nova",
            "district_id": district2_id,
            "address": "Rua das Acácias, 500",
            "latitude": -23.570520,
            "longitude": -46.653308,
            "leader_id": None,
            "service_schedule": [
                {"day_of_week": "wednesday", "time": "19:30"},
                {"day_of_week": "saturday", "time": "09:30"}
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        }
    ]
    
    await db.churches.insert_many(churches)
    
    # Create Leaders
    print("Creating leaders and members...")
    leader1 = {
        "id": leader1_id,
        "username": "lider1",
        "password_hash": pwd_context.hash("lider123"),
        "name": "Líder Maria Santos",
        "email": "maria.santos@example.com",
        "phone": "+5511977777777",
        "role": "lider_igreja",
        "district_id": district1_id,
        "church_id": church1_id,
        "is_preacher": True,
        "is_singer": True,
        "preacher_score": 78.0,
        "singer_score": 82.0,
        "unavailable_periods": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    
    leader2 = {
        "id": leader2_id,
        "username": "lider2",
        "password_hash": pwd_context.hash("lider123"),
        "name": "Líder Pedro Oliveira",
        "email": "pedro.oliveira@example.com",
        "phone": "+5511966666666",
        "role": "lider_igreja",
        "district_id": district1_id,
        "church_id": church2_id,
        "is_preacher": True,
        "is_singer": False,
        "preacher_score": 88.0,
        "singer_score": 50.0,
        "unavailable_periods": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    
    # Create Preachers and Singers
    preachers = []
    preacher_names = [
        ("José", "Silva", 75.0),
        ("Ana", "Costa", 92.0),
        ("Paulo", "Ferreira", 68.0),
        ("Mariana", "Alves", 85.0),
        ("Ricardo", "Santos", 79.0),
        ("Juliana", "Rodrigues", 90.0),
        ("Fernando", "Lima", 72.0),
        ("Carla", "Martins", 81.0)
    ]
    
    for first_name, last_name, score in preacher_names:
        preacher_id = str(uuid.uuid4())
        username = f"{first_name.lower()}.{last_name.lower()}"
        preachers.append({
            "id": preacher_id,
            "username": username,
            "password_hash": pwd_context.hash("pregador123"),
            "name": f"{first_name} {last_name}",
            "email": f"{username}@example.com",
            "phone": f"+551195{str(uuid.uuid4())[:7]}",
            "role": "pregador",
            "district_id": district1_id,
            "church_id": church1_id if len(preachers) % 2 == 0 else church2_id,
            "is_preacher": True,
            "is_singer": len(preachers) % 3 == 0,  # Some are also singers
            "preacher_score": score,
            "singer_score": 50.0 + (score - 50) * 0.8 if len(preachers) % 3 == 0 else 50.0,
            "unavailable_periods": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        })
    
    await db.users.insert_many([leader1, leader2] + preachers)
    
    print("✅ Database seeded successfully!")
    print("\n📋 Test Credentials:")
    print("=" * 50)
    print("Pastor Distrital:")
    print("  Username: pastor1")
    print("  Password: pastor123")
    print("\nLíder de Igreja:")
    print("  Username: lider1")
    print("  Password: lider123")
    print("\nPregador:")
    print("  Username: jose.silva")
    print("  Password: pregador123")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(seed_database())
