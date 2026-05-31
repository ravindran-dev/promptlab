import os
import redis
import logging
from sqlalchemy.orm import Session
from ..models import Prompt
from ..config import settings

logger = logging.getLogger(__name__)

# Setup redis client
redis_client = None
try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    # Test connection
    redis_client.ping()
    logger.info("Connected to Redis successfully.")
except Exception as e:
    logger.warning(f"Failed to connect to Redis. Caching will be disabled. Error: {e}")
    redis_client = None

class PromptRegistry:
    @staticmethod
    def get_prompt_content(version: str, db: Session) -> str:
        """
        Retrieves the prompt text for a given version.
        Tries to load from Redis first, then PostgreSQL, and falls back to the filesystem.
        """
        cache_key = f"prompt:{version}"
        
        # 1. Try Redis cache
        if redis_client:
            try:
                cached_prompt = redis_client.get(cache_key)
                if cached_prompt:
                    logger.info(f"Loaded prompt version '{version}' from Redis cache.")
                    return cached_prompt
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")

        # 2. Try PostgreSQL Database
        db_prompt = db.query(Prompt).filter(Prompt.version == version, Prompt.is_active == True).first()
        if db_prompt:
            logger.info(f"Loaded prompt version '{version}' from Database.")
            content = db_prompt.content
            # Save to Redis cache
            if redis_client:
                try:
                    redis_client.setex(cache_key, 3600, content) # Cache for 1 hour
                except Exception as e:
                    logger.warning(f"Redis set failed: {e}")
            return content

        # 3. Fallback to Filesystem
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(os.path.dirname(current_dir))
        file_path = os.path.join(backend_dir, "prompts", f"{version}.md")
        
        if os.path.exists(file_path):
            logger.info(f"Loaded prompt version '{version}' from Filesystem fallback.")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Write back to DB so it exists there in the future
                new_db_prompt = Prompt(
                    version=version,
                    content=content,
                    description=f"Auto-imported filesystem prompt {version}",
                    is_active=True
                )
                db.add(new_db_prompt)
                db.commit()
                
                # Cache in Redis
                if redis_client:
                    redis_client.setex(cache_key, 3600, content)
                return content
            except Exception as e:
                logger.error(f"Error reading filesystem prompt version '{version}': {e}")
                raise ValueError(f"Prompt version '{version}' read failed on filesystem: {e}")
                
        raise ValueError(f"Prompt version '{version}' not found in Cache, Database, or Filesystem.")

    @staticmethod
    def set_prompt_content(version: str, content: str, db: Session, description: str = None) -> Prompt:
        """
        Saves or updates a prompt version in the database and invalidates the cache.
        """
        db_prompt = db.query(Prompt).filter(Prompt.version == version).first()
        if db_prompt:
            db_prompt.content = content
            if description:
                db_prompt.description = description
            db_prompt.is_active = True
        else:
            db_prompt = Prompt(
                version=version,
                content=content,
                description=description or f"Registered prompt version {version}",
                is_active=True
            )
            db.add(db_prompt)
        
        db.commit()
        db.refresh(db_prompt)
        
        # Update Redis cache
        if redis_client:
            try:
                cache_key = f"prompt:{version}"
                redis_client.setex(cache_key, 3600, content)
                # Invalidate any dashboard summary cache to ensure updates are reflected
                redis_client.delete("dashboard:stats")
            except Exception as e:
                logger.warning(f"Redis cache update failed: {e}")
                
        return db_prompt
