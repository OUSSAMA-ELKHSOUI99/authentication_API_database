import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 1. Base configuration (connects to the default 'postgres' database first)
BASE_CONFIG = {
    "dbname": "postgres", 
    "user": "postgres",
    "password": "oussama", # .env
    "host": "127.0.0.1",
    "port": "5432"
}

# 2. Target database to create
TARGET_DB = "indie_core"

def setup_database():
    # --- PHASE 1: CREATE THE DATABASE ---
    print(f"⏳ Connecting to default server to check/create '{TARGET_DB}'...")
    try:
        conn = psycopg2.connect(**BASE_CONFIG)
        # PostgreSQL requires autocommit to be True to run CREATE DATABASE
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if the database already exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (TARGET_DB,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute(f"CREATE DATABASE {TARGET_DB};")
            print(f"✅ Database '{TARGET_DB}' created successfully.")
        else:
            print(f"⚡ Database '{TARGET_DB}' already exists. Skipping creation.")

    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return  # Stop the script if we can't create/find the DB
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'conn' in locals() and conn: conn.close()

    # --- PHASE 2: CREATE THE TABLES ---
    print(f"\n⏳ Connecting to '{TARGET_DB}' to set up tables...")
    
    # Update config to connect to our new database instead of the default one
    NEW_CONFIG = BASE_CONFIG.copy()
    NEW_CONFIG["dbname"] = TARGET_DB

    try:
        conn = psycopg2.connect(**NEW_CONFIG)
        cursor = conn.cursor()

        # Create the users table (IF NOT EXISTS prevents errors if run twice)
        create_users_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(36) PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_users_table_query)
        conn.commit()
        print("✅ 'users' table created successfully (or already exists).")
        print("\n🎉 Setup complete! Your database is ready. You can now start your API.")

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
    finally:
        if 'cursor' in locals() and cursor: cursor.close()
        if 'conn' in locals() and conn: conn.close()

if __name__ == "__main__":
    setup_database()