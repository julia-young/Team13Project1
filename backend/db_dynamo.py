"""
DynamoDB backend — Part A.

Implements the same 6 functions as the MySQL db.py so routes.py
never needs to change. db.py imports these when DB_PROVIDER=dynamo.

Table design
------------
Users table  (env: DDB_USERS_TABLE, default "users")
  PK: username (S)
  Attributes: id (S, UUID), email (S), password_hash (S)

Photos table (env: DDB_PHOTOS_TABLE, default "photos")
  PK: user_id (S)
  SK: id (N, millisecond timestamp — keeps compatible with /download/<int:photo_id>)
  Attributes: s3_bucket, s3_key, original_name, title, description,
              tags, content_type, size_bytes, uploaded_at
"""
import os
import time
import uuid
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key


# ---------------------------------------------------------------------------
# Helpers — get boto3 Table resources
# ---------------------------------------------------------------------------

def _ddb():
    return boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-2"))

def _users():
    return _ddb().Table(os.environ.get("DDB_USERS_TABLE", "users"))

def _photos():
    return _ddb().Table(os.environ.get("DDB_PHOTOS_TABLE", "photos"))


def _item_to_photo(item):
    """Convert a raw DynamoDB item dict into the shape routes.py expects."""
    return {
        "id":            int(item["id"]),
        "user_id":       item["user_id"],
        "s3_bucket":     item["s3_bucket"],
        "s3_key":        item["s3_key"],
        "original_name": item["original_name"],
        "title":         item.get("title"),
        "description":   item.get("description"),
        "tags":          item.get("tags"),
        "content_type":  item.get("content_type"),
        "size_bytes":    int(item["size_bytes"]) if item.get("size_bytes") else None,
        "uploaded_at":   item.get("uploaded_at"),
    }


# ---------------------------------------------------------------------------
# User functions
# ---------------------------------------------------------------------------

def create_user(username, email, password_hash):
    """
    Insert a new user row.
    Returns the new user's UUID (mirrors MySQL's lastrowid usage).
    """
    user_id = str(uuid.uuid4())
    item = {
        "username":      username,
        "id":            user_id,
        "password_hash": password_hash,
    }
    if email:
        item["email"] = email
    _users().put_item(Item=item)
    return user_id


def get_user_by_username(username):
    """
    Look up a user by username.
    Returns a dict with id, username, email, password_hash — or None if not found.
    """
    resp = _users().get_item(Key={"username": username})
    item = resp.get("Item")
    if not item:
        return None
    return {
        "id":            item["id"],
        "username":      item["username"],
        "email":         item.get("email"),
        "password_hash": item["password_hash"],
    }


# ---------------------------------------------------------------------------
# Photo functions
# ---------------------------------------------------------------------------

def add_photo(user_id, s3_bucket, s3_key, original_name,
              title=None, description=None, tags=None,
              content_type=None, size_bytes=None):
    """
    Insert a new photo record.
    Uses a millisecond timestamp as the integer ID so the /download/<int:photo_id>
    route in routes.py works without any changes.
    """
    photo_id = int(time.time() * 1000)
    item = {
        "user_id":       str(user_id),
        "id":            Decimal(photo_id),
        "s3_bucket":     s3_bucket,
        "s3_key":        s3_key,
        "original_name": original_name,
        "uploaded_at":   time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if title:        item["title"]        = title
    if description:  item["description"]  = description
    if tags:         item["tags"]         = tags
    if content_type: item["content_type"] = content_type
    if size_bytes:   item["size_bytes"]   = Decimal(size_bytes)

    _photos().put_item(Item=item)
    return photo_id


def list_photos(user_id, limit=50, offset=0):
    """
    Return all photos for a user, newest first.
    Queries on the partition key (user_id) — efficient even at scale.
    """
    resp = _photos().query(
        KeyConditionExpression=Key("user_id").eq(str(user_id)),
        ScanIndexForward=False,   # newest first (descending sort key)
    )
    items = [_item_to_photo(i) for i in resp.get("Items", [])]
    return items[offset: offset + limit]


def search_photos(user_id, q=None, limit=50, offset=0):
    """
    Search photos by title, description, tags, or original filename.
    Fetches all photos for the user then filters in Python — acceptable
    for the small dataset (20 photos) required by the assignment.
    """
    if not q:
        return list_photos(user_id, limit, offset)

    all_photos = list_photos(user_id, limit=1000, offset=0)
    q_lower = q.lower()
    results = [
        p for p in all_photos
        if q_lower in (p.get("title")         or "").lower()
        or q_lower in (p.get("description")   or "").lower()
        or q_lower in (p.get("tags")          or "").lower()
        or q_lower in (p.get("original_name") or "").lower()
    ]
    return results[offset: offset + limit]


def get_photo(photo_id, user_id):
    """
    Fetch a single photo by its integer ID and owner's user_id.
    Returns the photo dict or None if not found / wrong owner.
    """
    resp = _photos().get_item(Key={
        "user_id": str(user_id),
        "id":      Decimal(photo_id),
    })
    item = resp.get("Item")
    if not item:
        return None
    return _item_to_photo(item)
