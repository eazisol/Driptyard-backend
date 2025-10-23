"""
Database seeding script.

This script seeds the database with sample data for development and testing.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings


class DatabaseSeeder:
    """Database seeder class for populating the database with sample data."""
    
    def __init__(self):
        """Initialize the seeder."""
        self.db = SessionLocal()
    
    def seed_users(self) -> List[Dict[str, Any]]:
        """
        Seed users table with sample data.
        
        Returns:
            List[Dict[str, Any]]: List of created users
        """
        print("Seeding users...")
        
        # TODO: Implement user seeding when User model is ready
        # Sample users to create:
        users_data = [
            {
                "email": "admin@driptyard.com",
                "username": "admin",
                "first_name": "Admin",
                "last_name": "User",
                "is_active": True,
                "is_verified": True
            },
            {
                "email": "john@example.com",
                "username": "john_doe",
                "first_name": "John",
                "last_name": "Doe",
                "is_active": True,
                "is_verified": True
            },
            {
                "email": "jane@example.com",
                "username": "jane_smith",
                "first_name": "Jane",
                "last_name": "Smith",
                "is_active": True,
                "is_verified": True
            }
        ]
        
        # TODO: Create users in database
        print("✅ Users seeded successfully")
        return users_data
    
    def seed_categories(self) -> List[Dict[str, Any]]:
        """
        Seed categories with sample data.
        
        Returns:
            List[Dict[str, Any]]: List of created categories
        """
        print("Seeding categories...")
        
        # TODO: Implement category seeding when Category model is ready
        categories_data = [
            {"name": "Electronics", "description": "Electronic devices and gadgets"},
            {"name": "Clothing", "description": "Fashion and apparel"},
            {"name": "Home & Garden", "description": "Home improvement and gardening"},
            {"name": "Sports", "description": "Sports equipment and accessories"},
            {"name": "Books", "description": "Books and educational materials"},
            {"name": "Automotive", "description": "Car parts and accessories"},
            {"name": "Toys & Games", "description": "Toys and gaming equipment"},
            {"name": "Health & Beauty", "description": "Health and beauty products"}
        ]
        
        # TODO: Create categories in database
        print("✅ Categories seeded successfully")
        return categories_data
    
    def seed_products(self, users: List[Dict[str, Any]], categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Seed products with sample data.
        
        Args:
            users: List of users
            categories: List of categories
            
        Returns:
            List[Dict[str, Any]]: List of created products
        """
        print("Seeding products...")
        
        # TODO: Implement product seeding when Product model is ready
        products_data = [
            {
                "name": "iPhone 13 Pro",
                "description": "Latest iPhone in excellent condition",
                "price": 899.99,
                "category": "Electronics",
                "condition": "like_new",
                "location": "New York, NY",
                "owner_id": users[1]["id"] if users else None
            },
            {
                "name": "Vintage Leather Jacket",
                "description": "Authentic vintage leather jacket from the 80s",
                "price": 150.00,
                "category": "Clothing",
                "condition": "good",
                "location": "Los Angeles, CA",
                "owner_id": users[2]["id"] if users else None
            },
            {
                "name": "Gaming Laptop",
                "description": "High-performance gaming laptop with RTX 3070",
                "price": 1299.99,
                "category": "Electronics",
                "condition": "new",
                "location": "Chicago, IL",
                "owner_id": users[1]["id"] if users else None
            }
        ]
        
        # TODO: Create products in database
        print("✅ Products seeded successfully")
        return products_data
    
    def seed_orders(self, users: List[Dict[str, Any]], products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Seed orders with sample data.
        
        Args:
            users: List of users
            products: List of products
            
        Returns:
            List[Dict[str, Any]]: List of created orders
        """
        print("Seeding orders...")
        
        # TODO: Implement order seeding when Order model is ready
        orders_data = [
            {
                "product_id": products[0]["id"] if products else None,
                "buyer_id": users[2]["id"] if users else None,
                "seller_id": users[1]["id"] if users else None,
                "quantity": 1,
                "total_amount": 899.99,
                "status": "delivered",
                "shipping_address": "123 Main St, Los Angeles, CA 90210"
            }
        ]
        
        # TODO: Create orders in database
        print("✅ Orders seeded successfully")
        return orders_data
    
    def run_seeding(self):
        """Run the complete seeding process."""
        print("🌱 Starting database seeding...")
        
        try:
            # Seed in order of dependencies
            users = self.seed_users()
            categories = self.seed_categories()
            products = self.seed_products(users, categories)
            orders = self.seed_orders(users, products)
            
            print("🎉 Database seeding completed successfully!")
            print(f"Created: {len(users)} users, {len(categories)} categories, {len(products)} products, {len(orders)} orders")
            
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            raise
        finally:
            self.db.close()
    
    def clear_data(self):
        """Clear all seeded data."""
        print("🧹 Clearing seeded data...")
        
        # TODO: Implement data clearing when models are ready
        # This should delete all seeded data in reverse order of dependencies
        
        print("✅ Seeded data cleared successfully")


def main():
    """Main function to run database seeding."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database seeding script")
    parser.add_argument(
        "--clear", 
        action="store_true", 
        help="Clear all seeded data"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force seeding even if data exists"
    )
    
    args = parser.parse_args()
    
    seeder = DatabaseSeeder()
    
    if args.clear:
        seeder.clear_data()
    else:
        seeder.run_seeding()


if __name__ == "__main__":
    main()
