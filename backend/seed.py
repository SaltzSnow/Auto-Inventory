"""Seed database with test data."""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

from database import AsyncSessionLocal, init_db
from models.product import Product
import httpx


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding using OpenRouter API."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Warning: OPENROUTER_API_KEY not set. Using dummy embeddings.")
        # Return dummy embedding for testing
        return [0.0] * 1536
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                'https://openrouter.ai/api/v1/embeddings',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'google/gemini-embedding-001',
                    'input': text
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['data'][0]['embedding']
            else:
                print(f"Warning: Failed to generate embedding. Status: {response.status_code}")
                return [0.0] * 1536
    except Exception as e:
        print(f"Warning: Error generating embedding: {e}")
        return [0.0] * 1536


async def seed_products():
    """Seed products with embeddings."""
    products_data = [
        {
            "name": "โค้ก 325 มล.",
            "unit": "กระป๋อง",
            "quantity": 0,
            "reorder_point": 20,
            "description": "โคคา-โคล่า กระป๋อง 325 มิลลิลิตร"
        },
        {
            "name": "น้ำเปล่า",
            "unit": "ขวด",
            "quantity": 0,
            "reorder_point": 30,
            "description": "น้ำดื่มบรรจุขวด"
        },
        {
            "name": "นมสด",
            "unit": "กล่อง",
            "quantity": 0,
            "reorder_point": 15,
            "description": "นมสดพาสเจอร์ไรส์"
        },
        {
            "name": "ขนมปัง",
            "unit": "ถุง",
            "quantity": 0,
            "reorder_point": 10,
            "description": "ขนมปังแผ่น"
        },
        {
            "name": "ไข่ไก่",
            "unit": "ฟอง",
            "quantity": 0,
            "reorder_point": 50,
            "description": "ไข่ไก่สด"
        },
        {
            "name": "น้ำตาล",
            "unit": "กิโลกรัม",
            "quantity": 0,
            "reorder_point": 5,
            "description": "น้ำตาลทราย"
        },
        {
            "name": "กาแฟสำเร็จรูป",
            "unit": "ซอง",
            "quantity": 0,
            "reorder_point": 25,
            "description": "กาแฟสำเร็จรูป 3 in 1"
        },
        {
            "name": "มาม่า",
            "unit": "ซอง",
            "quantity": 0,
            "reorder_point": 40,
            "description": "บะหมี่กึ่งสำเร็จรูป"
        },
        {
            "name": "น้ำมันพืช",
            "unit": "ลิตร",
            "quantity": 0,
            "reorder_point": 3,
            "description": "น้ำมันพืชสำหรับทำอาหาร"
        },
        {
            "name": "ข้าวสาร",
            "unit": "กิโลกรัม",
            "quantity": 0,
            "reorder_point": 10,
            "description": "ข้าวหอมมะลิ"
        }
    ]
    
    async with AsyncSessionLocal() as session:
        print("Generating embeddings and creating products...")
        
        for idx, product_data in enumerate(products_data, 1):
            print(f"[{idx}/10] Creating product: {product_data['name']}")
            
            # Generate embedding
            embedding = await generate_embedding(product_data['name'])
            
            # Create product
            product = Product(
                name=product_data['name'],
                unit=product_data['unit'],
                quantity=product_data['quantity'],
                reorder_point=product_data['reorder_point'],
                description=product_data['description'],
                embedding=embedding
            )
            
            session.add(product)
        
        await session.commit()
        print("\n✓ Successfully seeded 10 products with embeddings!")


async def main():
    """Main function to run seeding."""
    print("Starting database seeding...")
    print("=" * 50)
    
    # Initialize database (create tables if they don't exist)
    print("Initializing database...")
    await init_db()
    
    # Seed products
    await seed_products()
    
    print("=" * 50)
    print("Database seeding completed!")


if __name__ == "__main__":
    asyncio.run(main())
