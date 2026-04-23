"""
First Admin User Setup Script for SARAI

This script creates the initial admin user for SARAI.
Run this ONCE after deployment to create your first admin account.

Usage:
    cd /app/backend
    python scripts/create_admin.py
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Import auth utilities
from utils.auth import hash_password


async def create_first_admin():
    """Create the first admin user"""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("\n" + "="*60)
    print("SARAI - First Admin User Setup")
    print("="*60 + "\n")
    
    # Check if any admin user exists
    existing_admin = await db.users.find_one({"role": "admin"}, {"_id": 0})
    
    if existing_admin:
        print("❌ Admin user already exists:")
        print(f"   Email: {existing_admin['email']}")
        print(f"   Name: {existing_admin['name']}")
        print(f"   Created: {existing_admin.get('created_at', 'N/A')}")
        print("\n⚠️  If you've forgotten your password, ask another admin to reset it")
        print("   or manually update the password_hash in the database.\n")
        await client.close()
        return
    
    # Create first admin user
    admin_email = "admin"
    admin_password = "Admin@2026!"
    admin_name = "System Administrator"
    
    admin_user = {
        "id": str(uuid.uuid4()),
        "email": admin_email,  # Username (not necessarily email)
        "password_hash": hash_password(admin_password),
        "name": admin_name,
        "role": "admin",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": None
    }
    
    # Insert into database
    result = await db.users.insert_one(admin_user)
    
    print("✅ First admin user created successfully!\n")
    print("="*60)
    print("LOGIN CREDENTIALS")
    print("="*60)
    print(f"Email:    {admin_email}")
    print(f"Password: {admin_password}")
    print("="*60)
    print("\n⚠️  IMPORTANT SECURITY NOTES:")
    print("   1. CHANGE THIS PASSWORD IMMEDIATELY after first login")
    print("   2. Store credentials securely")
    print("   3. Do not share this password")
    print("   4. Create separate user accounts for other staff members")
    print("\n✅ You can now login to SARAI with the above credentials\n")
    
    await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(create_first_admin())
    except KeyError as e:
        print(f"\n❌ ERROR: Missing environment variable: {e}")
        print("   Make sure .env file is configured with MONGO_URL and DB_NAME\n")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()
