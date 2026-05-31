from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Prompt
from ..schemas import PromptCreate, PromptResponse, PromptUpdate
from ..services.registry import PromptRegistry

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

@router.get("", response_model=List[PromptResponse])
def list_prompts(db: Session = Depends(get_db)):
    """
    List all registered prompt versions in the registry.
    """
    return db.query(Prompt).order_by(Prompt.version.desc()).all()

@router.get("/{version}", response_model=PromptResponse)
def get_prompt(version: str, db: Session = Depends(get_db)):
    """
    Get the details of a specific prompt version.
    """
    prompt = db.query(Prompt).filter(Prompt.version == version).first()
    if not prompt:
        # Try loading via registry fallback (files)
        try:
            content = PromptRegistry.get_prompt_content(version, db)
            prompt = db.query(Prompt).filter(Prompt.version == version).first()
        except Exception:
            raise HTTPException(status_code=404, detail=f"Prompt version '{version}' not found.")
            
    return prompt

@router.post("", response_model=PromptResponse)
def register_prompt(payload: PromptCreate, db: Session = Depends(get_db)):
    """
    Create or update a prompt version in the registry.
    """
    prompt = PromptRegistry.set_prompt_content(
        version=payload.version,
        content=payload.content,
        db=db,
        description=payload.description
    )
    return prompt

@router.put("/{version}", response_model=PromptResponse)
def update_prompt(version: str, payload: PromptUpdate, db: Session = Depends(get_db)):
    """
    Update prompt contents or details.
    """
    prompt = db.query(Prompt).filter(Prompt.version == version).first()
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt version '{version}' not found.")
        
    if payload.content is not None:
        PromptRegistry.set_prompt_content(
            version=version,
            content=payload.content,
            db=db,
            description=payload.description or prompt.description
        )
    else:
        if payload.description is not None:
            prompt.description = payload.description
        if payload.is_active is not None:
            prompt.is_active = payload.is_active
        db.commit()
        db.refresh(prompt)
        
    return prompt
