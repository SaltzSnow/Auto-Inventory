# 🤖 AI-Powered Inventory Management System

ระบบจัดการคลังสินค้าอัจฉริยะที่ใช้ AI อ่านใบเสร็จรับเงินและอัปเดตสต็อกสินค้าโดยอัตโนมัติ พัฒนาเพื่อช่วยธุรกิจขนาดเล็กถึงกลาง (SMEs) จัดการคลังสินค้าอย่างมีประสิทธิภาพ

> **Powered by Gemini and Vector Search**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis&logoColor=white)](https://redis.io/)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [How It Works](#-how-it-works)
- [Technology Stack](#-technology-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)
- [Development](#-development)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🎯 Core Features
- **📸 AI Receipt OCR** - อัปโหลดใบเสร็จและให้ AI อ่านข้อมูลอัตโนมัติด้วย Gemini Vision
- **🔍 Vector Search** - จับคู่สินค้ากับคลังด้วย Semantic Search (PGVector + Embeddings)
- **🤖 Smart Validation** - แปลงหน่วยอัตโนมัติ (เช่น "แพ็ค 6 กระป๋อง" → 6 กระป๋อง)
- **✅ User Confirmation** - ตรวจสอบและแก้ไขข้อมูลก่อนอัปเดตสต็อก
- **⚡ Real-time Processing** - ประมวลผลแบบ async ด้วย Celery + Redis
- **📊 Dashboard** - แสดงภาพรวมสต็อก, ธุรกรรม, และแนวโน้ม
- **🔔 Low Stock Alerts** - แจ้งเตือนเมื่อสินค้าใกล้หมด
- **📦 Inventory Management** - CRUD operations สำหรับจัดการสินค้า
- **📜 Transaction History** - ประวัติการทำรายการทั้งหมดพร้อม audit trail

### 🚀 Advanced Features
- **Embedding Cache** - Redis cache สำหรับ embeddings (TTL 7 วัน)
- **Atomic Transactions** - Database ACID compliance
- **Rate Limiting** - API rate limiting ด้วย slowapi
- **Error Recovery** - Graceful fallbacks และ retry mechanisms
- **Query Invalidation** - Auto-refresh UI หลังอัปเดตข้อมูล

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐│
│  │ Dashboard  │  │  Inventory │  │   Upload   │  │   Confirm  ││
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘│
│         │                │                │                │     │
└─────────┼────────────────┼────────────────┼────────────────┼─────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                              │ HTTP/REST API
┌─────────────────────────────┼─────────────────────────────────────┐
│                         Backend (FastAPI)                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐│
│  │  Products  │  │  Receipts  │  │Transactions│  │  Dashboard ││
│  │   Router   │  │   Router   │  │   Router   │  │   Router   ││
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘│
│         │                │                │                │     │
│  ┌──────┴────────────────┴────────────────┴────────────────┐   │
│  │                    Services Layer                        │   │
│  │  • product_service  • openrouter_service                 │   │
│  │  • transaction_service                                   │   │
│  └──────────────────────────────┬───────────────────────────┘   │
└─────────────────────────────────┼───────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
   ┌────▼─────┐            ┌──────▼──────┐          ┌──────▼──────┐
   │PostgreSQL│            │    Redis    │          │   Celery    │
   │+ PGVector│            │   (Cache)   │          │   Worker    │
   └──────────┘            └─────────────┘          └──────┬──────┘
        │                                                   │
        │                                            ┌──────▼───────────────────┐
        │                                            │  AI Services             │
        │                                            │  • Gemini 2.5 Flash Lite │
        │                                            │  • Gemini Embedding 001  │
        └────────────────────────────────────────────│  • OpenRouter Gateway    │
                                                     └──────────────────────────┘
```

---

## 🔄 How It Works

### Detailed Steps

#### 1. **Upload Receipt** 📤
```
User uploads image → FastAPI validates → Save to storage → Create Receipt record → Trigger Celery task
```

#### 2. **AI Processing** 🤖 (Celery Task)

**Step 1: OCR Extraction (33%)**
```python
# Gemini 2.5 Flash Lite (Vision)
extracted_items = extract_items_from_image(image_path)
# Returns: [{"name": "ไข่ต้ม", "quantity": "1 ชิ้น", "original_text": "ไข่ต้ม x1"}]
```

**Step 2: Product Matching (66%)**
```python
# Generate embedding with google/gemini-embedding-001
embedding = generate_embedding("ไข่ต้ม")  # 1536 dimensions

# Vector similarity search (PostgreSQL + PGVector)
SELECT id, name, unit,
       1 - (embedding <=> :embedding::vector) as similarity
FROM products
ORDER BY embedding <=> :embedding::vector
LIMIT 1

# Returns: MatchedProduct(product_id=UUID, similarity=0.95)
```

**Step 3: Validation & Unit Conversion (100%)**
```python
# Gemini 2.5 Flash Lite validates and converts units (with quantity hint)
validated_item = validate_and_convert(matched_product, original_text, raw_quantity_text)
# Returns: ValidatedItem(product_id=UUID, quantity=1, unit="ชิ้น", confidence=0.95)
```

#### 3. **User Confirmation** ✅
```
Display results → User reviews → Edit if needed → Confirm
```

#### 4. **Inventory Update** 📦
```
Atomic transaction → Update product quantities → Create transaction record → 
Update receipt status → Invalidate React Query cache → Refresh UI
```

---

## 🛠️ Technology Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18 | UI framework |
| TypeScript | 5.x | Type safety |
| TanStack React Query | 5.x | Data fetching & caching |
| React Router | 6.x | Routing |
| Axios | 1.x | HTTP client |
| Tailwind CSS | 3.x | Styling |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.115.x | Web framework |
| Python | 3.11+ | Programming language |
| SQLAlchemy | 2.0.x | ORM (async) |
| asyncpg | 0.29.x | PostgreSQL driver |
| Celery | 5.x | Task queue |
| Redis | Latest | Cache & message broker |
| slowapi | 0.1.x | Rate limiting |

### Database & Infrastructure
| Technology | Version | Purpose |
|------------|---------|---------|
| PostgreSQL | 14+ | Primary database |
| PGVector | 0.5.x | Vector operations |
| Redis | 7.x | Cache & Celery broker |
| Podman | Latest | Containerization |

### AI Services
| Service | Model | Purpose |
|---------|-------|---------|
| Gemini | 2.5 Flash Lite | Vision OCR & validation |
| Gemini | gemini-embedding-001 | Text embeddings (1536-dim) |
| OpenRouter | - | AI API gateway |

---

## 📦 Prerequisites

### Required
- **Podman** and **Podman Compose** (or Docker)
- **Node.js** 18+ (for local development)
- **Python** 3.11+ (for local development)
- **OpenRouter API Key** ([Get here](https://openrouter.ai/))
- **Gemini API Key** ([Get here](https://makersuite.google.com/app/apikey))

### Optional
- **Git** (for version control)
- **VSCode** (recommended IDE)

---

## 🚀 Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/ai-inventory.git
cd ai-inventory
```

### 2. Setup Environment Variables

**Backend:**
```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:
```env
# OpenRouter API Configuration
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/inventory

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Application Configuration
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
```

**Frontend:**
```bash
cd ../frontend
cp .env.example .env
```

Edit `frontend/.env`:
```env
REACT_APP_API_URL=http://localhost:8000
```

### 3. Start with Podman Compose

```bash
# From project root
podman compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Backend API (port 8000)
- Celery Worker
- Frontend (port 3000)

### 4. Access Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## ⚙️ Configuration

### Environment Variables

#### Backend (.env)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENROUTER_API_KEY` | OpenRouter API key | - | ✅ |
| `GEMINI_API_KEY` | Gemini API key | - | ✅ |
| `DATABASE_URL` | PostgreSQL connection string | See above | ✅ |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` | ✅ |
| `UPLOAD_DIR` | Upload directory path | `uploads` | ❌ |
| `MAX_FILE_SIZE` | Max upload size (bytes) | `10485760` (10MB) | ❌ |

#### Frontend (.env)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REACT_APP_API_URL` | Backend API URL | `http://localhost:8000` | ✅ |

---

## 📖 Usage

### 1. Create Products

1. Navigate to **Inventory** page
2. Click **"+ เพิ่มสินค้า"**
3. Fill in product details:
   - Name (e.g., "ไข่ต้ม")
   - Unit (e.g., "ชิ้น")
   - Quantity
   - Reorder Point
   - Description (optional)
4. Click **"บันทึก"**

> **Note:** System will automatically generate embedding for vector search

### 2. Upload Receipt

1. Navigate to **Upload** page
2. Drag & drop or select receipt image
3. Supported formats: JPG, PNG (max 10MB)
4. Click **"อัปโหลดและประมวลผล"**
5. Wait for AI processing (usually 10-30 seconds)

### 3. Confirm Results

1. Review extracted items
2. Check matched products (green checkmark)
3. Edit if needed:
   - Change quantity
   - Change matched product
   - Delete incorrect items
4. Click **"ยืนยันและอัปเดตสต็อก"**

### 4. View Dashboard

- **Summary Cards:** Total items, low stock alerts, transactions
- **Recent Transactions:** Latest 5 transactions
- **Low Stock Products:** Products below reorder point
- **Stock Trend:** 7-day trend chart

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### Products

```http
GET    /api/products           # List all products
POST   /api/products           # Create product
GET    /api/products/{id}      # Get product by ID
PUT    /api/products/{id}      # Update product
DELETE /api/products/{id}      # Delete product
GET    /api/products/search    # Search products
```

#### Receipts

```http
POST   /api/receipts/upload           # Upload receipt image
GET    /api/receipts/task/{task_id}   # Get processing status
POST   /api/receipts/confirm          # Confirm and update inventory
GET    /api/receipts/image/{path}     # Get receipt image
```

#### Transactions

```http
GET    /api/transactions              # List transactions (paginated)
GET    /api/transactions/{id}         # Get transaction by ID
GET    /api/transactions/search       # Search transactions
```

#### Dashboard

```http
GET    /api/dashboard/summary           # Get summary statistics
GET    /api/dashboard/recent-transactions # Get recent transactions
GET    /api/dashboard/low-stock          # Get low stock alerts
GET    /api/dashboard/stock-trend        # Get 7-day stock trend
```

### Example Requests

#### Upload Receipt

```bash
curl -X POST "http://localhost:8000/api/receipts/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@receipt.jpg"
```

Response:
```json
{
  "receipt_id": "4e5ee99f-f1d9-45e2-bd9a-447625f6a450",
  "task_id": "0a690b63-a81d-48c5-8f43-3a479f93ff95",
  "message": "อัปโหลดสำเร็จ กำลังประมวลผลด้วย AI..."
}
```

#### Check Task Status

```bash
curl "http://localhost:8000/api/receipts/task/0a690b63-a81d-48c5-8f43-3a479f93ff95"
```

Response:
```json
{
  "status": "completed",
  "progress": 100,
  "current_step": "done",
  "result": {
    "receipt_id": "4e5ee99f-f1d9-45e2-bd9a-447625f6a450",
    "items": [
      {
        "product_id": "a1b2c3d4-...",
        "product_name": "ไข่ต้ม",
        "quantity": 1,
        "unit": "ชิ้น",
        "confidence": 0.95,
        "original_text": "ไข่ต้ม"
      }
    ],
    "total_items": 1
  }
}
```

For complete API documentation, visit: http://localhost:8000/docs

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **Embedding Dimension Mismatch**

```
Error: expected 1536 dimensions, not 3072
```

**Solution:**
```bash
# Clear Redis cache
podman exec ai-inventory-redis redis-cli FLUSHDB

# Restart services
podman compose restart backend celery_worker
```

#### 2. **Product ID is Product Name Instead of UUID**

```
Error: product_id = "ไข่ต้ม" instead of UUID
```

**Solution:** Already fixed in latest version. Ensure you're using `matched_product.product_id` directly.

#### 3. **Backend Network Error / Crash**

```
Error: Network Error or slowapi parameter conflict
```

**Solution:**
```bash
# Check backend logs
podman logs ai-inventory-backend --tail 50

# Restart backend
podman compose restart backend
```

#### 4. **Dashboard Not Updating After Confirmation**

**Solution:** Already fixed with query invalidation. Ensure React Query cache is invalidated:
```typescript
await queryClient.invalidateQueries({ queryKey: ['products'] });
await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
```

#### 5. **Celery Task Not Processing**

```bash
# Check Celery worker logs
podman logs ai-inventory-celery --tail 50

# Check Redis connection
podman exec ai-inventory-redis redis-cli PING

# Restart Celery
podman compose restart celery_worker
```

### Debug Commands

```bash
# Check all containers
podman ps

# View logs
podman logs ai-inventory-backend --tail 100
podman logs ai-inventory-celery --tail 100
podman logs ai-inventory-redis --tail 100

# Connect to PostgreSQL
podman exec -it ai-inventory-db psql -U postgres -d inventory

# Connect to Redis
podman exec -it ai-inventory-redis redis-cli

# Clear Redis cache
podman exec ai-inventory-redis redis-cli FLUSHDB

# Restart services
podman compose restart backend celery_worker frontend
```

---

## 👨‍💻 Development

### Local Development Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

#### Celery Worker

```bash
cd backend
source venv/bin/activate

# Start Celery worker
celery -A celery_app worker --loglevel=info
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

---

## 📁 Project Structure

```
ai-inventory/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── database.py             # Database configuration
│   ├── celery_app.py          # Celery configuration
│   ├── routers/               # API routes
│   │   ├── products.py
│   │   ├── receipts.py
│   │   ├── transactions.py
│   │   └── dashboard.py
│   ├── services/              # Business logic
│   │   ├── product_service.py
│   │   ├── openrouter_service.py
│   │   ├── transaction_service.py
│   │   └── storage_service.py
│   ├── models/                # SQLAlchemy models
│   │   ├── product.py
│   │   ├── receipt.py
│   │   └── transaction.py
│   ├── schemas/               # Pydantic schemas
│   │   ├── product.py
│   │   ├── receipt.py
│   │   └── transaction.py
│   ├── tasks/                 # Celery tasks
│   │   └── receipt_tasks.py
│   ├── middleware/            # FastAPI middleware
│   │   └── security.py
│   ├── utils/                 # Utilities
│   │   ├── cache.py
│   │   ├── file_validation.py
│   │   └── text_normalization.py
│   ├── exceptions.py          # Custom exceptions
│   ├── alembic/               # Database migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── index.tsx
│   │   ├── pages/            # React pages
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── InventoryPage.tsx
│   │   │   ├── UploadPage.tsx
│   │   │   ├── ProcessingPage.tsx
│   │   │   ├── ConfirmationPage.tsx
│   │   │   └── TransactionsPage.tsx
│   │   ├── components/       # React components
│   │   │   ├── ProductTable.tsx
│   │   │   ├── ProductForm.tsx
│   │   │   ├── ItemEditForm.tsx
│   │   │   ├── ProductDropdown.tsx
│   │   │   ├── EmbeddingFailureModal.tsx
│   │   │   └── Toast.tsx
│   │   ├── hooks/           # Custom hooks
│   │   │   ├── useProducts.ts
│   │   │   ├── useConfirmation.ts
│   │   │   ├── useReceiptUpload.ts
│   │   │   ├── useTransactions.ts
│   │   │   └── useDashboard.ts
│   │   ├── services/        # API services
│   │   │   └── api.ts
│   │   └── types/           # TypeScript types
│   │       └── product.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── .env
├── docker-compose.yml
├── .gitignore
├── README.md
└── START.md
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Coding Standards

- **Backend:** Follow PEP 8 (Python)
- **Frontend:** Follow Airbnb style guide (TypeScript/React)
- Write tests for new features
- Update documentation

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Gemini API** - For powerful vision and embedding models
- **Claude API** - For intelligent validation
- **OpenRouter** - For unified AI API gateway
- **PGVector** - For efficient vector operations
- **FastAPI** - For excellent async Python framework
- **React Query** - For seamless data synchronization

---

Made with ❤️ by Your Team
