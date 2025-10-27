"""OpenRouter AI service for embeddings and LLM calls."""
import httpx
import os
from typing import List
import logging
import base64
import json
from pathlib import Path
from pydantic import ValidationError

from schemas.receipt import ExtractedItem, MatchedProduct, ValidatedItem
from utils.retry import retry_external_service
from exceptions import ExternalServiceError
from utils.cache import cache_service

logger = logging.getLogger(__name__)


class OpenRouterService:
    """Service for interacting with OpenRouter API."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set in environment variables")
        
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY not set in environment variables")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.gemini_base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.embedding_model = "models/gemini-embedding-001"
        self.vision_model = "google/gemini-2.5-flash"
        self.validation_model = "google/gemini-2.5-flash"
        self.timeout = 30.0
    
    @retry_external_service(max_attempts=3)
    async def extract_items_from_image(self, image_path: str) -> tuple[List[ExtractedItem], str]:
        """
        Extract items from receipt image using Gemini Vision.
        
        Args:
            image_path: Path to receipt image file
            
        Returns:
            Tuple of (List of ExtractedItem objects, raw OCR content string)
            
        Raises:
            Exception: If API call fails or image cannot be read
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")
        
        # Read and encode image to base64
        try:
            image_file_path = Path(image_path)
            if not image_file_path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            with open(image_file_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Determine image type
            suffix = image_file_path.suffix.lower()
            image_type = "jpeg" if suffix in [".jpg", ".jpeg"] else "png"
            
        except Exception as e:
            logger.error(f"Error reading image file: {str(e)}")
            raise Exception(f"Failed to read image file: {str(e)}")
        
        # Prepare prompt
        prompt = """คุณคือ AI ที่ช่วยอ่านและสกัดรายการสินค้าจากใบเสร็จ
กรุณาอ่านรูปภาพใบเสร็จนี้และสกัดรายการสินค้าทั้งหมด
ให้ตอบกลับเป็น JSON array เท่านั้น ไม่ต้องมีข้อความอื่น:
[{ "name": "ชื่อสินค้า", "quantity": "จำนวนและหน่วย", "original_text": "ข้อความต้นฉบับจากใบเสร็จ" }]

ตัวอย่าง:
[
  { "name": "โค้ก 325 มล.", "quantity": "6 กระป๋อง", "original_text": "โค้ก 325มล. x6" },
  { "name": "น้ำเปล่า", "quantity": "12 ขวด", "original_text": "น้ำเปล่า 12ขวด" }
]

สำคัญ: ให้ตอบเป็น JSON array เท่านั้น ไม่ต้องมีคำอธิบายเพิ่มเติม"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.vision_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": prompt
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/{image_type};base64,{image_data}"
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                )
                
                response.raise_for_status()
                
                # Capture raw response text before parsing
                response_text = response.text
                
                try:
                    result = response.json()
                except json.JSONDecodeError as json_err:
                    logger.error(f"JSON decode error extracting items. Response status: {response.status_code}, Response text: {response_text[:500]}")
                    raise ExternalServiceError(
                        message=f"ไม่สามารถแปลง response จาก API ได้\n\nรายละเอียด: {str(json_err)}\n\nResponse ที่ได้: {response_text[:200]}",
                        details={"error": str(json_err), "response_text": response_text, "status_code": response.status_code}
                    )
                
                if "choices" not in result or len(result["choices"]) == 0:
                    logger.error(f"Invalid response structure: {result}")
                    raise Exception(f"Invalid response from OpenRouter API: {result}")
                
                content = result["choices"][0]["message"]["content"]
                raw_content = content
                
                # Parse JSON from response (handle markdown code blocks)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                # Parse JSON
                items_data = json.loads(content)
                
                # Convert to ExtractedItem objects
                extracted_items = []
                try:
                    for item in items_data:
                        # Handle empty and None values
                        name = (item.get("name") or "").strip()
                        quantity = (item.get("quantity") or "").strip()
                        original_text = (item.get("original_text") or name).strip()
                        
                        # Skip items with empty required fields
                        if not name or not quantity:
                            logger.warning(f"Skipping item with empty fields: {item}")
                            continue
                        
                        extracted_items.append(
                            ExtractedItem(
                                name=name,
                                quantity=quantity,
                                original_text=original_text if original_text else name
                            )
                        )
                except ValidationError as ve:
                    logger.error(f"Validation error creating ExtractedItem: {str(ve)}")
                    raise ExternalServiceError(
                        message=f"ข้อมูลจาก AI ไม่ถูกต้อง\n\nรายละเอียด: {str(ve)}\n\nข้อมูลที่ OCR ได้: {raw_content}",
                        details={"error": str(ve), "raw_ocr_output": raw_content}
                    )
                except Exception as item_error:
                    logger.error(f"Error processing items: {str(item_error)}")
                    raise ExternalServiceError(
                        message=f"เกิดข้อผิดพลาดในการประมวลผล items\n\nรายละเอียด: {str(item_error)}\n\nข้อมูลที่ OCR ได้: {raw_content}",
                        details={"error": str(item_error), "error_type": type(item_error).__name__, "raw_ocr_output": raw_content}
                    )
                
                if not extracted_items:
                    logger.warning(f"No items extracted. Raw OCR output: {raw_content}")
                    raise ExternalServiceError(
                        message=f"ไม่พบรายการสินค้าในใบเสร็จ\n\nข้อมูลที่ OCR ได้: {raw_content}",
                        details={"raw_ocr_output": raw_content}
                    )
                
                logger.info(f"Extracted {len(extracted_items)} items from receipt")
                
                return (extracted_items, raw_content)
                
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            logger.error(f"HTTP error extracting items: {e.response.status_code} - {error_text}")
            raise ExternalServiceError(
                message=f"ไม่สามารถสกัดข้อมูลจากใบเสร็จได้ (รหัสข้อผิดพลาด: {e.response.status_code})\n\nรายละเอียด: {error_text}",
                details={"status_code": e.response.status_code, "error": str(e), "response": error_text}
            )
        except httpx.RequestError as e:
            logger.error(f"Request error extracting items: {str(e)}")
            raise ExternalServiceError(
                message=f"ไม่สามารถเชื่อมต่อกับบริการ AI ได้\n\nรายละเอียด: {str(e)}",
                details={"error": str(e)}
            )
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error extracting items: {str(e)}, content: {content}")
            raise ExternalServiceError(
                message=f"ไม่สามารถแปลงผลลัพธ์จาก AI ได้\n\nรายละเอียด: {str(e)}\n\nContent ที่ได้: {content}",
                details={"error": str(e), "content": content}
            )
        except ExternalServiceError:
            # Re-raise ExternalServiceError as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error extracting items: {str(e)}")
            raise ExternalServiceError(
                message=f"เกิดข้อผิดพลาดในการประมวลผลใบเสร็จ\n\nรายละเอียด: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )
    
    @retry_external_service(max_attempts=3)
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate vector embedding for text using Gemini API directly.
        Uses Redis cache to avoid regenerating embeddings for the same text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector (1536 dimensions)
            
        Raises:
            Exception: If API call fails
        """
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        normalized_text = text.strip()
        
        # Check cache first
        cached_embedding = await cache_service.get_embedding(normalized_text)
        if cached_embedding:
            return cached_embedding
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.gemini_base_url}/{self.embedding_model}:embedContent",
                    headers={
                        "x-goog-api-key": self.gemini_api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.embedding_model,
                        "content": {
                            "parts": [{
                                "text": normalized_text
                            }]
                        },
                        "output_dimensionality": 1536
                    }
                )
                
                response.raise_for_status()
                
                # Capture raw response text before parsing
                response_text = response.text
                
                try:
                    result = response.json()
                except json.JSONDecodeError as json_err:
                    logger.error(f"JSON decode error. Response status: {response.status_code}, Response text: {response_text[:500]}")
                    raise ExternalServiceError(
                        message=f"ไม่สามารถแปลง response จาก Gemini API ได้\n\nรายละเอียด: {str(json_err)}\n\nResponse ที่ได้: {response_text[:200]}",
                        details={"error": str(json_err), "response_text": response_text, "status_code": response.status_code}
                    )
                
                if "embedding" not in result or "values" not in result["embedding"]:
                    logger.error(f"Invalid response structure: {result}")
                    raise Exception(f"Invalid response from Gemini API: {result}")
                
                embedding = result["embedding"]["values"]
                
                # With output_dimensionality=1536, we should always get exactly 1536 dimensions
                # This is a safety check in case something goes wrong
                if len(embedding) != 1536:
                    logger.warning(
                        f"Unexpected embedding dimension: {len(embedding)} (expected 1536). "
                        f"Adjusting to match database schema."
                    )
                    if len(embedding) > 1536:
                        # Truncate if too large (shouldn't happen with output_dimensionality)
                        embedding = embedding[:1536]
                    elif len(embedding) < 1536:
                        # Pad with zeros if too small (shouldn't happen with output_dimensionality)
                        embedding = embedding + [0.0] * (1536 - len(embedding))
                
                logger.info(f"Generated embedding for text: {normalized_text[:50]}... (dimension: {len(embedding)})")
                
                # Cache the embedding for 7 days
                await cache_service.set_embedding(normalized_text, embedding)
                
                return embedding
                
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            logger.error(f"HTTP error generating embedding: {e.response.status_code} - {error_text}")
            raise ExternalServiceError(
                message=f"ไม่สามารถสร้าง embedding ได้ (รหัสข้อผิดพลาด: {e.response.status_code})\n\nรายละเอียด: {error_text}",
                details={"status_code": e.response.status_code, "error": str(e), "response": error_text}
            )
        except httpx.RequestError as e:
            logger.error(f"Request error generating embedding: {str(e)}")
            raise ExternalServiceError(
                message=f"ไม่สามารถเชื่อมต่อกับบริการ AI ได้\n\nรายละเอียด: {str(e)}",
                details={"error": str(e)}
            )
        except ExternalServiceError:
            # Re-raise ExternalServiceError as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {str(e)}")
            raise ExternalServiceError(
                message=f"เกิดข้อผิดพลาดในการสร้าง embedding\n\nรายละเอียด: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )
    
    @retry_external_service(max_attempts=3)
    async def validate_and_convert(
        self, 
        matched_item: MatchedProduct, 
        original_text: str
    ) -> ValidatedItem:
        """
        Validate and convert item units using LLM.
        
        This function uses Claude 3 Opus to:
        1. Confirm the product match is correct
        2. Convert compound units to individual units (e.g., "แพ็ค 6 กระป๋อง" → 6 กระป๋อง)
        3. Provide a confidence score for the validation
        
        Args:
            matched_item: Product matched from inventory with similarity score
            original_text: Original text from receipt
            
        Returns:
            ValidatedItem with confirmed product_id, quantity, unit, and confidence
            
        Raises:
            Exception: If API call fails or response cannot be parsed
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")
        
        # Prepare prompt
        system_prompt = """คุณคือ AI ที่ช่วยยืนยันและแปลงหน่วยสินค้าจากใบเสร็จ
คุณต้องวิเคราะห์ข้อความจากใบเสร็จและยืนยันว่าตรงกับสินค้าในคลังหรือไม่
จากนั้นแปลงจำนวนเป็นหน่วยเดี่ยว

ให้ตอบกลับเป็น JSON เท่านั้น:
{
  "product_id": "id ของสินค้า",
  "product_name": "ชื่อสินค้า",
  "quantity": จำนวนเป็นตัวเลข (int),
  "unit": "หน่วย",
  "confidence": ค่าความมั่นใจ 0.0-1.0 (float),
  "original_text": "ข้อความต้นฉบับ"
}

ตัวอย่าง:
- "โค้กแพ็ค 6 กระป๋อง" → quantity: 6, unit: "กระป๋อง"
- "น้ำเปล่า 12 ขวด" → quantity: 12, unit: "ขวด"
- "ขนมปัง 2 แพ็ค" → quantity: 2, unit: "แพ็ค"

ถ้าไม่แน่ใจหรือข้อมูลไม่ชัดเจน ให้ confidence ต่ำกว่า 0.8"""

        user_prompt = f"""สินค้าในคลัง: "{matched_item.product_name}" (หน่วย: {matched_item.unit})
ข้อความจากใบเสร็จ: "{original_text}"
ความคล้ายคลึงจากการจับคู่: {matched_item.similarity_score:.2f}

กรุณายืนยันและแปลงเป็นจำนวนชิ้นเดี่ยว"""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.validation_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": user_prompt
                            }
                        ],
                        "temperature": 0.1  # Low temperature for consistent validation
                    }
                )
                
                response.raise_for_status()
                
                # Capture raw response text before parsing
                response_text = response.text
                
                try:
                    result = response.json()
                except json.JSONDecodeError as json_err:
                    logger.error(f"JSON decode error validating item. Response status: {response.status_code}, Response text: {response_text[:500]}")
                    raise ExternalServiceError(
                        message=f"ไม่สามารถแปลง response จาก API ได้\n\nรายละเอียด: {str(json_err)}\n\nResponse ที่ได้: {response_text[:200]}",
                        details={"error": str(json_err), "response_text": response_text, "status_code": response.status_code}
                    )
                
                if "choices" not in result or len(result["choices"]) == 0:
                    logger.error(f"Invalid response structure: {result}")
                    raise Exception(f"Invalid response from OpenRouter API: {result}")
                
                content = result["choices"][0]["message"]["content"]
                
                # Parse JSON from response (handle markdown code blocks)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                # Parse JSON
                validated_data = json.loads(content)
                
                # Create ValidatedItem with Pydantic validation
                try:
                    validated_item = ValidatedItem(
                        product_id=matched_item.product_id,  # Always use product_id from matched product (UUID)
                        product_name=validated_data.get("product_name", matched_item.product_name),
                        quantity=int(validated_data.get("quantity", 0)),
                        unit=validated_data.get("unit", matched_item.unit),
                        confidence=float(validated_data.get("confidence", 0.0)),
                        original_text=validated_data.get("original_text", original_text)
                    )
                except ValidationError as ve:
                    logger.error(f"Validation error creating ValidatedItem: {str(ve)}")
                    raise ExternalServiceError(
                        message=f"ข้อมูลจาก AI ไม่ถูกต้อง\n\nรายละเอียด: {str(ve)}\n\nContent ที่ได้: {content}",
                        details={"error": str(ve), "content": content, "validated_data": validated_data}
                    )
                
                # Log warning if confidence is low
                if validated_item.confidence < 0.8:
                    logger.warning(
                        f"Low confidence validation: {validated_item.confidence:.2f} "
                        f"for item '{original_text}' → '{validated_item.product_name}'"
                    )
                
                logger.info(
                    f"Validated item: {validated_item.product_name} "
                    f"(quantity: {validated_item.quantity} {validated_item.unit}, "
                    f"confidence: {validated_item.confidence:.2f})"
                )
                
                return validated_item
                
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            logger.error(f"HTTP error validating item: {e.response.status_code} - {error_text}")
            raise ExternalServiceError(
                message=f"ไม่สามารถยืนยันข้อมูลสินค้าได้ (รหัสข้อผิดพลาด: {e.response.status_code})\n\nรายละเอียด: {error_text}",
                details={"status_code": e.response.status_code, "error": str(e), "response": error_text}
            )
        except httpx.RequestError as e:
            logger.error(f"Request error validating item: {str(e)}")
            raise ExternalServiceError(
                message=f"ไม่สามารถเชื่อมต่อกับบริการ AI ได้\n\nรายละเอียด: {str(e)}",
                details={"error": str(e)}
            )
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error validating item: {str(e)}, content: {content}")
            raise ExternalServiceError(
                message=f"ไม่สามารถแปลงผลลัพธ์จาก AI ได้\n\nรายละเอียด: {str(e)}\n\nContent ที่ได้: {content}",
                details={"error": str(e), "content": content}
            )
        except ValueError as e:
            logger.error(f"Value error validating item: {str(e)}")
            raise ExternalServiceError(
                message=f"ข้อมูลจาก AI ไม่ถูกต้อง\n\nรายละเอียด: {str(e)}",
                details={"error": str(e)}
            )
        except ExternalServiceError:
            # Re-raise ExternalServiceError as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error validating item: {str(e)}")
            raise ExternalServiceError(
                message=f"เกิดข้อผิดพลาดในการยืนยันข้อมูลสินค้า\n\nรายละเอียด: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )


# Singleton instance
openrouter_service = OpenRouterService()
