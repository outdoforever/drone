"""
MongoDB Database Interface for Autonomous Disaster-Response Drone Backend.
Replaces SQLite with MongoDB Atlas / Local MongoDB via PyMongo.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import pymongo
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

# Load environment variables from .env file
root_env = os.path.join(os.path.dirname(__file__), "..", ".env")
backend_env = os.path.join(os.path.dirname(__file__), ".env")

if os.path.exists(root_env):
    load_dotenv(root_env)
if os.path.exists(backend_env):
    load_dotenv(backend_env)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "disaster_drone")

# In-memory store fallback if MongoDB server is unreachable
_in_memory_detections: Dict[str, Dict[str, Any]] = {}
_is_mongo_connected = False
_last_check_time = 0.0

_client = None
_db = None

def get_db():
    global _client, _db, _is_mongo_connected, _last_check_time
    if _db is not None:
        return _db

    now = time.time()
    # If connection previously failed, retry at most once every 10 seconds
    if not _is_mongo_connected and (now - _last_check_time < 10.0):
        return None

    _last_check_time = now
    try:
        uri = os.getenv("MONGODB_URI", MONGODB_URI)
        db_name = os.getenv("MONGODB_DB_NAME", MONGODB_DB_NAME)
        
        # Connect to MongoDB with timeout
        _client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=1500)
        # Force connection check
        _client.admin.command('ping')
        _db = _client[db_name]
        _is_mongo_connected = True
        print(f"[MongoDB] Connected successfully to DB '{db_name}' at {uri.split('@')[-1] if '@' in uri else uri}")
        return _db
    except Exception as e:
        _is_mongo_connected = False
        return None

def init_db():
    db = get_db()
    if db is not None:
        try:
            # Create unique index on detection ID
            db.detections.create_index([("id", pymongo.ASCENDING)], unique=True)
            db.detections.create_index([("timestamp", pymongo.DESCENDING)])
            db.mission_logs.create_index([("timestamp", pymongo.DESCENDING)])
            # Disaster zone indexes
            db.disaster_zones.create_index([("zone_id", pymongo.ASCENDING)], unique=True)
            db.disaster_zones.create_index([("timestamp", pymongo.DESCENDING)])
            print("[MongoDB] Collections and indexes initialized successfully.")
        except Exception as e:
            print(f"[MongoDB] Index creation error: {e}")

def save_detection(det: Dict[str, Any]):
    # Ensure document copy without mutating caller
    doc = dict(det)
    det_id = doc.get("id")
    if not det_id:
        return

    # Normalize fields
    doc["thermal_confirmed"] = bool(doc.get("thermal_confirmed", False))
    doc["nearby_fire"] = bool(doc.get("nearby_fire", False))
    doc["nearby_smoke"] = bool(doc.get("nearby_smoke", False))
    doc["nearby_flood"] = bool(doc.get("nearby_flood", False))
    doc["risk_score"] = int(doc.get("risk_score", 0))

    db = get_db()
    if db is not None:
        try:
            db.detections.update_one(
                {"id": det_id},
                {"$set": doc},
                upsert=True
            )
            return
        except PyMongoError as pe:
            print(f"[MongoDB] Save error: {pe}")

    # Fallback in-memory
    _in_memory_detections[det_id] = doc

def get_all_detections() -> List[Dict[str, Any]]:
    db = get_db()
    if db is not None:
        try:
            # Query MongoDB and exclude internal _id for clean JSON serialization
            cursor = db.detections.find({}, {"_id": 0}).sort("timestamp", pymongo.DESCENDING)
            results = list(cursor)
            return results
        except PyMongoError as pe:
            print(f"[MongoDB] Fetch error: {pe}")

    # Fallback in-memory
    items = list(_in_memory_detections.values())
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return items

def clear_detections():
    db = get_db()
    if db is not None:
        try:
            db.detections.delete_many({})
            print("[MongoDB] Cleared all detections from MongoDB collection.")
        except PyMongoError as pe:
            print(f"[MongoDB] Clear error: {pe}")

    _in_memory_detections.clear()


# ──────────────── Disaster Zones Collection ────────────────

_in_memory_zones: Dict[str, Dict[str, Any]] = {}

def save_zone(zone: Dict[str, Any]):
    """Save or update a disaster zone polygon."""
    doc = dict(zone)
    zone_id = doc.get("zone_id")
    if not zone_id:
        return

    db = get_db()
    if db is not None:
        try:
            db.disaster_zones.update_one(
                {"zone_id": zone_id},
                {"$set": doc},
                upsert=True
            )
            return
        except PyMongoError as pe:
            print(f"[MongoDB] Zone save error: {pe}")

    _in_memory_zones[zone_id] = doc

def get_all_zones() -> List[Dict[str, Any]]:
    """Retrieve all mapped disaster zones."""
    db = get_db()
    if db is not None:
        try:
            cursor = db.disaster_zones.find({}, {"_id": 0}).sort("timestamp", pymongo.DESCENDING)
            return list(cursor)
        except PyMongoError as pe:
            print(f"[MongoDB] Zone fetch error: {pe}")

    items = list(_in_memory_zones.values())
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return items

def clear_zones():
    """Clear all disaster zones."""
    db = get_db()
    if db is not None:
        try:
            db.disaster_zones.delete_many({})
            print("[MongoDB] Cleared all disaster zones.")
        except PyMongoError as pe:
            print(f"[MongoDB] Zone clear error: {pe}")

    _in_memory_zones.clear()

