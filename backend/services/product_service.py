"""Product service for business logic."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, text
from typing import List, Optional, Dict
from models.product import Product
from schemas.product import ProductCreate, ProductUpdate
from schemas.receipt import MatchedProduct, ValidatedItem
from services.openrouter_service import openrouter_service
from exceptions import EmbeddingFailureError
import logging

logger = logging.getLogger(__name__)


class ProductService:
    """Service for managing products."""
    
    async def create_product(
        self,
        db: AsyncSession,
        product_data: ProductCreate
    ) -> Product:
        """
        Create a new product with auto-generated embedding.
        
        Args:
            db: Database session
            product_data: Product creation data
            
        Returns:
            Created product
            
        Raises:
            EmbeddingFailureError: If embedding generation fails and force_without_embedding is False
        """
        # Try to generate embedding from product name
        embedding = None
        embedding_error = None
        
        try:
            embedding = await openrouter_service.generate_embedding(product_data.name)
            logger.info(f"Generated embedding for product: {product_data.name}")
        except Exception as e:
            embedding_error = str(e)
            logger.warning(
                f"Failed to generate embedding for product '{product_data.name}': {embedding_error}"
            )
            
            # If not forcing creation without embedding, raise error
            if not product_data.force_without_embedding:
                raise EmbeddingFailureError(
                    message=(
                        f"ไม่สามารถสร้าง embedding สำหรับสินค้า '{product_data.name}' ได้\n\n"
                        f"รายละเอียด: {embedding_error}\n\n"
                        f"หากต้องการสร้างสินค้าโดยไม่มี embedding (ฟีเจอร์ AI search จะไม่ทำงาน) "
                        f"กรุณากดปุ่ม 'ดำเนินการต่อแบบไม่มี Embedding'"
                    ),
                    details={
                        "product_name": product_data.name,
                        "error": embedding_error,
                        "can_force_create": True
                    }
                )
            
            logger.info(
                f"Creating product '{product_data.name}' without embedding (forced by user)"
            )
        
        # Create product instance
        product = Product(
            name=product_data.name,
            unit=product_data.unit,
            quantity=product_data.quantity,
            reorder_point=product_data.reorder_point,
            description=product_data.description,
            embedding=embedding
        )
        
        db.add(product)
        await db.flush()
        await db.refresh(product)
        
        logger.info(f"Created product: {product.id} - {product.name}")
        
        return product
    
    async def update_product(
        self,
        db: AsyncSession,
        product_id: str,
        product_data: ProductUpdate
    ) -> Optional[Product]:
        """
        Update an existing product. Regenerate embedding if name changed.
        
        Args:
            db: Database session
            product_id: Product ID to update
            product_data: Product update data
            
        Returns:
            Updated product or None if not found
        """
        # Get existing product
        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            return None
        
        # Track if name changed
        name_changed = False
        
        # Update fields
        if product_data.name is not None:
            if product_data.name != product.name:
                name_changed = True
            product.name = product_data.name
        
        if product_data.unit is not None:
            product.unit = product_data.unit
        
        if product_data.quantity is not None:
            product.quantity = product_data.quantity
        
        if product_data.reorder_point is not None:
            product.reorder_point = product_data.reorder_point
        
        if product_data.description is not None:
            product.description = product_data.description
        
        # Regenerate embedding if name changed
        if name_changed:
            try:
                embedding = await openrouter_service.generate_embedding(product.name)
                product.embedding = embedding
                logger.info(f"Regenerated embedding for product: {product.id}")
            except Exception as e:
                logger.warning(
                    f"Failed to regenerate embedding for product '{product.name}': {str(e)}. "
                    f"Product will be updated without embedding (AI search won't work for this product)"
                )
                product.embedding = None
        
        await db.flush()
        await db.refresh(product)
        
        logger.info(f"Updated product: {product.id} - {product.name}")
        
        return product
    
    async def delete_product(
        self,
        db: AsyncSession,
        product_id: str
    ) -> bool:
        """
        Delete a product.
        
        Args:
            db: Database session
            product_id: Product ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            return False
        
        await db.delete(product)
        await db.flush()
        
        logger.info(f"Deleted product: {product_id}")
        
        return True
    
    async def get_products(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        Get all products with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of products
        """
        result = await db.execute(
            select(Product)
            .order_by(Product.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        products = result.scalars().all()
        
        return list(products)
    
    async def get_product_by_id(
        self,
        db: AsyncSession,
        product_id: str
    ) -> Optional[Product]:
        """
        Get a single product by ID.
        
        Args:
            db: Database session
            product_id: Product ID
            
        Returns:
            Product or None if not found
        """
        result = await db.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()
    
    async def search_products(
        self,
        db: AsyncSession,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        Search products by name (case-insensitive).
        
        Args:
            db: Database session
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching products
        """
        search_pattern = f"%{query}%"
        
        result = await db.execute(
            select(Product)
            .where(Product.name.ilike(search_pattern))
            .order_by(Product.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        products = result.scalars().all()
        
        return list(products)
    
    async def find_matching_product(
        self,
        db: AsyncSession,
        item_name: str
    ) -> Optional[MatchedProduct]:
        """
        Find matching product using vector similarity search.
        Falls back to text-based search if embedding generation fails.
        
        Uses PGVector to find the most similar product based on embedding similarity.
        Only returns a match if similarity score is greater than 0.8.
        
        Args:
            db: Database session
            item_name: Name of item to match
            
        Returns:
            MatchedProduct if similarity > 0.8, otherwise None
        """
        try:
            # Try to generate embedding for the item name
            embedding = await openrouter_service.generate_embedding(item_name)
            
            # Convert embedding list to PostgreSQL vector format
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            
            # Execute vector similarity search query
            query = text("""
                SELECT id, name, unit,
                       1 - (embedding <=> :embedding::vector) as similarity
                FROM products
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :embedding::vector
                LIMIT 1
            """)
            
            result = await db.execute(
                query,
                {"embedding": embedding_str}
            )
            row = result.fetchone()
            
            # Check if we have a result and if similarity meets threshold
            if row and row.similarity > 0.8:
                matched_product = MatchedProduct(
                    product_id=str(row.id),
                    product_name=row.name,
                    unit=row.unit,
                    similarity_score=float(row.similarity)
                )
                
                logger.info(
                    f"Found matching product for '{item_name}': "
                    f"{matched_product.product_name} (similarity: {matched_product.similarity_score:.3f})"
                )
                
                return matched_product
            
            logger.info(
                f"No matching product found for '{item_name}' "
                f"(best similarity: {row.similarity:.3f if row else 0})"
            )
            return None
            
        except Exception as e:
            logger.warning(
                f"Vector search failed for '{item_name}': {str(e)}. "
                f"Falling back to text-based search..."
            )
            
            # Fallback to text-based search using ILIKE
            try:
                search_pattern = f"%{item_name}%"
                result = await db.execute(
                    select(Product)
                    .where(Product.name.ilike(search_pattern))
                    .order_by(Product.created_at.desc())
                    .limit(1)
                )
                product = result.scalar_one_or_none()
                
                if product:
                    # Use a fixed similarity score for text-based matches
                    matched_product = MatchedProduct(
                        product_id=str(product.id),
                        product_name=product.name,
                        unit=product.unit,
                        similarity_score=0.85  # Fixed score for text matches
                    )
                    
                    logger.info(
                        f"Found matching product using text search for '{item_name}': "
                        f"{matched_product.product_name}"
                    )
                    
                    return matched_product
                
                logger.info(f"No matching product found for '{item_name}' using text search")
                return None
                
            except Exception as text_error:
                logger.error(f"Text-based search also failed for '{item_name}': {str(text_error)}")
                return None
    
    async def update_inventory(
        self,
        db: AsyncSession,
        items: List[ValidatedItem]
    ) -> List[Dict[str, any]]:
        """
        Update inventory quantities for multiple products atomically.
        
        Uses database transaction to ensure atomic updates.
        Checks for low stock alerts after updating.
        
        Args:
            db: Database session
            items: List of validated items to update inventory
            
        Returns:
            List of products that need low stock alert (quantity < reorder_point)
            
        Raises:
            ValueError: If any product is not found
        """
        if not items:
            return []
        
        low_stock_products = []
        
        try:
            # Update each product's quantity
            for item in items:
                # Get the product
                result = await db.execute(
                    select(Product).where(Product.id == item.product_id)
                )
                product = result.scalar_one_or_none()
                
                if not product:
                    raise ValueError(f"Product with id {item.product_id} not found")
                
                # Update quantity (add to existing quantity)
                old_quantity = product.quantity
                product.quantity = product.quantity + item.quantity
                
                logger.info(
                    f"Updated inventory for {product.name}: "
                    f"{old_quantity} + {item.quantity} = {product.quantity}"
                )
                
                # Check if product is now low stock
                if product.quantity < product.reorder_point:
                    low_stock_products.append({
                        "product_id": product.id,
                        "product_name": product.name,
                        "quantity": product.quantity,
                        "reorder_point": product.reorder_point,
                        "unit": product.unit
                    })
                    logger.warning(
                        f"Low stock alert: {product.name} "
                        f"(quantity: {product.quantity}, reorder point: {product.reorder_point})"
                    )
            
            # Flush changes to database
            await db.flush()
            
            logger.info(
                f"Successfully updated inventory for {len(items)} products. "
                f"{len(low_stock_products)} products need reordering."
            )
            
            return low_stock_products
            
        except Exception as e:
            logger.error(f"Error updating inventory: {str(e)}")
            raise


# Singleton instance
product_service = ProductService()
