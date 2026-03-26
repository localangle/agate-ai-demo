"""API key service layer for managing encrypted project API keys."""

from typing import Optional, List, Dict
from sqlmodel import Session, select
from .models import ProjectApiKey
from agate_utils.encryption import encrypt_api_key, decrypt_api_key


def get_project_api_key(session: Session, project_id: int, key_name: str) -> Optional[str]:
    """
    Get a decrypted API key for a project.
    
    Args:
        session: Database session
        project_id: Project ID
        key_name: API key name (e.g., "OPENAI_API_KEY")
        
    Returns:
        Decrypted API key value or None if not found
        
    Raises:
        ValueError: If decryption fails
    """
    result = session.exec(
        select(ProjectApiKey).where(
            ProjectApiKey.project_id == project_id,
            ProjectApiKey.key_name == key_name
        )
    ).first()
    
    if not result:
        return None
    
    try:
        return decrypt_api_key(result.encrypted_value)
    except Exception as e:
        raise ValueError(f"Failed to decrypt API key '{key_name}' for project {project_id}: {str(e)}")


def set_project_api_key(session: Session, project_id: int, key_name: str, value: str) -> ProjectApiKey:
    """
    Set an encrypted API key for a project.
    
    Args:
        session: Database session
        project_id: Project ID
        key_name: API key name (e.g., "OPENAI_API_KEY")
        value: API key value to encrypt and store
        
    Returns:
        Created or updated ProjectApiKey record
        
    Raises:
        ValueError: If encryption fails
    """
    if not value.strip():
        raise ValueError("API key value cannot be empty")
    
    try:
        encrypted_value = encrypt_api_key(value)
    except Exception as e:
        raise ValueError(f"Failed to encrypt API key '{key_name}': {str(e)}")
    
    # Check if key already exists
    existing = session.exec(
        select(ProjectApiKey).where(
            ProjectApiKey.project_id == project_id,
            ProjectApiKey.key_name == key_name
        )
    ).first()
    
    if existing:
        # Update existing key
        existing.encrypted_value = encrypted_value
        existing.updated_at = existing.updated_at  # This will be updated by the database
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    else:
        # Create new key
        api_key = ProjectApiKey(
            project_id=project_id,
            key_name=key_name,
            encrypted_value=encrypted_value
        )
        session.add(api_key)
        session.commit()
        session.refresh(api_key)
        return api_key


def delete_project_api_key(session: Session, project_id: int, key_name: str) -> bool:
    """
    Delete an API key for a project.
    
    Args:
        session: Database session
        project_id: Project ID
        key_name: API key name to delete
        
    Returns:
        True if key was deleted, False if not found
    """
    result = session.exec(
        select(ProjectApiKey).where(
            ProjectApiKey.project_id == project_id,
            ProjectApiKey.key_name == key_name
        )
    ).first()
    
    if not result:
        return False
    
    session.delete(result)
    session.commit()
    return True


def list_project_api_keys(session: Session, project_id: int) -> List[ProjectApiKey]:
    """
    List all API keys for a project (metadata only, not decrypted values).
    
    Args:
        session: Database session
        project_id: Project ID
        
    Returns:
        List of ProjectApiKey records (without decrypted values)
    """
    return session.exec(
        select(ProjectApiKey).where(ProjectApiKey.project_id == project_id)
    ).all()


def get_all_project_api_keys(session: Session, project_id: int) -> Dict[str, str]:
    """
    Get all decrypted API keys for a project as a dictionary.
    
    Args:
        session: Database session
        project_id: Project ID
        
    Returns:
        Dictionary mapping key_name to decrypted value
        
    Raises:
        ValueError: If any decryption fails
    """
    api_keys = list_project_api_keys(session, project_id)
    result = {}
    
    for api_key in api_keys:
        try:
            decrypted_value = decrypt_api_key(api_key.encrypted_value)
            result[api_key.key_name] = decrypted_value
        except Exception as e:
            raise ValueError(f"Failed to decrypt API key '{api_key.key_name}' for project {project_id}: {str(e)}")
    
    return result
