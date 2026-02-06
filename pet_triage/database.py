"""
Database Module
===============

SQLite database for users and pet profiles.
In production, replace with PostgreSQL or similar.

Tables:
- users: User accounts (email, password_hash, name)
- pet_profiles: Pet information linked to users
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "fuzzy_friend.db")


@contextmanager
def get_db():
    """Get database connection with automatic cleanup."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dicts
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database tables."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        
        # Pet profiles table (one per user for now, can extend to multiple pets)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pet_profiles (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                species TEXT NOT NULL,
                breed TEXT,
                age_years INTEGER,
                weight REAL,
                weight_unit TEXT DEFAULT 'kg',
                sex TEXT,
                spay_neuter_status TEXT,
                last_heat_cycle TEXT,
                vaccination_status TEXT,
                lifestyle TEXT,
                allergies TEXT,
                medical_history_flags TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Triage sessions table - stores triage history for users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS triage_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                session_id TEXT NOT NULL,
                species TEXT,
                category TEXT,
                user_description TEXT,
                risk_level TEXT,
                response_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        conn.commit()
        print(f"Database initialized at {DB_PATH}")



# =============================================================================
# User Operations
# =============================================================================

def create_user(user_id: str, email: str, password_hash: str, name: str) -> bool:
    """Create a new user."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (id, email, password_hash, name, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, email.lower(), password_hash, name, datetime.utcnow().isoformat()))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False  # Email already exists


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower(),))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


# =============================================================================
# Pet Profile Operations
# =============================================================================

def create_or_update_pet_profile(
    user_id: str,
    name: str,
    species: str,
    breed: str = None,
    age_years: int = None,
    weight: float = None,
    weight_unit: str = "kg",
    sex: str = None,
    spay_neuter_status: str = None,
    last_heat_cycle: str = None,
    vaccination_status: str = None,
    lifestyle: str = None,
    allergies: str = None,
    medical_history_flags: List[str] = None
) -> Dict[str, Any]:
    """Create or update pet profile for a user."""
    
    # Convert list to comma-separated string
    history_str = ",".join(medical_history_flags) if medical_history_flags else None
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if profile exists
        cursor.execute("SELECT id FROM pet_profiles WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()
        
        now = datetime.utcnow().isoformat()
        
        if existing:
            # Update existing profile
            cursor.execute("""
                UPDATE pet_profiles SET
                    name = ?, species = ?, breed = ?, age_years = ?,
                    weight = ?, weight_unit = ?, sex = ?, spay_neuter_status = ?,
                    last_heat_cycle = ?, vaccination_status = ?, lifestyle = ?,
                    allergies = ?, medical_history_flags = ?, updated_at = ?
                WHERE user_id = ?
            """, (name, species, breed, age_years, weight, weight_unit, sex,
                  spay_neuter_status, last_heat_cycle, vaccination_status, lifestyle,
                  allergies, history_str, now, user_id))
            profile_id = existing["id"]
        else:
            # Create new profile
            profile_id = f"pet_{user_id}_{int(datetime.utcnow().timestamp())}"
            cursor.execute("""
                INSERT INTO pet_profiles (
                    id, user_id, name, species, breed, age_years, weight, weight_unit,
                    sex, spay_neuter_status, last_heat_cycle, vaccination_status,
                    lifestyle, allergies, medical_history_flags, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (profile_id, user_id, name, species, breed, age_years, weight, weight_unit,
                  sex, spay_neuter_status, last_heat_cycle, vaccination_status, lifestyle,
                  allergies, history_str, now))
        
        conn.commit()
        
        return get_pet_profile(user_id)


def get_pet_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get pet profile for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pet_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            profile = dict(row)
            # Convert medical_history_flags back to list
            if profile.get("medical_history_flags"):
                profile["medical_history_flags"] = profile["medical_history_flags"].split(",")
            else:
                profile["medical_history_flags"] = []
            return profile
        return None


def delete_pet_profile(user_id: str) -> bool:
    """Delete pet profile for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pet_profiles WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0


# =============================================================================
# Triage Session Operations
# =============================================================================

def save_triage_session(
    session_id: str,
    species: str = None,
    category: str = None,
    user_description: str = None,
    risk_level: str = None,
    response_json: str = None,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Save a triage session to the database.
    
    Args:
        session_id: Frontend session identifier
        species: Pet species (dog/cat)
        category: Symptom category
        user_description: User's symptom description
        risk_level: Triage risk level (ER/TODAY/SOON/MONITOR)
        response_json: Full JSON response as string
        user_id: User ID if logged in (optional)
    
    Returns:
        Saved session data
    """
    import uuid
    
    record_id = f"triage_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO triage_sessions (
                id, user_id, session_id, species, category,
                user_description, risk_level, response_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (record_id, user_id, session_id, species, category,
              user_description, risk_level, response_json, now))
        conn.commit()
    
    return {
        "id": record_id,
        "session_id": session_id,
        "user_id": user_id,
        "species": species,
        "category": category,
        "risk_level": risk_level,
        "created_at": now
    }


def get_triage_sessions(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get triage history for a user.
    
    Args:
        user_id: User ID
        limit: Maximum number of sessions to return
    
    Returns:
        List of triage sessions, most recent first
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, session_id, species, category, user_description,
                   risk_level, created_at
            FROM triage_sessions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_triage_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific triage session by ID.
    
    Args:
        session_id: Session ID (either record ID or frontend session_id)
    
    Returns:
        Full session data including response_json
    """
    with get_db() as conn:
        cursor = conn.cursor()
        # Try matching by record ID first, then by session_id
        cursor.execute("""
            SELECT * FROM triage_sessions
            WHERE id = ? OR session_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (session_id, session_id))
        row = cursor.fetchone()
        if row:
            session = dict(row)
            # Parse response_json if present
            if session.get("response_json"):
                import json
                try:
                    session["response"] = json.loads(session["response_json"])
                except json.JSONDecodeError:
                    session["response"] = None
            return session
        return None


# Initialize database on module import
init_db()
