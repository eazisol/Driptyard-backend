# Product Database Structure

This document outlines all the fields/columns in the `products` table.

## Base Fields (Inherited from BaseModel)

| Field Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `id` | UUID | No | auto-generated | Primary key, unique identifier |
| `created_at` | DateTime (timezone) | No | now() | Record creation timestamp |
| `updated_at` | DateTime (timezone) | No | now() | Last update timestamp |

## Basic Product Information

| Field Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `title` | String(255) | No | - | Product title (indexed) |
| `description` | Text | Yes | NULL | Product description |
| `price` | Numeric(10, 2) | No | - | Product price |
| `category` | String(100) | Yes | NULL | Product category (indexed) |
| `condition` | String(50) | Yes | NULL | Product condition (Like New, Excellent, Brand New, Good, Fair) |

## Deal Method and Meetup Details

| Field Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `deal_method` | String(20) | No | "delivery" | Deal method: "delivery" or "meetup" |
| `meetup_date` | String(10) | Yes | NULL | Meetup date (YYYY-MM-DD format) |
| `meetup_location` | String(255) | Yes | NULL | Meetup location |
| `meetup_time` | String(5) | Yes | NULL | Meetup time (HH:MM format) |
| `meetup_locations` | JSON | Yes | NULL | Array of meetup locations (JSON) |

## Product Status

| Field Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `is_active` | Boolean | No | true | Whether product is active |
| `is_sold` | Boolean | No | false | Whether product is sold |
| `is_featured` | Boolean | No | false | Whether product is featured (indexed) |
| `is_verified` | Boolean | No | false | Whether product is verified (indexed) |
| `is_flagged` | Boolean | No | false | Whether product is flagged for review (indexed) |
| `verification_code` | String(6) | Yes | NULL | Product verification code |
| `verification_expires_at` | DateTime | Yes | NULL | Verification code expiration |
| `verification_attempts` | Integer | No | 0 | Number of verification attempts |

## Stock Management

| Field Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `stock_quantity` | Integer | No | 1 | Stock quantity |
| `stock_status` | String(50) | No | "In Stock" | Stock status (In Stock, Out of Stock, Limited) |

## Location and Shipping

| Field Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `location` | String(255) | Yes | NULL | Product location |
| `shipping_cost` | Numeric(10, 2) | Yes | NULL | Shipping cost |
| `delivery_days` | String(50) | Yes | NULL | Delivery days (e.g., "2-3 business days") |

## Owner Information

| Field Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `owner_id` | UUID | No | - | Owner/seller user ID (indexed) |

## Product Details

| Field Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `brand` | String(100) | Yes | NULL | Product brand |
| `model` | String(100) | Yes | NULL | Product model |
| `year` | Integer | Yes | NULL | Product year |
| `sku` | String(100) | Yes | NULL | SKU (unique) |
| `gender` | String(20) | Yes | NULL | Target gender |
| `product_type` | String(100) | Yes | NULL | Product type |
| `sub_category` | String(100) | Yes | NULL | Product sub-category |
| `designer` | String(100) | Yes | NULL | Product designer |
| `size` | String(50) | Yes | NULL | Product size |
| `colors` | JSON | Yes | NULL | Array of colors (JSON) |
| `product_style` | String(50) | Yes | NULL | Product style |

## Measurements

| Field Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `measurement_chest` | String(50) | Yes | NULL | Chest measurement |
| `measurement_sleeve_length` | String(50) | Yes | NULL | Sleeve length measurement |
| `measurement_length` | String(50) | Yes | NULL | Length measurement |
| `measurement_hem` | String(50) | Yes | NULL | Hem measurement |
| `measurement_shoulders` | String(50) | Yes | NULL | Shoulder measurement |

## Delivery Configuration

| Field Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `purchase_button_enabled` | Boolean | No | true | Whether purchase button is enabled |
| `delivery_method` | String(20) | Yes | NULL | Delivery method |
| `delivery_time` | String(20) | Yes | NULL | Delivery time |
| `delivery_fee` | Numeric(10, 2) | Yes | NULL | Delivery fee |
| `delivery_fee_type` | String(20) | Yes | NULL | Delivery fee type |
| `tracking_provided` | Boolean | No | false | Whether tracking is provided |
| `shipping_address` | String(255) | Yes | NULL | Shipping address |

## Ratings and Reviews

| Field Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `rating` | Float | No | 0.0 | Product rating |
| `review_count` | Integer | No | 0 | Number of reviews |

## Media and Content

| Field Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `images` | JSON | Yes | NULL | Array of image URLs (JSON) |
| `specifications` | JSON | Yes | NULL | Product specifications (JSON) |
| `key_features` | JSON | Yes | NULL | Array of key features (JSON) |
| `tags` | JSON | Yes | NULL | Array of tags (JSON) |

## Seller Policies

| Field Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `return_policy` | String(255) | Yes | "30-day return policy" | Return policy |
| `warranty_info` | String(255) | Yes | NULL | Warranty information |
| `packaging_info` | String(255) | Yes | "Secure packaging for safe delivery" | Packaging information |

## Search and Filtering

| Field Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `condition_badge` | String(50) | Yes | NULL | Condition badge (Like New, Excellent, Brand New) |

---

## Summary

- **Total Fields**: 54 fields (including 3 base fields)
- **Indexed Fields**: 
  - `id` (primary key)
  - `title`
  - `category`
  - `is_featured`
  - `is_verified`
  - `is_flagged`
  - `owner_id`
  - `sku` (unique)
  - `created_at`
  - `updated_at`

## Field Categories

1. **Base Fields** (3): id, created_at, updated_at
2. **Basic Information** (5): title, description, price, category, condition
3. **Deal Method** (5): deal_method, meetup_date, meetup_location, meetup_time, meetup_locations
4. **Product Status** (8): is_active, is_sold, is_featured, is_verified, is_flagged, verification_code, verification_expires_at, verification_attempts
5. **Stock Management** (2): stock_quantity, stock_status
6. **Location/Shipping** (3): location, shipping_cost, delivery_days
7. **Owner** (1): owner_id
8. **Product Details** (11): brand, model, year, sku, gender, product_type, sub_category, designer, size, colors, product_style
9. **Measurements** (5): measurement_chest, measurement_sleeve_length, measurement_length, measurement_hem, measurement_shoulders
10. **Delivery Configuration** (6): purchase_button_enabled, delivery_method, delivery_time, delivery_fee, delivery_fee_type, tracking_provided, shipping_address
11. **Ratings** (2): rating, review_count
12. **Media/Content** (4): images, specifications, key_features, tags
13. **Seller Policies** (3): return_policy, warranty_info, packaging_info
14. **Search/Filtering** (1): condition_badge

## JSON Fields

The following fields store JSON data:
- `colors` - Array of color strings
- `meetup_locations` - Array of meetup location objects
- `images` - Array of image URL strings
- `specifications` - Object with product specifications
- `key_features` - Array of key feature strings
- `tags` - Array of tag strings

