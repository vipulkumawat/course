"""
API routes for saved searches management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from app.core.database import get_db
from models.schemas import SavedSearch
from models.pydantic_models import SavedSearchCreate, SavedSearchUpdate, SavedSearchResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[SavedSearchResponse])
async def get_saved_searches(
    user_id: str = Query("demo_user", description="User ID"),
    folder: Optional[str] = Query(None, description="Filter by folder"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    shared: Optional[bool] = Query(None, description="Filter shared searches"),
    db: Session = Depends(get_db)
):
    """Get all saved searches for a user with optional filters"""
    try:
        query = db.query(SavedSearch).filter(SavedSearch.user_id == user_id)
        
        if folder:
            query = query.filter(SavedSearch.folder == folder)
            
        if tag:
            query = query.filter(SavedSearch.tags.contains([tag]))
            
        if shared is not None:
            query = query.filter(SavedSearch.is_shared == shared)
        
        searches = query.order_by(SavedSearch.updated_at.desc()).all()
        
        return [SavedSearchResponse.from_orm(search) for search in searches]
        
    except Exception as e:
        logger.error(f"Error getting saved searches: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve saved searches")

@router.get("/{search_id}", response_model=SavedSearchResponse)
async def get_saved_search(
    search_id: str,
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Get a specific saved search by ID"""
    search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == user_id
    ).first()
    
    if not search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    # Update last used timestamp
    search.last_used = datetime.utcnow()
    search.usage_count += 1
    db.commit()
    
    return SavedSearchResponse.from_orm(search)

@router.post("/", response_model=SavedSearchResponse)
async def create_saved_search(
    search_data: SavedSearchCreate,
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Create a new saved search"""
    try:
        # Check for duplicate names
        existing = db.query(SavedSearch).filter(
            SavedSearch.user_id == user_id,
            SavedSearch.name == search_data.name
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Search name already exists")
        
        new_search = SavedSearch(
            name=search_data.name,
            description=search_data.description,
            user_id=user_id,
            query_params=search_data.query_params.dict(),
            visualization_config=search_data.visualization_config.dict() if search_data.visualization_config else None,
            folder=search_data.folder,
            tags=search_data.tags,
            is_shared=search_data.is_shared,
            shared_with=search_data.shared_with
        )
        
        db.add(new_search)
        db.commit()
        db.refresh(new_search)
        
        logger.info(f"Created saved search: {new_search.name} for user: {user_id}")
        return SavedSearchResponse.from_orm(new_search)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating saved search: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create saved search")

@router.put("/{search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
    search_id: str,
    search_data: SavedSearchUpdate,
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Update an existing saved search"""
    search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == user_id
    ).first()
    
    if not search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    try:
        # Update only provided fields
        update_data = search_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "query_params" and value:
                setattr(search, field, value.dict())
            elif field == "visualization_config" and value:
                setattr(search, field, value.dict())
            else:
                setattr(search, field, value)
        
        search.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(search)
        
        logger.info(f"Updated saved search: {search.name}")
        return SavedSearchResponse.from_orm(search)
        
    except Exception as e:
        logger.error(f"Error updating saved search: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update saved search")

@router.delete("/{search_id}")
async def delete_saved_search(
    search_id: str,
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Delete a saved search"""
    search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == user_id
    ).first()
    
    if not search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    try:
        db.delete(search)
        db.commit()
        logger.info(f"Deleted saved search: {search.name}")
        return {"message": "Saved search deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting saved search: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete saved search")

@router.post("/{search_id}/execute")
async def execute_saved_search(
    search_id: str,
    user_id: str = Query("demo_user", description="User ID"),
    time_override: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """Execute a saved search with optional time range override"""
    search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == user_id
    ).first()
    
    if not search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    try:
        # Simulate search execution (integrate with actual log search service)
        query_params = search.query_params.copy()
        if time_override:
            query_params["time_range"] = time_override
        
        # Update usage statistics
        search.last_used = datetime.utcnow()
        search.usage_count += 1
        db.commit()
        
        # Mock results for demonstration
        mock_results = {
            "search_id": search_id,
            "query_params": query_params,
            "total_results": 150,
            "execution_time_ms": 45,
            "results": [
                {
                    "timestamp": "2025-01-15T10:30:00Z",
                    "service": "api-gateway",
                    "level": "ERROR",
                    "message": "Connection timeout to database",
                    "metadata": {"request_id": "req_123", "duration": 5000}
                },
                {
                    "timestamp": "2025-01-15T10:29:30Z",
                    "service": "payment-service",
                    "level": "WARN",
                    "message": "High response time detected",
                    "metadata": {"request_id": "req_124", "duration": 2000}
                }
            ]
        }
        
        return mock_results
        
    except Exception as e:
        logger.error(f"Error executing saved search: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute saved search")

@router.get("/folders/list")
async def get_folders(
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Get list of unique folders for a user"""
    try:
        folders = db.query(SavedSearch.folder).filter(
            SavedSearch.user_id == user_id
        ).distinct().all()
        
        folder_list = [folder[0] for folder in folders if folder[0]]
        return {"folders": folder_list}
        
    except Exception as e:
        logger.error(f"Error getting folders: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve folders")

@router.get("/tags/list")
async def get_tags(
    user_id: str = Query("demo_user", description="User ID"),
    db: Session = Depends(get_db)
):
    """Get list of all tags used by a user"""
    try:
        searches = db.query(SavedSearch).filter(SavedSearch.user_id == user_id).all()
        all_tags = set()
        
        for search in searches:
            if search.tags:
                all_tags.update(search.tags)
        
        return {"tags": sorted(list(all_tags))}
        
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tags")
