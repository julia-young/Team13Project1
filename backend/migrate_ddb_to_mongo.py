import os
from decimal import Decimal
import boto3
from boto3.dynamodb.types import TypeDeserializer
from pymongo import MongoClient

AWS_REGION = os.environ.get("AWS_REGION", "us-east-2")
USERS_TABLE = os.environ["DDB_USERS_TABLE"]
PHOTOS_TABLE = os.environ["DDB_PHOTOS_TABLE"]
MONGO_URI = os.environ["MONGO_URI"]
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "SE4220")

deser = TypeDeserializer()

def ddb_to_py(item):
    out = {k: deser.deserialize(v) for k, v in item.items()}

    def fix(v):
        if isinstance(v, list):
            return [fix(x) for x in v]
        if isinstance(v, dict):
            return {kk: fix(vv) for kk, vv in v.items()}
        if isinstance(v, set):
            return list(v)
        if isinstance(v, Decimal):
            return int(v) if v % 1 == 0 else float(v)
        return v

    return fix(out)

def scan_all(ddb, table):
    items = []
    kwargs = {"TableName": table}
    while True:
        resp = ddb.scan(**kwargs)
        items.extend(resp.get("Items", []))
        last = resp.get("LastEvaluatedKey")
        if not last:
            break
        kwargs["ExclusiveStartKey"] = last
    return items

def main():
    ddb = boto3.client("dynamodb", region_name=AWS_REGION)

    users_raw = scan_all(ddb, USERS_TABLE)
    photos_raw = scan_all(ddb, PHOTOS_TABLE)

    users = [ddb_to_py(i) for i in users_raw]
    photos = [ddb_to_py(i) for i in photos_raw]

    print(f"Dynamo counts -> users: {len(users)} photos: {len(photos)}")

    mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=20000)
    db = mongo.get_default_database()
    if db is None:
        db = mongo[MONGO_DB_NAME]

    users_col = db["users"]
    photos_col = db["photos"]

    users_col.delete_many({})
    photos_col.delete_many({})

    if users:
        users_col.insert_many(users)
    if photos:
        photos_col.insert_many(photos)

    print("Mongo counts -> users:", users_col.count_documents({}),
          "photos:", photos_col.count_documents({}))

    print("Sample user:", users_col.find_one({}, {"_id": 0}))
    print("Sample photo:", photos_col.find_one({}, {"_id": 0}))

if __name__ == "__main__":
    main()
