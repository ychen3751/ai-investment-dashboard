import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate

router = APIRouter()


@router.get("", response_model=List[AlertResponse])
async def list_alerts(is_active: bool = None, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(Alert).where(Alert.user_id == current_user.id)
    if is_active is not None:
        query = query.where(Alert.is_active == is_active)
    result = await db.execute(query.order_by(Alert.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(data: AlertCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    alert = Alert(
        user_id=current_user.id,
        symbol=data.symbol.upper(),
        alert_type=data.alert_type,
        condition=data.condition,
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)
    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(alert_id: uuid.UUID, data: AlertUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id))
    alert = result.scalar_one_or_none()
    if not alert:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if data.is_active is not None:
        alert.is_active = data.is_active
    if data.condition is not None:
        alert.condition = data.condition
    await db.flush()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id))
    await db.flush()
