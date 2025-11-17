# API Structure Documentation

This document outlines the API structure with service layer architecture and organized endpoints.

## Overview

The API is organized into 4 main routers with clear separation of concerns:

1. **Authentication** (`/auth/*`) - User authentication and security
2. **Users** (`/users/*`) - User profile management
3. **Products** (`/products/*`) - Product CRUD operations with image uploads
4. **Admin** (`/admin/*`) - Admin-only platform management

## Architecture

### Service Layer Pattern

The application follows a **service layer architecture** where:
- **Routes** (`app/routes/*`) - Handle HTTP concerns (request/response, validation, error handling)
- **Services** (`app/services/*`) - Contain all business logic (database operations, validations, transformations)
- **Models** (`app/models/*`) - Database models
- **Schemas** (`app/schemas/*`) - Request/response validation schemas

This separation ensures:
- ✅ Business logic is reusable and testable
- ✅ Routes remain thin and focused on HTTP concerns
- ✅ Easy to maintain and extend
- ✅ Clear separation of concerns

### Service Files

- `app/services/auth.py` - Authentication business logic
- `app/services/user.py` - User profile management logic
- `app/services/product.py` - Product management logic
- `app/services/email.py` - Email sending functionality
- `app/services/s3.py` - AWS S3 file upload operations

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
  - Requires authentication
  - Returns: UserResponse with all user information
- `PUT /users/me` - Update profile (JSON only)
  - Content-Type: `application/json`
  - Accepts: `username`, `first_name`, `last_name`, `phone`, `country_code`, `bio`
  - Validates username uniqueness and format
- `POST /users/me/avatar` - Upload user avatar image
  - Content-Type: `multipart/form-data`
  - Accepts: `avatar` (file)
  - Supported formats: JPG, JPEG, PNG, GIF, WEBP
  - Automatically uploads to S3 and updates `avatar_url`

---

## 🛍️ Products Routes (`/products/*`)

### Product Listing
- `GET /products/featured` - Get featured products (paginated)
  - Query params: `page`, `page_size`
- `GET /products/recommended` - Get recommended products (paginated)
  - Query params: `page`, `page_size`
- `GET /products/my-listings` - List products created by the authenticated user (paginated)
  - Requires authentication
  - Query params: `page`, `page_size`, `status` (`active`, `inactive`, `sold`, `verification_pending`), `search`
- `GET /products/` - List all products with filters (paginated)
  - Query params: `page`, `page_size`, `category`, `search`, `min_price`, `max_price`, `condition`
- `GET /products/{product_id}` - Get detailed product info

### Product Management (Authenticated)
- `POST /products/` - Create new product with images
  - Content-Type: `multipart/form-data`
  - Required: `title`, `description`, `price`, `category`, `condition`, `dealMethod`, `productType`, `designer`, `productStyle`, `colors`
  - Optional: `meetupDate`, `meetupLocation`, `meetupTime`, `meetupLocations`, `images[]` (minimum 4, maximum 10 files)
  - Automatically uploads images to S3
  - Sends listing verification code to seller email; listing stays inactive until verified
- `PUT /products/{product_id}` - Update product info (JSON only, no images)
  - Content-Type: `application/json`
  - Only product owner can update
- `POST /products/{product_id}/images` - Add/update product images
  - Content-Type: `multipart/form-data`
  - Accepts multiple image files (max 10 total per product)
  - Automatically uploads to S3 and updates product
- `POST /products/{product_id}/verification/send` - Send or resend listing verification code
- `POST /products/{product_id}/verification` - Verify listing with email code (activates listing)
- `DELETE /products/{product_id}` - Soft delete product (marks as inactive)
  - Only product owner can delete

---

## 👨‍💼 Admin Routes (`/admin/*`)

### Dashboard & Statistics
- `GET /admin/stats/overview` - Get platform statistics overview
  - Requires admin authentication
  - Returns: User counts, product counts, sales data, etc.

### Product Management
- `GET /admin/products` - List all products with admin filters (paginated)
  - Query params: `page`, `page_size`, `status`, `search`, `category`, `is_verified`, `is_flagged`
- `GET /admin/products/{product_id}` - Get product details (admin view)
- `PUT /admin/products/{product_id}` - Update product (admin override)
- `DELETE /admin/products/{product_id}` - Delete product (hard delete)

### User Management
- `GET /admin/users` - List all users with admin filters (paginated)
  - Query params: `page`, `page_size`, `search`, `is_active`, `is_verified`, `is_admin`
- `GET /admin/users/{user_id}` - Get user details (admin view)
- `PUT /admin/users/{user_id}` - Update user (admin override)
- `DELETE /admin/users/{user_id}` - Deactivate user account

---

## 🔑 Key Architecture Features

### 1. **Service Layer Pattern**
   - ✅ All business logic in service classes
   - ✅ Routes are thin wrappers around service methods
   - ✅ Services are reusable and testable
   - ✅ Clear separation between HTTP and business logic

### 2. **RESTful Design**
   - Proper HTTP methods (GET, POST, PUT, DELETE)
   - Resource-based URLs
   - Nested routes for sub-resources (e.g., `/products/{id}/images`)
   - Consistent response formats

### 3. **File Upload Strategy**
   - Avatar uploads: `POST /users/me/avatar`
   - Product images: `POST /products/` (creation) or `POST /products/{id}/images` (add to existing)
   - All uploads go to AWS S3
   - Automatic URL storage in database

### 4. **Authentication & Authorization**
   - JWT-based authentication
   - Role-based access control (admin routes)
   - Owner-based access control (product/user updates)

### 5. **Product Verification System**
   - Products created inactive
   - Verification code sent via email
   - Products activated after verification
   - Prevents spam and ensures valid listings

---

## 📁 File Upload Details

### Avatar Uploads
- **Endpoint**: `POST /users/me/avatar`
- **S3 Folder**: `avatars/`
- **Max Files**: 1 per request
- **Supported Formats**: JPG, JPEG, PNG, GIF, WEBP
- **Auto-updates**: User's `avatar_url` field

### Product Images
- **Endpoints**: 
  - `POST /products/` (during creation, minimum 4 images)
  - `POST /products/{product_id}/images` (add to existing)
- **S3 Folder**: `product_images/`
- **Max Files**: 10 per product total
- **Min Files**: 4 required for new products
- **Auto-updates**: Product's `images` array field

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
  -F "productType=Tops" \
  -F "designer=Nike" \
  -F "productStyle=Casual" \
  -F "colors=[\"Black\", \"White\"]" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  -F "images=@image3.jpg" \
  -F "images=@image4.jpg"
```

### Update User Profile
```bash
curl -X PUT "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "bio": "Fashion enthusiast"
  }'
```

### Upload User Avatar
```bash
curl -X POST "http://localhost:8000/users/me/avatar" \
  -H "Authorization: Bearer YOUR_TOKEN" \
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

## 📂 Project Structure

```
app/
├── routes/           # HTTP route handlers (thin wrappers)
│   ├── auth.py      # Authentication endpoints
│   ├── users.py     # User profile endpoints
│   ├── products.py  # Product management endpoints
│   └── admin.py     # Admin management endpoints
├── services/         # Business logic layer
│   ├── auth.py      # Authentication business logic
│   ├── user.py      # User profile business logic
│   ├── product.py   # Product management business logic
│   ├── email.py     # Email sending service
│   └── s3.py        # AWS S3 upload service
├── models/          # Database models
│   ├── user.py
│   ├── product.py
│   └── ...
├── schemas/         # Pydantic request/response schemas
│   ├── auth.py
│   ├── user.py
│   ├── product.py
│   └── ...
└── main.py          # FastAPI application setup
```

---

## ✅ Architecture Benefits

- **Maintainable** - Clear separation of concerns
- **Testable** - Business logic isolated in services
- **Scalable** - Easy to add new features
- **RESTful** - Follows REST best practices
- **Type-safe** - Pydantic schemas for validation
- **Secure** - JWT authentication, role-based access control
