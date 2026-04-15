from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import jwt
import datetime
import uuid

app = FastAPI(title="Indie App Core API")

# --- Configuration ---
DB_CONFIG = {
    "dbname": "indie_core",
    "user": "postgres",
    "password": "YOUR_POSTGRES_PASSWORD",
    "host": "127.0.0.1", # Python runs on your PC, so it uses localhost!
    "port": "5432"
}
JWT_SECRET = "my_super_secret_indie_key"

# --- Pydantic Models (Like Dart Data Classes) ---
class AuthRequest(BaseModel):
    email: str
    password: str
    name: str = "User" # Default value for login

class RefreshRequest(BaseModel):
    refresh_token: str

# --- Helper Functions ---
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_tokens(user_id: str, email: str):
    # Access Token (15 mins)
    access_payload = {
        "id": user_id, "email": email, "type": "access",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    }
    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm="HS256")

    # Refresh Token (30 days)
    refresh_payload = {
        "id": user_id, "type": "refresh",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm="HS256")

    return {"accessToken": access_token, "refreshToken": refresh_token}

# --- API Endpoints ---

@app.post("/register")
def register(request: AuthRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Check if email exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (request.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already in use")

        # 2. Insert new user
        user_id = str(uuid.uuid4())
        hashed_pw = hash_password(request.password)
        
        cursor.execute(
            "INSERT INTO users (id, email, name, password_hash) VALUES (%s, %s, %s, %s)",
            (user_id, request.email, request.name, hashed_pw)
        )
        conn.commit()

        # 3. Generate Tokens
        return create_tokens(user_id, request.email)

    finally:
        cursor.close()
        conn.close()

@app.post("/login")
def login(request: AuthRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (request.email,))
        user = cursor.fetchone()

        if not user or not verify_password(request.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        return create_tokens(user['id'], user['email'])
    finally:
        cursor.close()
        conn.close()

@app.post("/refresh")
def refresh_session(request: RefreshRequest):
    try:
        # Verify the old refresh token
        payload = jwt.decode(request.refresh_token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
            
        # In a real app, you might look up the user's email again here using payload['id']
        # For simplicity, we just generate new tokens using the ID
        return create_tokens(payload['id'], "user@email.com")
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired, please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")