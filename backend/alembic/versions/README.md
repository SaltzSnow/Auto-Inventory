# Database Migrations

This directory contains Alembic migration scripts for the AI Inventory Management system.

## Initial Migration (001)

The initial migration creates:
- **pgvector extension** for vector similarity search
- **products table** with vector embedding column
- **receipts table** for tracking uploaded receipts
- **transactions table** for inventory updates
- **transaction_items table** for individual transaction items

### Indexes Created

1. **products table**:
   - `ix_products_name` - B-tree index on name column
   - `ix_products_created_at` - B-tree index on created_at column
   - `ix_products_embedding` - IVFFlat index for vector similarity search

2. **receipts table**:
   - `ix_receipts_created_at` - B-tree index on created_at column

3. **transactions table**:
   - `ix_transactions_receipt_id` - B-tree index on receipt_id column
   - `ix_transactions_created_at` - B-tree index on created_at column

4. **transaction_items table**:
   - `ix_transaction_items_transaction_id` - B-tree index on transaction_id column
   - `ix_transaction_items_product_id` - B-tree index on product_id column

## Running Migrations

### Apply migrations:
```bash
cd backend
alembic upgrade head
```

### Rollback migrations:
```bash
cd backend
alembic downgrade -1
```

### Create new migration:
```bash
cd backend
alembic revision -m "description of changes"
```

### Auto-generate migration from model changes:
```bash
cd backend
alembic revision --autogenerate -m "description of changes"
```

## Seeding Test Data

After running migrations, seed the database with test products:

```bash
cd backend
python seed.py
```

This will create 10 sample products with embeddings.
