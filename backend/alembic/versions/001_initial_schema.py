"""Initial schema with pgvector extension

Revision ID: 001
Revises: 
Create Date: 2025-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('reorder_point', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_products_name', 'products', ['name'])
    op.create_index('ix_products_created_at', 'products', ['created_at'])
    
    # Create ivfflat index for vector similarity search
    op.execute(
        'CREATE INDEX ix_products_embedding ON products USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)'
    )
    
    # Create receipts table
    op.create_table(
        'receipts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.Column('status', sa.Enum('PROCESSING', 'PENDING_CONFIRMATION', 'CONFIRMED', 'FAILED', name='receiptstatus'), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('extracted_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_receipts_created_at', 'receipts', ['created_at'])
    
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('receipt_id', sa.String(), nullable=False),
        sa.Column('total_items', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['receipt_id'], ['receipts.id'], )
    )
    op.create_index('ix_transactions_receipt_id', 'transactions', ['receipt_id'])
    op.create_index('ix_transactions_created_at', 'transactions', ['created_at'])
    
    # Create transaction_items table
    op.create_table(
        'transaction_items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('transaction_id', sa.String(), nullable=False),
        sa.Column('product_id', sa.String(), nullable=False),
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], )
    )
    op.create_index('ix_transaction_items_transaction_id', 'transaction_items', ['transaction_id'])
    op.create_index('ix_transaction_items_product_id', 'transaction_items', ['product_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_transaction_items_product_id', table_name='transaction_items')
    op.drop_index('ix_transaction_items_transaction_id', table_name='transaction_items')
    op.drop_table('transaction_items')
    
    op.drop_index('ix_transactions_created_at', table_name='transactions')
    op.drop_index('ix_transactions_receipt_id', table_name='transactions')
    op.drop_table('transactions')
    
    op.drop_index('ix_receipts_created_at', table_name='receipts')
    op.drop_table('receipts')
    
    op.execute('DROP INDEX IF EXISTS ix_products_embedding')
    op.drop_index('ix_products_created_at', table_name='products')
    op.drop_index('ix_products_name', table_name='products')
    op.drop_table('products')
    
    # Drop pgvector extension
    op.execute('DROP EXTENSION IF EXISTS vector')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS receiptstatus')
