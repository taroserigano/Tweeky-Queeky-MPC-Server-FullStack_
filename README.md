# 🤖 Tweeky-Queeky Shop: Agentic AI E-Commerce Portfolio

> **Portfolio project focused on agentic AI patterns (tool-use via MCP + retrieval via RAG) wrapped inside a real e-commerce app (FastAPI + React).**

This repo is intentionally **agent-first**:
- The React frontend talks to an **Agent Gateway** (one `/chat` surface)
- The agent **routes intent** to either an **MCP tool server** (products/orders) or a **RAG service** (policy/docs)
- The tool layer stays **hidden from the UI**, making the boundary clean, testable, and production-shaped

You can also run the full e-commerce backend (auth/products/orders/payments) alongside the agentic stack.

## 🔥 Key Technologies (Agentic, Up Front)

- **Agent Gateway (FastAPI):** orchestrates requests and routes to tools vs retrieval
- **MCP Tool Server:** product search + product lookup + order tracking tools (HTTP tools API)
- **RAG Service:** local markdown doc retrieval (TF‑IDF) for policy/support Q&A
- **Frontend:** React 18 (chat UI at `/ai`), Redux Toolkit / RTK Query
- **Full E‑Commerce API (optional mode):** FastAPI + MongoDB (Beanie), JWT cookies, uploads, PayPal/Stripe config
- **Search (optional mode):** hybrid search (BM25 + embeddings) with OpenAI + Pinecone configuration
- **Infra:** Docker / Compose (full-stack), plus simple local scripts for the 3-service agent architecture

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![Redux](https://img.shields.io/badge/redux-%23593d88.svg?style=for-the-badge&logo=redux&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens)

</div>

---

## 🎯 Project Highlights

- ✅ **Agentic Architecture (MCP + RAG + Agent Gateway)** - UI calls one agent endpoint; tools/retrieval are internal services
- ✅ **Tool-Use Boundary (MCP)** - Product/order capabilities exposed as explicit tools (easy to audit + test)
- ✅ **Retrieval Boundary (RAG)** - Policy/support answers come from local docs (no vendor lock-in for the demo)
- ✅ **Modern Full-Stack Backbone** - FastAPI + React 18 foundation with auth, products, orders, uploads, admin UX
- ✅ **Two Run Modes** - Local “agent demo” (no keys) or full e-commerce stack (Mongo/payments/hybrid search)

## 🧠 Agentic Architecture (The Point of This Repo)

```
Frontend (React :3000)
  ↓  (only calls /chat)
Agent Gateway (FastAPI :7000)
  ├─ MCP Tool Server (FastAPI :7001)   → products / orders tools
  └─ RAG Service (FastAPI :7002)       → doc retrieval (TF‑IDF)
```

### What the agent actually does

- **Intent routing**: “track order …” → MCP tool; “return policy” → RAG
- **Tool execution**: calls tools like `searchProducts` / `getProduct` / `getOrderStatus`
- **UI isolation**: frontend never calls MCP/RAG directly (clean separation)

## 🚀 Quickstart (Agentic Demo: Local, No API Keys)

### 1) Start the 3 services

Windows:
- Run `run_all.bat`

Or run individually:
- `cd services/mcp_server && python main.py` (7001)
- `cd services/rag_service && python main.py` (7002)
- `cd services/agent_gateway && python main.py` (7000)

### 2) Start the frontend

- `cd frontend && npm install`
- `npm start`

Visit `http://localhost:3000/ai`

### Example prompts to try

- “Show me headphones under $300” (MCP)
- “Track order ORD-1001” (MCP)
- “What’s your return policy?” (RAG)

## 🏃 Run Mode: Full E‑Commerce Stack (Optional)

If you want the full storefront API (auth/products/orders/payments) in addition to the agentic demo:

- Backend API: `python -m uvicorn main:app --reload --port 5000`
- Frontend: `npm start` (same as above)

Docker (full-stack) is available via `docker-compose.yml` (MongoDB + backend + frontend). This mode can be configured with Mongo/OpenAI/Pinecone env vars.

## ✨ Features

### Agentic AI Features (Primary)

- 🧭 **Agent Gateway** - single `/chat` surface the frontend calls
- 🧰 **MCP Tools** - product search + product lookup + order status tools
- 📚 **RAG Service** - doc retrieval for support/policy questions
- 🧪 **Inspectable Debugging** - health endpoints and tool routing visibility during development

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

## 🏗️ Tech Stack & Architecture

### 🐍 Backend (FastAPI - Python 3.11+)

| Technology           | Purpose             | Why This Choice                                                            |
| -------------------- | ------------------- | -------------------------------------------------------------------------- |
| **FastAPI 0.115.0**  | REST API Framework  | ⚡ Async/await native, auto-generated OpenAPI docs                         |
| **Beanie ODM**       | MongoDB Integration | 🔄 Async MongoDB operations, Pydantic integration, relationship management |
| **Pydantic v2**      | Data Validation     | 🛡️ Type-safe validation and serialization                                  |
| **PyJWT**            | Authentication      | 🔐 JWT token generation/verification with HTTP-only cookie security        |
| **Passlib + Bcrypt** | Password Security   | 🔒 Industry-standard password hashing with salt rounds                     |
| **Uvicorn**          | ASGI Server         | 🚀 High-performance async server for production deployments                |

**Key Backend Features:**

- ✅ **100% Type-Hinted** - Full type safety with mypy compatibility
- ✅ **Async/Await Throughout** - Non-blocking I/O for high concurrency
- ✅ **Dependency Injection** - FastAPI's powerful DI system for clean, testable code
- ✅ **Auto-Generated Docs** - Interactive Swagger UI & ReDoc at `/docs` and `/redoc`
- ✅ **Pydantic V2 Models** - Request/response validation with detailed error messages

### ⚛️ Frontend (React 18 + Modern JS Ecosystem)

> **🎨 Enterprise-Grade React Application with Advanced State Management & Real-Time Features**

| Technology            | Version | Purpose                 | Why This Choice                                                              |
| --------------------- | ------- | ----------------------- | ---------------------------------------------------------------------------- |
| **React 18.2**        | 18.2.0  | UI Framework            | ⚡ Concurrent rendering, automatic batching, Suspense, improved performance  |
| **Redux Toolkit**     | 2.0+    | State Management        | 🎯 Modern Redux with 70% less boilerplate, built-in Immer for immutability   |
| **RTK Query**         | 2.0+    | Data Fetching & Caching | 🔄 Auto-caching, invalidation, polling, optimistic updates, tag-based system |
| **React Router v6**   | 6.20+   | Client-Side Routing     | 🛣️ Data loaders, nested routes, lazy loading, protected route patterns       |
| **React Bootstrap 5** | 2.9+    | UI Component Library    | 🎨 Production-ready components, responsive grid, customizable theming        |
| **Axios**             | 1.6+    | HTTP Client             | 📡 Request/response interceptors, CSRF protection, credential handling       |
| **React Icons**       | 5.0+    | Icon Library            | 🎭 Font Awesome integration, tree-shakeable imports                          |
| **React Toastify**    | 9.1+    | Notification System     | 🔔 Non-intrusive toast notifications with animations                         |

**🎯 Advanced React Patterns & Practices:**

- ✅ **Custom API Hooks** - Domain hooks for API access (orders/products/users)
- ✅ **Redux Toolkit Slices** - Modular state with `createSlice`, `createAsyncThunk`, `createEntityAdapter`
- ✅ **RTK Query Integration** - API slice with automatic cache management and tag invalidation
- ✅ **Component Composition** - HOCs, render props, and compound components for reusability
- ✅ **Code Splitting** - React.lazy() and Suspense for optimized bundle sizes
- ✅ **Protected Routes** - Custom `<AdminRoute>` and `<PrivateRoute>` components with role-based access
- ✅ **Error Boundaries** - Graceful error handling with fallback UI
- ✅ **Performance Optimization** - useMemo, useCallback, React.memo for render optimization

**🔥 React Features & UI/UX:**

- ✅ **Responsive Design** - Mobile-first CSS, Bootstrap grid system, 100% responsive on all devices
- ✅ **LocalStorage Persistence** - Cart state persists across browser sessions
- ✅ **Optimistic UI Updates** - Instant feedback with automatic rollback on API errors
- ✅ **Loading States** - Skeleton screens, spinners, and progressive loading indicators
- ✅ **Form Validation** - Real-time validation with custom hooks and error display
- ✅ **Infinite Scroll** - Pagination with load-more functionality for product listings
- ✅ **Search Debouncing** - Optimized search with 300ms debounce to reduce API calls
- ✅ **Image Lazy Loading** - Native lazy loading for product images (performance boost)
- ✅ **Checkout Flow** - Multi-step checkout with progress indicators and validation
- ✅ **Order Tracking** - Real-time order status updates with timeline visualization

### 🗄️ Database & Infrastructure

| Technology            | Purpose            | Why This Choice                                                         |
| --------------------- | ------------------ | ----------------------------------------------------------------------- |
| **MongoDB Atlas 7.0** | NoSQL Database     | 📊 Document-based storage, horizontal scaling, cloud-managed            |
| **Docker 24.0**       | Containerization   | 📦 Consistent environments, easy deployment, microservices architecture |
| **Docker Compose**    | Orchestration      | 🎼 Multi-container management, service dependencies, networking         |
| **Nginx**             | Reverse Proxy      | 🌐 Static file serving, load balancing, SSL termination                 |
| **PayPal SDK**        | Payment Processing | 💳 Secure transactions, sandbox testing, order management               |

**Architecture Highlights:**

- ✅ **Multi-Container Architecture** - Separate containers for frontend, backend, and database
- ✅ **Cloud-Ready** - MongoDB Atlas for scalable, managed database hosting
- ✅ **Production Optimized** - Multi-stage Docker builds, minimized image sizes
- ✅ **Environment Isolation** - Docker networking, volume persistence, secret management

---

## 🔥 Advanced Features

### Backend Capabilities

- **Beanie Link Relationships** - Proper document references with automatic population
- **Async MongoDB Queries** - Non-blocking database operations with connection pooling
- **Pagination & Filtering** - Efficient query optimization with index support
- **Image Upload System** - File handling with validation and storage management
- **PayPal Webhook Integration** - Real-time payment status updates

### Frontend Capabilities

- **🛒 Advanced Shopping Cart** - Redux Toolkit state + LocalStorage persistence with sync mechanisms
- **📦 Real-Time Order Tracking** - Live order status updates with timeline component and status badges
- **⭐ Product Review System** - Star ratings, user reviews with optimistic UI updates and validation
- **🔍 Smart Search** - Debounced search with real-time filtering, keyword highlighting, and suggestions
- **📱 Responsive Dashboard** - Mobile-optimized admin panel with responsive tables and infinite scroll
- **🎨 Custom API Hooks** - Centralized React Query hooks in `frontend/src/hooks/`
- **🚀 Performance Optimized** - Code splitting, lazy loading, memoization, and bundle optimization
- **♿ Accessibility (A11y)** - ARIA labels, keyboard navigation, screen reader support, semantic HTML
- **🎭 Advanced UI Components**:
  - **CheckoutSteps** - Multi-step form with progress indicators
  - **Rating Component** - Interactive star rating with half-star support
  - **FormContainer** - Reusable form wrapper with validation states
  - **Product Carousel** - Touch-enabled image slider with thumbnails
  - **AdminRoute/PrivateRoute** - Role-based route guards with redirect logic
  - **SearchBox** - Auto-complete search with keyboard shortcuts (Cmd/Ctrl+K)
  - **Paginate** - Custom pagination with page number inputs and jump-to-page
  - **Message & Loader** - Consistent loading and error message components

---

## ⚛️ React Architecture Deep Dive

### 🎯 State Management Strategy

**Redux Toolkit + RTK Query Architecture:**

```
frontend/src/
├── store.js                    # Redux store configuration with RTK Query
├── slices/
│   ├── authSlice.js           # User authentication state
│   ├── cartSlice.js           # Shopping cart state + localStorage sync
│   ├── productsApiSlice.js    # RTK Query endpoints for products
│   ├── usersApiSlice.js       # RTK Query endpoints for users
│   └── ordersApiSlice.js      # RTK Query endpoints for orders
```

**Key State Management Patterns:**

1. **Redux Toolkit Slices** - Using `createSlice` for cleaner reducer logic
2. **RTK Query API Slices** - Automatic caching, invalidation, and refetching
3. **LocalStorage Middleware** - Cart persistence across sessions
4. **Optimistic Updates** - Instant UI feedback with automatic rollback
5. **Tag-Based Invalidation** - Smart cache invalidation on mutations

### 🧩 Component Architecture

**Atomic Design Pattern Implementation:**

```
frontend/src/components/
├── Header.jsx              # Navigation with cart badge, user dropdown
├── Footer.jsx              # Reusable footer component
├── Rating.jsx              # Star rating display (atoms)
├── Product.jsx             # Product card (molecules)
├── CheckoutSteps.jsx       # Stepper component (molecules)
├── AdminRoute.jsx          # HOC for admin-only routes
├── PrivateRoute.jsx        # HOC for authenticated routes
├── SearchBox.jsx           # Search with debouncing
├── Paginate.jsx            # Pagination controls
├── FormContainer.jsx       # Form layout wrapper
├── Message.jsx             # Alert/error messages
└── Loader.jsx              # Loading spinner
```

**Screen/Page Components:**

```
frontend/src/screens/
├── HomeScreen.jsx          # Product listing with search & pagination
├── ProductScreen.jsx       # Product details + reviews
├── CartScreen.jsx          # Shopping cart management
├── LoginScreen.jsx         # User authentication
├── RegisterScreen.jsx      # User registration
├── ShippingScreen.jsx      # Checkout step 1: Address
├── PaymentScreen.jsx       # Checkout step 2: Payment method
├── PlaceOrderScreen.jsx    # Checkout step 3: Order review
├── OrderScreen.jsx         # Order details + PayPal integration
├── ProfileScreen.jsx       # User profile + order history
├── admin/
│   ├── OrderListScreen.jsx    # Admin: Manage orders
│   ├── ProductListScreen.jsx  # Admin: Manage products
│   ├── ProductEditScreen.jsx  # Admin: Edit product
│   └── UserListScreen.jsx     # Admin: Manage users
```

### 🔗 Custom Hooks Library

**Reusable Business Logic:**

These hooks are implemented in `frontend/src/hooks/` and re-exported from `frontend/src/hooks/index.js`.

- **Orders**: `useCreateOrder`, `useOrderDetails`, `usePayOrder`, `usePayPalClientId`, `useMyOrders`, `useOrders`, `useDeliverOrder`
- **Products**: `useProducts`, `useProductDetails`, `useTopProducts`, `useCreateReview`, `useCreateProduct`, `useUpdateProduct`, `useDeleteProduct`, `useUploadProductImage`
- **Users**: `useLogin`, `useRegister`, `useLogout`, `useUpdateProfile`, `useUsers`, `useUserDetails`, `useDeleteUser`, `useUpdateUser`

### 🎨 Styling & Theming

- **Bootstrap 5** - Grid system, utilities, components
- **Custom CSS Modules** - Component-scoped styles
- **CSS Variables** - Theme customization (colors, spacing)
- **Responsive Breakpoints** - Mobile (< 576px), Tablet (768px), Desktop (992px+)

### 🚀 Performance Optimizations

1. **Code Splitting** - React.lazy() for route-based splitting
2. **Memoization** - React.memo, useMemo, useCallback for expensive operations
3. **Image Optimization** - Lazy loading, WebP format, responsive images
4. **Bundle Size** - Tree shaking, dynamic imports, minimize dependencies
5. **Debouncing** - Search input, window resize, scroll events
6. **Virtual Scrolling** - For large product lists (future enhancement)

---

## 🚀 Quick Start

> 📘 **Ports (current defaults):**
>
> - **Docker:** Frontend `3000`, Backend `5000`
> - **Local dev via `start.py`:** Frontend `3000`, Backend `5003`

### 🐳 Docker Deployment (Recommended for Production)

**One-Command Setup:**

```bash
# Clone the repository
git clone https://github.com/taroserigano/Tweeky-Queeky-Shop-Mern-Dockerized_Master-PY.git
cd Tweeky-Queeky-Shop-Mern-Dockerized_Master-PY

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your MongoDB Atlas URI, JWT secret, and PayPal credentials

# Start all services (Frontend + Backend + Database)
docker-compose up -d --build

# Seed database with sample products and users
docker exec tweeky-queeky-fastapi python seeder.py

# 🎉 Application is now running!
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000
# API Docs: http://localhost:5000/docs (Swagger UI)
# API Docs: http://localhost:5000/redoc (ReDoc)
```

**Default Admin Credentials:**

- Email: `admin@email.com`
- Password: `123456`

### 💻 Local Development Setup

**Backend (Python/FastAPI):**

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start full stack (recommended for local dev)
python start.py

# Frontend: http://localhost:3000
# Backend API: http://localhost:5003
# API Docs: http://localhost:5003/docs

# Or run only the backend:
uvicorn main:app --reload --port 5003 --host 127.0.0.1
```

### 🤖 MCP Server (Agentic AI Tools)

The MCP server exposes safe tools that AI assistants can use to browse, analyze, and assist with shopping.

It reads `MONGO_URI` and `OPEN_AI` (OpenAI API key) from your environment.

```bash
# Run the MCP server (stdio)
python -m mcp_server.server
```

**Catalog & Search Tools:**

| Tool                  | Description                                        |
| --------------------- | -------------------------------------------------- |
| `list_products`       | List products with optional category/price filters |
| `search_products`     | Search by name, brand, or category                 |
| `get_product`         | Get full product details by ID                     |
| `get_top_products`    | Get top-rated products                             |
| `get_product_reviews` | Get reviews for a product                          |
| `catalog_stats`       | Total products, reviews, category counts           |

**Catalog Intelligence Tools:**

| Tool                        | Description                                  |
| --------------------------- | -------------------------------------------- |
| `low_stock_report`          | Products at or below stock threshold         |
| `price_outliers`            | Products with unusual prices vs category avg |
| `category_price_summary`    | Min/max/avg price per category               |
| `reviews_sentiment_summary` | Positive/neutral/negative review counts      |
| `inventory_value`           | Total inventory value by category            |

**Shopping Assistant Tools (AI-powered):**

| Tool                      | Description                                      |
| ------------------------- | ------------------------------------------------ |
| `recommend_products`      | AI recommendations based on preferences + budget |
| `compare_products`        | Side-by-side product comparison                  |
| `build_cart_suggestion`   | AI builds a cart for a goal within budget        |
| `explain_product`         | AI-generated product summary                     |
| `answer_product_question` | AI answers customer questions about a product    |

**Admin Ops Tools (with Audit Logging & Dry-Run):**

| Tool                      | Description                                   |
| ------------------------- | --------------------------------------------- |
| `list_admins`             | List admin users for authentication reference |
| `update_stock`            | Update product stock (dry-run supported)      |
| `update_product_price`    | Update product price (dry-run supported)      |
| `flag_review`             | Flag a review for moderation                  |
| `bulk_update_stock`       | Batch update stock for multiple products      |
| `mark_order_delivered`    | Mark an order as delivered                    |
| `get_audit_log`           | Retrieve audit log entries with filters       |
| `admin_dashboard_summary` | Quick admin metrics dashboard                 |

> **💡 Safe Agentic AI Pattern:** All admin tools require `admin_email` for authentication and support `dry_run=True` mode to preview changes without applying them. Every action is logged to the `AuditLog` collection for accountability.

**Frontend (React):**

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Frontend running at http://localhost:3000
```

### 🔄 Switching Between Local and Docker

For day-to-day development, use `python start.py` (frontend `3000`, backend `5003`). For containerized runs, use Docker Compose (frontend `3000`, backend `5000`).

**From Local to Docker:**

```bash
# Stop local servers (Ctrl+C in both terminals)
# Then start Docker
docker-compose up -d
```

**From Docker to Local:**

```bash
# Stop Docker containers
docker-compose down

# Start local servers
# Recommended:
#   python start.py
# Or (2 terminals):
#   Terminal 1: uvicorn main:app --reload --port 5003 --host 127.0.0.1
#   Terminal 2: cd frontend && npm start
```

Access: http://localhost:3000 (works the same in both environments)

### 📋 Prerequisites

| Requirement               | Version   | Purpose                       |
| ------------------------- | --------- | ----------------------------- |
| **Docker**                | 24.0+     | Container runtime             |
| **Docker Compose**        | 2.0+      | Multi-container orchestration |
| **Python**                | 3.11+     | Backend development           |
| **Node.js**               | 18+       | Frontend development          |
| **MongoDB Atlas Account** | Free Tier | Cloud database hosting        |

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

- **Docker (default)**:
  - Swagger UI: http://localhost:5000/docs
  - ReDoc: http://localhost:5000/redoc
- **Local dev via `start.py`**:
  - Swagger UI: http://localhost:5003/docs
  - ReDoc: http://localhost:5003/redoc

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

---

<div align="center">

**🌟 Star this repo if you found it helpful!**

**Made with FastAPI 🐍 • React ⚛️ • MongoDB 🍃 • Docker 🐳**

</div>
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

## Default Admin Account

- **Email**: admin@email.com
- **Password**: 123456

# Tweeky-Queeky-Store-Dockerized-Mongo-FastAPI-app
