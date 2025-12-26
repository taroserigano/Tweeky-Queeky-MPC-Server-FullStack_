# 🛒 TweekySqueeky E-Commerce Platform

A modern, full-stack e-commerce application built with **FastAPI**, **React**, and **MongoDB**. Features secure payment processing, user authentication, and a responsive admin dashboard.

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![MongoDB](https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

## ✨ Features

### User Features

- 🔐 **Secure Authentication** - JWT-based auth with HTTP-only cookies
- 🛍️ **Product Browsing** - Search, filter, and pagination
- ⭐ **Product Reviews** - Rate and review products
- 🛒 **Shopping Cart** - Add/remove items, calculate totals
- 💳 **PayPal Integration** - Secure payment processing
- 📦 **Order Tracking** - View order history and status

### Admin Features

- 👥 **User Management** - View and manage users
- 📝 **Product Management** - CRUD operations for products
- 📊 **Order Management** - Process and track orders
- 🖼️ **Image Upload** - Product image management

## 🏗️ Tech Stack

### Backend

- **FastAPI** - Modern, high-performance Python web framework
- **Beanie ODM** - Async MongoDB object-document mapper
- **Pydantic v2** - Data validation and settings management
- **PyJWT** - JSON Web Token implementation
- **Passlib** - Secure password hashing

### Frontend

- **React 18** - Modern UI library
- **Redux Toolkit** - State management
- **React Bootstrap** - Responsive UI components
- **React Router v6** - Client-side routing

### Database & Infrastructure

- **MongoDB 7.0** - NoSQL database
- **Docker & Docker Compose** - Containerization
- **Nginx** - Reverse proxy and static file serving

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Run with Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd TweekySqueeky-FastAPI-Ecommer-App

# Create environment file
cp .env.example .env
# Edit .env with your credentials

# Start all services (Frontend, Backend, MongoDB)
docker-compose up -d --build

# Seed database with sample data
docker exec tweeky-queeky-fastapi python seeder.py

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000
# API Docs: http://localhost:5000/docs
```

### Local Development

```bash
# Backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 5000

# Frontend (separate terminal)
cd frontend
npm install
npm start
```

## 📁 Project Structure

```
├── config/              # Configuration and database setup
├── middleware/          # Authentication middleware
├── models/             # MongoDB models (User, Product, Order)
├── routers/            # API route handlers
├── schemas/            # Pydantic schemas for validation
├── utils/              # Utility functions (JWT, PayPal, etc.)
├── tests/              # Comprehensive test suite
├── frontend/           # React application
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── screens/    # Page components
│   │   └── slices/     # Redux slices
│   ├── Dockerfile      # Frontend container config
│   └── nginx.conf      # Nginx configuration
├── main.py             # FastAPI application entry point
├── docker-compose.yml  # Multi-container orchestration
└── requirements.txt    # Python dependencies
```

## 🔧 Configuration

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

### 🔄 Switching Between MongoDB Local (Docker) and Atlas (Cloud)

The application supports both local MongoDB (Docker) and MongoDB Atlas (cloud) databases. Switching between them is straightforward:

**Using Local MongoDB (Docker)** - Default setup when running with docker-compose:

```env
# In docker-compose.yml (already configured)
MONGO_URI=mongodb://admin:adminpassword@mongodb:27017/tweeky?authSource=admin
```

**Using MongoDB Atlas (Cloud)**:

```env
# In .env file or docker-compose.yml
MONGO_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/tweeky?retryWrites=true&w=majority
```

After changing the `MONGO_URI`:

```bash
# Restart the backend service
docker-compose restart fastapi-backend

# Or restart all services
docker-compose down && docker-compose up -d
```

**Benefits of Each:**

- **Local (Docker)**: No internet required, faster development, free, full control
- **Atlas (Cloud)**: Managed service, automatic backups, scalable, accessible anywhere

## 📡 API Documentation

Once the server is running:

- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

### Key Endpoints

**Authentication**

- `POST /api/users/auth` - Login
- `POST /api/users` - Register
- `POST /api/users/logout` - Logout

**Products**

- `GET /api/products` - List products (pagination, search)
- `GET /api/products/{id}` - Get product details
- `GET /api/products/top` - Top rated products
- `POST /api/products/{id}/reviews` - Add review

**Orders**

- `POST /api/orders` - Create order
- `GET /api/orders/mine` - User's orders
- `GET /api/orders/{id}` - Order details
- `PUT /api/orders/{id}/pay` - Process payment

**Admin**

- `GET /api/users` - Manage users
- `PUT /api/orders/{id}/deliver` - Mark delivered
- Full CRUD for products

## 🧪 Testing

Comprehensive test suite with 35 automated tests covering all critical flows:

```bash
# Run all tests
python tests/test_comprehensive_e2e.py    # 13 E2E tests
python tests/test_integration.py          # 17 integration tests
python tests/test_payment_stress.py       # 5 stress tests

# Test results: 34/35 passed (97.1%)
```

**Test Coverage:**

- ✅ User authentication and authorization
- ✅ Product CRUD operations
- ✅ Order creation and management
- ✅ Payment processing (PayPal)
- ✅ Admin functions
- ✅ Edge cases and error handling

## 🐳 Docker Deployment

The application is fully containerized:

```yaml
Services:
  - frontend (React + Nginx) → Port 3000
  - fastapi-backend → Port 5000
  - mongodb → Port 27017
```

**Access Points:**

- **Application**: http://localhost:3000
- **API**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs

## 🔒 Security Features

- JWT tokens in HTTP-only cookies
- Password hashing with bcrypt
- CORS configuration
- Input validation with Pydantic
- SQL injection prevention (NoSQL)
- Secure payment processing

## 📈 Performance

- **Async/await** throughout for high concurrency
- **MongoDB indexes** for fast queries
- **Docker optimization** with multi-stage builds
- **Nginx caching** for static assets
- **Connection pooling** for database

## 🛠️ Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload

# Format code
black .

# Lint code
ruff check .
```

## 📝 Database Schema

**Users**

- Email, password (hashed), name, admin flag

**Products**

- Name, image, brand, category, description
- Price, stock count, rating

**Orders**

- User reference, order items, shipping address
- Payment method, prices, status flags

## 🎯 Future Enhancements

- [ ] Add product categories filtering
- [ ] Implement wishlist feature
- [ ] Add email notifications
- [ ] Integrate additional payment methods
- [ ] Add product recommendations
- [ ] Implement advanced search filters

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

Built with ❤️ using FastAPI, React, and MongoDB

---

**Note**: This is a portfolio/demonstration project. For production use, ensure you:

- Use strong JWT secrets
- Enable HTTPS
- Use production PayPal credentials
- Implement rate limiting
- Add comprehensive logging
- Set up monitoring and alerts
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
