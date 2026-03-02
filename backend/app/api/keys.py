from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.api_key import APIKey, ServiceEnum
from app.models.schemas import APIKeyCreate, APIKeyResponse
from app.api.auth import get_current_user
from app.services.encryption import EncryptionService
from app.core.config import settings

router = APIRouter()

@router.get("/", response_model=List[APIKeyResponse])
def get_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all API keys for current user"""
    keys = db.query(APIKey).filter(APIKey.owner_id == current_user.id).all()
    return keys

@router.post("/", response_model=APIKeyResponse)
def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key (encrypted storage)"""
    # Validate service
    try:
        service_enum = ServiceEnum(key_data.service)
    except ValueError:
        available = [s.value for s in ServiceEnum]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid service. Available services: {available}"
        )

    # Encrypt the key
    encryption_service = EncryptionService(settings.ENCRYPTION_KEY)
    encrypted_key = encryption_service.encrypt(key_data.key)

    # Create API key record
    api_key = APIKey(
        owner_id=current_user.id,
        name=key_data.name,
        service=service_enum,
        encrypted_key=encrypted_key
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return api_key

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.owner_id == current_user.id
    ).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    db.delete(api_key)
    db.commit()
    return None

@router.put("/{key_id}/deactivate", response_model=APIKeyResponse)
def deactivate_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate an API key (soft delete)"""
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.owner_id == current_user.id
    ).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    api_key.is_active = False
    db.commit()
    db.refresh(api_key)
    return api_key