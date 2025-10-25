"""
Simple SQLite database setup for JARVIS 3.0 development
Works without external dependencies for testing purposes
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