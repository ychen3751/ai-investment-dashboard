import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.watchlist import Watchlist, WatchlistItem
from app.schemas.watchlist import WatchlistCreate, WatchlistResponse, WatchlistItemResponse, WatchlistItemCreate
from app.services import market_data_service, watchlist_signals_service

router = APIRouter()


@router.get("", response_model=List[WatchlistResponse])
async def list_watchlists(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Watchlist).where(Watchlist.user_id == current_user.id).options(selectinload(Watchlist.items))
    )
    watchlists = result.scalars().all()
    responses = []
    for w in watchlists:
        items = []
        for item in w.items:
            quote = await market_data_service.get_quote(item.symbol)
            items.append(WatchlistItemResponse(
                id=item.id, symbol=item.symbol, notes=item.notes, added_at=item.added_at,
                current_price=float(quote["price"]) if quote and quote.get("price") else None,
                change=float(quote["change"]) if quote and quote.get("change") else None,
                change_pct=float(quote["change_pct"]) if quote and quote.get("change_pct") else None,
            ))
        responses.append(WatchlistResponse(
            id=w.id, name=w.name, created_at=w.created_at,
            item_count=len(items), items=items,
        ))
    return responses


@router.post("", response_model=WatchlistResponse, status_code=201)
async def create_watchlist(data: WatchlistCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    w = Watchlist(user_id=current_user.id, name=data.name)
    db.add(w)
    await db.flush()
    await db.refresh(w)
    return WatchlistResponse(id=w.id, name=w.name, created_at=w.created_at)


@router.delete("/{watchlist_id}", status_code=204)
async def delete_watchlist(watchlist_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Watchlist).where(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id))
    await db.flush()


@router.post("/{watchlist_id}/items", response_model=WatchlistItemResponse, status_code=201)
async def add_item(watchlist_id: uuid.UUID, data: WatchlistItemCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = WatchlistItem(watchlist_id=watchlist_id, symbol=data.symbol.upper(), notes=data.notes)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    await market_data_service.add_tracked_symbol(data.symbol.upper())
    return WatchlistItemResponse(id=item.id, symbol=item.symbol, notes=item.notes, added_at=item.added_at)


@router.delete("/{watchlist_id}/items/{item_id}", status_code=204)
async def remove_item(watchlist_id: uuid.UUID, item_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(WatchlistItem).where(WatchlistItem.id == item_id, WatchlistItem.watchlist_id == watchlist_id))
    await db.flush()


@router.get("/signals/all")
async def get_all_signals(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """AI watchlist signals for all unique symbols across user's watchlists."""
    result = await db.execute(
        select(Watchlist).where(Watchlist.user_id == current_user.id).options(selectinload(Watchlist.items))
    )
    watchlists = result.scalars().all()
    symbols = list(set(item.symbol for wl in watchlists for item in wl.items))
    if not symbols:
        return []
    return await watchlist_signals_service.get_signals(symbols)
