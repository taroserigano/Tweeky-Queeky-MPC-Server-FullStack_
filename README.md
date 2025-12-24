# FastAPI Backend for Tweeky Queeky Shop

A complete FastAPI rewrite of the Node.js/Express backend with identical functionality.

## Features

- ✅ **User Authentication**: JWT-based auth with HTTP-only cookies
- ✅ **Product Management**: Full CRUD with pagination, search, and reviews
- ✅ **Order Processing**: Cart, checkout, PayPal integration
- ✅ **Admin Panel**: User and product management
- ✅ **File Upload**: Image upload for products
- ✅ **MongoDB**: Async ODM with Beanie

## Tech Stack

- **FastAPI** - Modern async web framework
- **Beanie** - Async MongoDB ODM
- **Motor** - Async MongoDB driver
- **Pydantic** - Data validation
- **PyJWT** - JWT authentication
- **Passlib** - Password hashing
- **HTTPX** - Async HTTP client for PayPal

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the root directory:

```env
PORT=5000
MONGO_URI=mongodb://localhost:27017/tweekyqueeky
JWT_SECRET=your_jwt_secret_key_change_this_in_production
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_APP_SECRET=your_paypal_secret
PAYPAL_API_URL=https://api-m.sandbox.paypal.com
NODE_ENV=development
PAGINATION_LIMIT=12
```

## Running the Application

### With Docker (Recommended)

```bash
# Build and run with docker-compose
docker-compose up

# Or build and run in detached mode
docker-compose up -d

# Stop the container
docker-compose down

# Rebuild after code changes
docker-compose up --build
```

### Without Docker

```bash
# Development mode with auto-reload
uvicorn main:app --reload --port 5000

# Or using Python directly
python main.py
```

## Database Seeder

```bash
# Import sample data
python seeder.py

# Destroy all data
python seeder.py -d
```

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

## API Endpoints

### Users

- `POST /api/users/auth` - Authenticate user
- `POST /api/users` - Register user
- `POST /api/users/logout` - Logout user
- `GET /api/users/profile` - Get user profile (Protected)
- `PUT /api/users/profile` - Update profile (Protected)
- `GET /api/users` - Get all users (Admin)
- `DELETE /api/users/{id}` - Delete user (Admin)
- `GET /api/users/{id}` - Get user by ID (Admin)
- `PUT /api/users/{id}` - Update user (Admin)

### Products

- `GET /api/products` - Get all products (with pagination & search)
- `GET /api/products/{id}` - Get product by ID
- `POST /api/products` - Create product (Admin)
- `PUT /api/products/{id}` - Update product (Admin)
- `DELETE /api/products/{id}` - Delete product (Admin)
- `POST /api/products/{id}/reviews` - Create review (Protected)
- `GET /api/products/top/products` - Get top products

### Orders

- `POST /api/orders` - Create order (Protected)
- `GET /api/orders/myorders` - Get user orders (Protected)
- `GET /api/orders/{id}` - Get order by ID (Protected)
- `PUT /api/orders/{id}/pay` - Update order to paid (Protected)
- `PUT /api/orders/{id}/deliver` - Update to delivered (Admin)
- `GET /api/orders` - Get all orders (Admin)

### Upload

- `POST /api/upload` - Upload image

### Config

- `GET /api/config/paypal` - Get PayPal client ID

## Project Structure

```
backend_fastapi/
├── config/
│   ├── __init__.py
│   ├── database.py       # Database connection
│   └── settings.py       # Environment settings
├── middleware/
│   ├── __init__.py
│   └── auth.py          # JWT authentication
├── models/
│   ├── __init__.py
│   ├── user.py          # User model
│   ├── product.py       # Product & Review models
│   └── order.py         # Order model
├── routers/
│   ├── __init__.py
│   ├── users.py         # User routes
│   ├── products.py      # Product routes
│   ├── orders.py        # Order routes
│   └── upload.py        # File upload routes
├── schemas/
│   ├── __init__.py
│   ├── user.py          # User schemas
│   ├── product.py       # Product schemas
│   └── order.py         # Order schemas
├── utils/
│   ├── __init__.py
│   ├── generate_token.py # JWT utilities
│   ├── calc_prices.py    # Price calculation
│   └── paypal.py         # PayPal integration
├── main.py              # FastAPI app
├── seeder.py            # Database seeder
└── requirements.txt     # Dependencies
```

## Key Differences from Node.js Version

1. **Type Safety**: Full type hints with Pydantic
2. **Async/Await**: Native async throughout
3. **Auto Documentation**: Built-in Swagger/ReDoc
4. **Dependency Injection**: FastAPI's DI system instead of middleware chains
5. **Better Validation**: Pydantic models with automatic validation

## Default Admin Account

- **Email**: admin@email.com
- **Password**: 123456

## License

MIT
