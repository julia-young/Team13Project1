"""
Run schema.sql against RDS to create the photo_gallery database and tables.
Uses the same env vars as the app (DB_HOST, DB_USER, DB_PASS, DB_PORT).
Run once from EC2 (or anywhere that can reach RDS): python init_db.py
"""
import os
import pymysql

def main():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        sql = f.read()

    conn = pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        port=int(os.environ.get("DB_PORT", "3306")),
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            for stmt in sql.split(";"):
                stmt = "\n".join(
                    line for line in stmt.split("\n")
                    if line.strip() and not line.strip().startswith("--")
                ).strip()
                if stmt:
                    cur.execute(stmt)
        print("Schema applied: photo_gallery database and tables created.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
