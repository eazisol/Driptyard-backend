# Clean API Structure

This document outlines the cleaned up API structure after removing redundancies and organizing endpoints logically.

## Overview

The API is now organized into 3 main routers with clear separation of concerns:

1. **Authentication** (`/auth/*`) - User authentication and security
2. **Users** (`/users/*`) - User profile management
3. **Products** (`/products/*`) - Product CRUD operations with image uploads

---

## 🔐 Authentication Routes (`/auth/*`)

### Registration & Verification
- `POST /auth/register` - Register new user, sends verification email
- `POST /auth/verify-email` - Verify email with code, activates account
- `POST /auth/resend-verification` - Resend verification code

### Authentication
- `POST /auth/login` - Login with email/password, returns JWT token
- `POST /auth/logout` - Logout current user
- `POST /auth/refresh` - Refresh access token

### Password Reset
- `POST /auth/password-reset/request` - Request password reset (sends code via email)
- `POST /auth/password-reset/verify` - Verify reset code and update password

---

## 👤 Users Routes (`/users/*`)

### Profile Management
- `GET /users/me` - Get current user profile
- `PATCH /users/me` - Update profile (JSON only)
  - For simple text field updates
  - Content-Type: `application/json`
- `PUT /users/me` - Update profile with avatar upload
  - For updates including file uploads
  - Content-Type: `multipart/form-data`
  - Accepts: `username`, `first_name`, `last_name`, `phone`, `country_code`, `bio`, `avatar` (file)
  - Automatically uploads avatar to S3 and updates database

---

## 🛍️ Products Routes (`/products/*`)

### Product Listing
- `GET /products/featured` - Get featured products (paginated)
  - Query params: `page`, `page_size`
- `GET /products/recommended` - Get recommended products (paginated)
  - Query params: `page`, `page_size`
- `GET /products/` - List all products with filters (paginated)
  - Query params: `page`, `page_size`, `category`, `search`, `min_price`, `max_price`, `condition`
- `GET /products/{product_id}` - Get detailed product info

### Product Management (Authenticated)
- `POST /products/` - Create new product with images
  - Content-Type: `multipart/form-data`
  - Required: `title`, `description`, `price`, `category`, `condition`, `dealMethod`
  - Optional: `meetupDate`, `meetupLocation`, `meetupTime`, `images[]` (up to 10 files)
  - Automatically uploads images to S3
  - Sends listing verification code to seller email; listing stays inactive until verified
- `PUT /products/{product_id}` - Update product info (JSON only, no images)
  - Content-Type: `application/json`
- `POST /products/{product_id}/images` - Add/update product images
  - Content-Type: `multipart/form-data`
  - Accepts multiple image files (max 10 total per product)
  - Automatically uploads to S3 and updates product
- `POST /products/{product_id}/verification/send` - Send or resend listing verification code
- `POST /products/{product_id}/verification` - Verify listing with email code (activates listing)
- `DELETE /products/{product_id}` - Soft delete product (marks as inactive)

---

## 🔑 Key Improvements

### 1. **Removed Redundancy**
   - ❌ Deleted entire `/uploads/*` router
   - ❌ Removed duplicate `GET /me` from auth
   - ❌ Removed duplicate `PUT /profile` from auth
   - ❌ Removed duplicate `PATCH /me` from users

### 2. **Integrated File Uploads**
   - ✅ Avatar uploads integrated into `PUT /users/me`
   - ✅ Product images integrated into `POST /products/` (creation)
   - ✅ Separate endpoint `POST /products/{product_id}/images` for adding images to existing products

### 3. **Clear Separation of Concerns**
   - **Auth**: Only authentication/authorization operations
   - **Users**: Only profile management
   - **Products**: Complete product lifecycle including image management

### 4. **RESTful Design**
   - Proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
   - Resource-based URLs
   - Nested routes for sub-resources (e.g., `/products/{id}/images`)

### 5. **Simplified Architecture**
   - No scattered upload logic
   - Single source of truth for each operation
   - Easy to understand and maintain

---

## 📁 File Upload Strategy

All file uploads now happen within their respective resource routes:

### Avatar Uploads
- **Where**: `PUT /users/me`
- **S3 Folder**: `avatars/`
- **Max Files**: 1 per request
- **Auto-updates**: User's `avatar_url` field

### Product Images
- **Where**: 
  - `POST /products/` (during creation)
  - `POST /products/{product_id}/images` (add to existing)
- **S3 Folder**: `product_images/`
- **Max Files**: 10 per product total
- **Auto-updates**: Product's `images` array field

---

## 🚫 What Was Removed

### Deleted Files:
- `app/routes/uploads.py` - Entire redundant router

### Removed Endpoints:
- `POST /uploads/avatar` - Moved to `PUT /users/me`
- `POST /uploads/product-images` - Integrated into products router
- `DELETE /uploads/file` - Not needed (handle in respective resources)
- `GET /uploads/presigned-url` - Not needed for current use case
- `GET /auth/me` - Duplicate of `GET /users/me`
- `PUT /auth/profile` - Duplicate of user profile updates
- All empty placeholder order endpoints

### Cleaned Up:
- `app/routes/orders.py` - Removed placeholder endpoints, kept as TODO placeholder
- `app/main.py` - Removed orders router (not implemented yet)

---

## 🎯 Usage Examples

### Create Product with Images
```bash
curl -X POST "http://localhost:8000/products/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=Vintage Jacket" \
  -F "description=Barely used vintage jacket" \
  -F "price=49.99" \
  -F "category=Fashion" \
  -F "condition=Like New" \
  -F "dealMethod=Meet Up" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg"
```

### Update User Avatar
```bash
curl -X PUT "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "first_name=John" \
  -F "last_name=Doe" \
  -F "avatar=@profile.jpg"
```

### Add Images to Existing Product
```bash
curl -X POST "http://localhost:8000/products/123e4567-e89b-12d3-a456-426614174000/images" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "images=@image3.jpg" \
  -F "images=@image4.jpg"
```

---

## ✅ Result

- **3 clean routers** instead of 5 messy ones
- **No redundancy** - each operation has one clear endpoint
- **Integrated uploads** - no separate upload router needed
- **RESTful** - follows REST best practices
- **Maintainable** - easy to understand and extend

