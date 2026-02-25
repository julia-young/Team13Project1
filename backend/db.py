"""
Database switch layer.

Reads DB_PROVIDER from the environment and delegates all function calls
to the matching backend module:
  dynamo  → db_dynamo.py  (Part A)
  mongo   → db_mongo.py   (Part B)
  mysql   → inline below  (Project 1 fallback)

routes.py always imports this file as `db` and calls db.create_user(),
db.add_photo(), etc. — it never needs to know which backend is active.
"""
import os

_provider = os.environ.get("DB_PROVIDER", "mysql")

if _provider == "dynamo":
    from db_dynamo import (
        create_user,
        get_user_by_username,
        add_photo,
        list_photos,
        search_photos,
        get_photo,
    )

elif _provider == "mongo":
    from db_mongo import (
        create_user,
        get_user_by_username,
        add_photo,
        list_photos,
        search_photos,
        get_photo,
    )

else:
    # MySQL fallback — original Project 1 implementation
    import pymysql

    def get_conn():
        return pymysql.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASS"],
            database=os.environ.get("DB_NAME", "photo_gallery"),
            port=int(os.environ.get("DB_PORT", "3306")),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )

    def create_user(username, email, password_hash):
        sql = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (username, email, password_hash))
                return cur.lastrowid

    def get_user_by_username(username):
        sql = "SELECT id, username, email, password_hash FROM users WHERE username = %s"
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (username,))
                return cur.fetchone()

    def add_photo(user_id, s3_bucket, s3_key, original_name, title=None, description=None, tags=None, content_type=None, size_bytes=None):
        sql = """
        INSERT INTO photos (user_id, s3_bucket, s3_key, original_name, title, description, tags, content_type, size_bytes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, s3_bucket, s3_key, original_name, title, description, tags, content_type, size_bytes))
                return cur.lastrowid

    def search_photos(user_id, q=None, limit=50, offset=0):
        if not q:
            return list_photos(user_id, limit, offset)
        sql = """
        SELECT id, user_id, s3_bucket, s3_key, original_name, title, description, tags, uploaded_at
        FROM photos
        WHERE user_id = %s
          AND (
            title LIKE CONCAT('%%', %s, '%%')
            OR description LIKE CONCAT('%%', %s, '%%')
            OR tags LIKE CONCAT('%%', %s, '%%')
          )
        ORDER BY uploaded_at DESC
        LIMIT %s OFFSET %s
        """
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, q, q, q, limit, offset))
                return cur.fetchall()

    def get_photo(photo_id, user_id):
        sql = """
        SELECT id, user_id, s3_bucket, s3_key, original_name, title, description, tags, content_type, size_bytes, uploaded_at
        FROM photos WHERE id = %s AND user_id = %s
        """
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (photo_id, user_id))
                return cur.fetchone()

    def list_photos(user_id, limit=50, offset=0):
        sql = """
        SELECT id, user_id, s3_bucket, s3_key, original_name, title, description, tags, uploaded_at
        FROM photos WHERE user_id = %s ORDER BY uploaded_at DESC LIMIT %s OFFSET %s
        """
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, limit, offset))
                return cur.fetchall()