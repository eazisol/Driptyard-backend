"""
Script to assign moderator role and set all permissions for a user.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models.user import User
from app.models.moderator import ModeratorPermission
from app.models.product import Product
from app.models.order import Order
from app.models.report import ProductReport
from sqlalchemy.exc import IntegrityError


def add_moderator_permissions(user_id: int):
    """Add moderator role and all permissions for a user."""
    db = SessionLocal()
    
    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            print(f"Error: User with ID {user_id} not found")
            return False
        
        # Set moderator flag
        user.is_moderator = True
        
        # Check if permissions already exist
        existing_permissions = db.query(ModeratorPermission).filter(
            ModeratorPermission.user_id == user_id
        ).first()
        
        if existing_permissions:
            # Update existing permissions
            existing_permissions.can_see_dashboard = True
            existing_permissions.can_see_users = True
            existing_permissions.can_manage_users = True
            existing_permissions.can_see_listings = True
            existing_permissions.can_manage_listings = True
            existing_permissions.can_see_spotlight_history = True
            existing_permissions.can_spotlight = True
            existing_permissions.can_remove_spotlight = True
            existing_permissions.can_see_flagged_content = True
            existing_permissions.can_manage_flagged_content = True
            print(f"Updated permissions for user ID {user_id}")
        else:
            # Create new permissions
            permissions = ModeratorPermission(
                user_id=user_id,
                can_see_dashboard=True,
                can_see_users=True,
                can_manage_users=True,
                can_see_listings=True,
                can_manage_listings=True,
                can_see_spotlight_history=True,
                can_spotlight=True,
                can_remove_spotlight=True,
                can_see_flagged_content=True,
                can_manage_flagged_content=True
            )
            db.add(permissions)
            print(f"Created permissions for user ID {user_id}")
        
        # Commit changes
        db.commit()
        print(f"Successfully added all permissions for user ID {user_id}")
        print(f"User: {user.username} ({user.email})")
        return True
        
    except IntegrityError as e:
        db.rollback()
        print(f"Error: {str(e)}")
        return False
    except Exception as e:
        db.rollback()
        print(f"Error: {str(e)}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    user_id = 10
    print(f"Adding moderator role and all permissions for user ID {user_id}...")
    success = add_moderator_permissions(user_id)
    
    if success:
        print("\n✅ Done!")
    else:
        print("\n❌ Failed!")
        sys.exit(1)

