"""
Database seeding script for categories and brands.

This script seeds the database with all category and brand data.
"""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.category import (
    MainCategory,
    CategoryType,
    SubCategory,
    Brand,
    Gender
)


def seed_genders(db: Session):
    """Seed genders table."""
    print("Seeding genders...")
    
    genders = ["male", "female", "unisex"]
    gender_objects = {}
    
    for gender_name in genders:
        existing = db.query(Gender).filter(Gender.name == gender_name).first()
        if existing:
            gender_objects[gender_name] = existing
            print(f"  - Gender '{gender_name}' already exists")
        else:
            gender = Gender(name=gender_name)
            db.add(gender)
            gender_objects[gender_name] = gender
            print(f"  + Created gender: {gender_name}")
    
    db.commit()
    return gender_objects


def seed_main_categories(db: Session):
    """Seed main categories table."""
    print("\nSeeding main categories...")
    
    main_categories = ["Fashion", "Collectibles", "Lifestyle"]
    category_objects = {}
    
    for cat_name in main_categories:
        existing = db.query(MainCategory).filter(MainCategory.name == cat_name).first()
        if existing:
            category_objects[cat_name] = existing
            print(f"  - Main category '{cat_name}' already exists")
        else:
            category = MainCategory(name=cat_name)
            db.add(category)
            category_objects[cat_name] = category
            print(f"  + Created main category: {cat_name}")
    
    db.commit()
    return category_objects


def seed_category_types(db: Session, main_categories: dict):
    """Seed category types table."""
    print("\nSeeding category types...")
    
    category_types_data = {
        "Fashion": [
            "Tops",
            "Bottoms",
            "Outerwear",
            "Footwear",
            "Accessories"
        ],
        "Lifestyle": [
            "Luxury Bicycles",
            "Road Bikes",
            "Fixed Gear / Single Speed",
            "Mountain Bikes",
            "Folding Bikes",
            "Framesets / Components",
            "Helmets",
            "Gloves",
            "Riding Apparel",
            "Bags",
            "Tools & Accessories"
        ],
        "Collectibles": [
            "Pokémon",
            "Yu-Gi-Oh",
            "One Piece TCG",
            "Magic the Gathering",
            "Labubu",
            "Bearbrick",
            "Kaws",
            "Other"
        ]
    }
    
    type_objects = {}
    
    for main_cat_name, types in category_types_data.items():
        main_cat = main_categories[main_cat_name]
        for type_name in types:
            existing = db.query(CategoryType).filter(
                CategoryType.name == type_name,
                CategoryType.parent_id == main_cat.id
            ).first()
            
            if existing:
                type_objects[type_name] = existing
                print(f"  - Category type '{type_name}' already exists")
            else:
                category_type = CategoryType(name=type_name, parent_id=main_cat.id)
                db.add(category_type)
                type_objects[type_name] = category_type
                print(f"  + Created category type: {type_name} (under {main_cat_name})")
    
    db.commit()
    return type_objects


def seed_sub_categories(db: Session, category_types: dict, genders: dict):
    """Seed sub categories table."""
    print("\nSeeding sub categories...")
    
    # Male sub-categories
    male_sub_categories = {
        "Tops": [
            "Long Sleeve T-Shirts",
            "Short Sleeve T-Shirts",
            "Tank Tops & Sleeveless",
            "Polos",
            "Button Ups",
            "Sweaters & Knitwear",
            "Sweatshirts & Hoodies",
            "Jerseys"
        ],
        "Bottoms": [
            "Casual Pants",
            "Cropped Pants",
            "Denim",
            "Overalls & Jumpsuits",
            "Shorts",
            "Sweatpants & Joggers",
            "Swimwear"
        ],
        "Outerwear": [
            "Bombers",
            "Denim Jackets",
            "Leather Jackets",
            "Light Jackets",
            "Heavy Coats",
            "Parkas",
            "Raincoats",
            "Blazers",
            "Cloaks & Capes",
            "Vests"
        ],
        "Footwear": [
            "Boots",
            "Casual Leather Shoes",
            "Formal Shoes",
            "Hi-Top Sneakers",
            "Low-Top Sneakers",
            "Sandals",
            "Slip Ons"
        ],
        "Accessories": [
            "Bags & Luggage",
            "Belts",
            "Glasses / Sunglasses",
            "Gloves & Scarves",
            "Hats",
            "Jewelry & Watches",
            "Wallets",
            "Socks & Underwear",
            "Miscellaneous"
        ]
    }
    
    # Female sub-categories
    female_sub_categories = {
        "Tops": [
            "Crop Tops",
            "Blouses",
            "Bodysuits"
        ],
        "Bottoms": [
            "Leggings",
            "Maxi / Midi / Mini Skirts",
            "Dresses"
        ],
        "Outerwear": [
            "Blazers"
        ],
        "Footwear": [
            "Heels",
            "Platforms",
            "Flats"
        ],
        "Accessories": [
            "Hair Accessories"
        ]
    }
    
    count = 0
    
    # Seed male sub-categories
    for type_name, sub_cats in male_sub_categories.items():
        if type_name in category_types:
            type_obj = category_types[type_name]
            for sub_cat_name in sub_cats:
                existing = db.query(SubCategory).filter(
                    SubCategory.name == sub_cat_name,
                    SubCategory.type_id == type_obj.id,
                    SubCategory.gender_id == genders["male"].id
                ).first()
                
                if not existing:
                    sub_category = SubCategory(
                        name=sub_cat_name,
                        type_id=type_obj.id,
                        gender_id=genders["male"].id
                    )
                    db.add(sub_category)
                    count += 1
                    print(f"  + Created sub-category: {sub_cat_name} (Male - {type_name})")
    
    # Seed female sub-categories
    for type_name, sub_cats in female_sub_categories.items():
        if type_name in category_types:
            type_obj = category_types[type_name]
            for sub_cat_name in sub_cats:
                existing = db.query(SubCategory).filter(
                    SubCategory.name == sub_cat_name,
                    SubCategory.type_id == type_obj.id,
                    SubCategory.gender_id == genders["female"].id
                ).first()
                
                if not existing:
                    sub_category = SubCategory(
                        name=sub_cat_name,
                        type_id=type_obj.id,
                        gender_id=genders["female"].id
                    )
                    db.add(sub_category)
                    count += 1
                    print(f"  + Created sub-category: {sub_cat_name} (Female - {type_name})")
    
    db.commit()
    print(f"\n  + Created {count} new sub-categories")


def seed_brands(db: Session):
    """Seed brands table."""
    print("\nSeeding brands...")
    
    brands = [
        "Ralph Lauren",
        "Valentino",
        "Lacoste",
        "BOSS (Hugo Boss)",
        "Chanel",
        "Prada",
        "Gucci",
        "Céline",
        "D&G (Dolce & Gabbana)",
        "Marc Jacobs",
        "Louis Vuitton (LV)",
        "Calvin Klein (CK)",
        "Dior",
        "Versace",
        "Roberto Cavalli",
        "Fendi",
        "Givenchy",
        "Miu Miu",
        "BVLGARI (Bvlgari)",
        "Chloé",
        "Hermès (Hermes)",
        "Balenciaga",
        "Burberry",
        "Nike",
        "Tory Burch",
        "Adidas",
        "Vivienne Westwood",
        "Reebok",
        "The North Face",
        "Asics",
        "Giorgio Armani",
        "Puma",
        "Under Armour",
        "Vans",
        "New Balance",
        "FILA",
        "Hollister",
        "Oscar de la Renta",
        "Coach",
        "Cartier",
        "Titoni",
        "Levi's",
        "Swarovski",
        "Estée Lauder",
        "Yves Saint Laurent (YSL)",
        "Salvatore Ferragamo",
        "Ray-Ban",
        "ZARA",
        "Pandora",
        "Kookai",
        "River Island",
        "Aldo Brue",
        "Christian Louboutin",
        "Abercrombie & Fitch",
        "Ted Baker",
        "Other / Not Listed"
    ]
    
    count = 0
    for brand_name in brands:
        existing = db.query(Brand).filter(Brand.name == brand_name).first()
        if existing:
            print(f"  - Brand '{brand_name}' already exists")
        else:
            brand = Brand(name=brand_name, active=True)
            db.add(brand)
            count += 1
            print(f"  + Created brand: {brand_name}")
    
    db.commit()
    print(f"\n  + Created {count} new brands")


def main():
    """Main function to run database seeding."""
    print("Starting category and brand seeding...")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Seed in order of dependencies
        genders = seed_genders(db)
        main_categories = seed_main_categories(db)
        category_types = seed_category_types(db, main_categories)
        seed_sub_categories(db, category_types, genders)
        seed_brands(db)
        
        print("\n" + "=" * 60)
        print("Database seeding completed successfully!")
        print("\nSummary:")
        print(f"  - Genders: {len(genders)}")
        print(f"  - Main Categories: {len(main_categories)}")
        print(f"  - Category Types: {len(category_types)}")
        print(f"  - Brands: {db.query(Brand).count()}")
        print(f"  - Sub Categories: {db.query(SubCategory).count()}")
        
    except Exception as e:
        print(f"\nError during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

