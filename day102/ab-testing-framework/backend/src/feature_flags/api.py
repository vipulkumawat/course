from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from config.database import get_db
from .service import feature_flag_service
from .models import FeatureFlag, Experiment
from pydantic import BaseModel

router = APIRouter(prefix="/api/feature-flags", tags=["feature-flags"])

class FeatureFlagRequest(BaseModel):
    flag_name: str
    user_id: str
    user_attributes: Dict[str, Any] = {}

class ExperimentAssignmentRequest(BaseModel):
    user_id: str
    experiment_id: int

@router.post("/evaluate")
async def evaluate_feature_flag(request: FeatureFlagRequest):
    """Evaluate feature flag for user"""
    try:
        is_enabled = await feature_flag_service.evaluate_feature_flag(
            request.flag_name,
            request.user_id,
            request.user_attributes
        )
        
        return {
            "flag_name": request.flag_name,
            "user_id": request.user_id,
            "is_enabled": is_enabled,
            "variant": "treatment" if is_enabled else "control"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assign")
async def assign_to_experiment(request: ExperimentAssignmentRequest, 
                             db: Session = Depends(get_db)):
    """Assign user to experiment variant"""
    try:
        variant = await feature_flag_service.assign_user_to_experiment(
            request.user_id,
            request.experiment_id,
            db
        )
        
        return {
            "user_id": request.user_id,
            "experiment_id": request.experiment_id,
            "variant": variant
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/experiments/{experiment_id}/results")
async def get_experiment_results(experiment_id: int, db: Session = Depends(get_db)):
    """Get experiment results"""
    try:
        results = await feature_flag_service.get_experiment_results(experiment_id, db)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/flags")
async def list_feature_flags(db: Session = Depends(get_db)):
    """List all feature flags"""
    flags = db.query(FeatureFlag).all()
    return [
        {
            "id": flag.id,
            "name": flag.name,
            "description": flag.description,
            "is_enabled": flag.is_enabled,
            "rollout_percentage": flag.rollout_percentage
        }
        for flag in flags
    ]
