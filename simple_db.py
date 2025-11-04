"""
=============================================================================
JARVIS 3.0 - USER DATABASE MODULE (SQLite User Management)
=============================================================================

PURPOSE:
--------
Manages the users table in SQLite for authentication. Stores user accounts,
credentials (hashed passwords), and user metadata. This is the ONLY file
that directly interacts with the users database (jarvis_dev.db).

RESPONSIBILITY:
---------------
- Initialize users table in SQLite (id, email, username, password_hash, created_at)
- Create new users (INSERT operations)
- Retrieve users by username or ID (SELECT operations)
- Update user information (UPDATE operations)
- Password hash storage (SHA256 hashed passwords)

DATA FLOW (User Operations):
-----------------------------
CREATE USER FLOW:
1. simple_auth.py calls db.create_user(email, username, password_hash)
2. This module connects to jarvis_dev.db SQLite database
3. Execute INSERT INTO users (email, username, password_hash, created_at)
4. Commit transaction and return user_id
5. Close database connection (context manager ensures cleanup)

FETCH USER FLOW:
1. simple_auth.py calls db.get_user_by_username(username) during login
2. Connect to jarvis_dev.db
3. Execute SELECT * FROM users WHERE username = ?
4. Fetch one row from results
5. Convert row tuple to dictionary with column names
6. Return user dict {id, email, username, password_hash, created_at} or None

VERIFY USER EXISTS FLOW:
1. simple_auth.py calls db.get_user_by_id(user_id) during token validation
2. Connect to jarvis_dev.db
3. Execute SELECT * FROM users WHERE id = ?
4. Return user dict or None if not found

DATABASE SCHEMA:
----------------
Table: users
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- email (TEXT UNIQUE NOT NULL)
- username (TEXT UNIQUE NOT NULL)
- password_hash (TEXT NOT NULL) - SHA256 hashed, NOT plaintext
- created_at (TEXT) - ISO format timestamp

DEPENDENCIES:
-------------
- sqlite3: Python standard library for SQLite operations
- hashlib: SHA256 password hashing (used in simple_auth.py)
- datetime: Timestamp generation for created_at field

USED BY:
--------
- simple_auth.py: User registration, login, token validation
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional
import hashlib

DATABASE_PATH = "jarvis_dev.db"

class SimpleDB:
    """Simple SQLite database for development"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_db()
    
    def init_db(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                full_name TEXT,
                bio TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_verified BOOLEAN DEFAULT 0,
                is_premium BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"Database initialized: {self.db_path}")
    
    def create_user(self, email: str, username: str, password: str, full_name: str = None, bio: str = None) -> Optional[dict]:
        """Create a new user"""
        try:
            # Hash password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (email, username, hashed_password, full_name, bio, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (email, username, hashed_password, full_name, bio, datetime.now()))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                "id": user_id,
                "email": email,
                "username": username,
                "full_name": full_name
            }
            
        except sqlite3.IntegrityError as e:
            if "email" in str(e):
                return {"error": "Email already exists"}
            elif "username" in str(e):
                return {"error": "Username already exists"}
            else:
                return {"error": "User creation failed"}
        except Exception as e:
            return {"error": str(e)}
    
    def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authenticate user with email and password"""
        try:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, email, username, full_name, is_active, is_verified, is_premium, created_at
                FROM users 
                WHERE email = ? AND hashed_password = ?
            """, (email, hashed_password))
            
            user = cursor.fetchone()
            
            if user:
                # Update last login
                cursor.execute("""
                    UPDATE users SET last_login = ? WHERE id = ?
                """, (datetime.now(), user[0]))
                conn.commit()
                
                conn.close()
                
                return {
                    "id": user[0],
                    "email": user[1],
                    "username": user[2],
                    "full_name": user[3],
                    "is_active": bool(user[4]),
                    "is_verified": bool(user[5]),
                    "is_premium": bool(user[6]),
                    "created_at": user[7]
                }
            
            conn.close()
            return None
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Get user by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, email, username, full_name, is_active, is_verified, is_premium, created_at
                FROM users 
                WHERE id = ?
            """, (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    "id": user[0],
                    "email": user[1],
                    "username": user[2],
                    "full_name": user[3],
                    "is_active": bool(user[4]),
                    "is_verified": bool(user[5]),
                    "is_premium": bool(user[6]),
                    "created_at": user[7]
                }
            
            return None
            
        except Exception as e:
            return {"error": str(e)}

# Global database instance
db = SimpleDB()