from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset import ApplicationAsset
from app.schemas.asset import AssetResponse, AssetUpdate

router = APIRouter(prefix="/api/jobs", tags=["assets"])


@router.get("/{job_id}/assets", response_model=list[AssetResponse])
def get_job_assets(job_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ApplicationAsset)
        .filter(ApplicationAsset.job_id == job_id)
        .all()
    )


@router.put("/{job_id}/assets/{asset_id}", response_model=AssetResponse)
def update_asset(
    job_id: int, asset_id: int, data: AssetUpdate, db: Session = Depends(get_db)
):
    asset = db.query(ApplicationAsset).get(asset_id)
    if not asset or asset.job_id != job_id:
        raise HTTPException(status_code=404, detail="Asset not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(asset, key, value)
    db.commit()
    db.refresh(asset)
    return asset


@router.post("/{job_id}/assets/{asset_id}/approve", response_model=AssetResponse)
def approve_asset(job_id: int, asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(ApplicationAsset).get(asset_id)
    if not asset or asset.job_id != job_id:
        raise HTTPException(status_code=404, detail="Asset not found")
    asset.status = "approved"
    db.commit()
    db.refresh(asset)
    return asset
