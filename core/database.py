"""
Database Module
Handles SQLite database operations for user data and recommendations
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "db" / "smartinvest.db"


def get_connection():
    """Get database connection"""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # User profiles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            age INTEGER,
            investment_horizon INTEGER,
            risk_level TEXT,
            risk_score INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Recommendations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            goal TEXT,
            risk_level TEXT,
            risk_score INTEGER,
            base_allocation TEXT,
            final_allocation TEXT,
            market_conditions TEXT,
            recommended_products TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()


def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username, password, email=None):
    """
    Create a new user
    Returns: (success: bool, message: str, user_id: int or None)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            (username, password_hash, email)
        )
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return True, "Account created successfully!", user_id
    except sqlite3.IntegrityError:
        return False, "Username already exists!", None
    except Exception as e:
        return False, f"Error: {str(e)}", None


def authenticate_user(username, password):
    """
    Authenticate user credentials
    Returns: (success: bool, message: str, user_id: int or None)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return True, "Login successful!", result[0]
        else:
            return False, "Invalid username or password!", None
    except Exception as e:
        return False, f"Error: {str(e)}", None


def save_recommendation(user_id, amount, goal, risk_level, risk_score, 
                        base_allocation, final_allocation, market_conditions, 
                        recommended_products):
    """Save a recommendation to database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO recommendations 
            (user_id, amount, goal, risk_level, risk_score, base_allocation, 
             final_allocation, market_conditions, recommended_products)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            amount,
            goal,
            risk_level,
            risk_score,
            json.dumps(base_allocation),
            json.dumps(final_allocation),
            json.dumps(market_conditions),
            json.dumps(recommended_products, default=str)
        ))
        
        conn.commit()
        conn.close()
        return True, "Recommendation saved!"
    except Exception as e:
        return False, f"Error saving: {str(e)}"


def get_user_recommendations(user_id, limit=10):
    """Get user's recommendation history"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, amount, goal, risk_level, risk_score, 
                   base_allocation, final_allocation, market_conditions,
                   recommended_products, created_at
            FROM recommendations
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        
        recommendations = []
        for row in cursor.fetchall():
            recommendations.append({
                'id': row[0],
                'amount': row[1],
                'goal': row[2],
                'risk_level': row[3],
                'risk_score': row[4],
                'base_allocation': json.loads(row[5]),
                'final_allocation': json.loads(row[6]),
                'market_conditions': json.loads(row[7]),
                'recommended_products': json.loads(row[8]),
                'created_at': row[9]
            })
        
        conn.close()
        return recommendations
    except Exception as e:
        print(f"Error fetching recommendations: {e}")
        return []


def update_user_profile(user_id, age, horizon, risk_level, risk_score):
    """Update or create user profile"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if profile exists
        cursor.execute("SELECT id FROM user_profiles WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE user_profiles 
                SET age = ?, investment_horizon = ?, risk_level = ?, 
                    risk_score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (age, horizon, risk_level, risk_score, user_id))
        else:
            cursor.execute("""
                INSERT INTO user_profiles 
                (user_id, age, investment_horizon, risk_level, risk_score)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, age, horizon, risk_level, risk_score))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating profile: {e}")
        return False


def get_user_profile(user_id):
    """Get user profile data"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT age, investment_horizon, risk_level, risk_score
            FROM user_profiles
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'age': result[0],
                'horizon': result[1],
                'risk_level': result[2],
                'risk_score': result[3]
            }
        return None
    except Exception as e:
        print(f"Error fetching profile: {e}")
        return None


# Initialize database on module import
init_database()
