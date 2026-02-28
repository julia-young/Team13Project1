import os
import time
import uuid
from pymongo import MongoClient

_client = None
_db = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_db():
    global _client, _db
    if _db is not None:
        return _db

    uri = os.environ["MONGO_URI"]
    _client = MongoClient(uri, serverSelectionTimeoutMS=20000)
    _db = _client.get_default_database()
    return _db


def _users():
    return _get_db()["users"]


def _photos():
    return _get_db()["photos"]


# ---------------------------------------------------------------------------
# User functions 
# ---------------------------------------------------------------------------

def create_user(username, email, password_hash):
    user_id = str(uuid.uuid4())

    doc = {
        "id": user_id,
        "username": username,
        "password_hash": password_hash,
    }
    if email:
        doc["email"] = email

    _users().insert_one(doc)
    return user_id


def get_user_by_username(username):
    user = _users().find_one({"username": username}, {"_id": 0})
    return user


# ---------------------------------------------------------------------------
# Photo functions 
# ---------------------------------------------------------------------------

def add_photo(user_id, s3_bucket, s3_key, original_name,
              title=None, description=None, tags=None,
              content_type=None, size_bytes=None):

    photo_id = int(time.time() * 1000)

    doc = {
        "id": photo_id,
        "user_id": str(user_id),
        "s3_bucket": s3_bucket,
        "s3_key": s3_key,
        "original_name": original_name,
        "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    if title:
        doc["title"] = title
    if description:
        doc["description"] = description
    if tags:
        doc["tags"] = tags
    if content_type:
        doc["content_type"] = content_type
    if size_bytes:
        doc["size_bytes"] = size_bytes

    _photos().insert_one(doc)
    return photo_id


def list_photos(user_id, limit=50, offset=0):
    cursor = (
        _photos()
        .find({"user_id": str(user_id)}, {"_id": 0})
        .sort("id", -1)
        .skip(offset)
        .limit(limit)
    )
    return list(cursor)


def search_photos(user_id, q=None, limit=50, offset=0):
    if not q:
        return list_photos(user_id, limit, offset)

    q_regex = {"$regex": q, "$options": "i"}

    query = {
        "user_id": str(user_id),
        "$or": [
            {"title": q_regex},
            {"description": q_regex},
            {"tags": q_regex},
            {"original_name": q_regex},
        ],
    }

    cursor = (
        _photos()
        .find(query, {"_id": 0})
        .sort("id", -1)
        .skip(offset)
        .limit(limit)
    )

    return list(cursor)


def get_photo(photo_id, user_id):
    photo = _photos().find_one(
        {"id": int(photo_id), "user_id": str(user_id)},
        {"_id": 0}
    )
    return photo
