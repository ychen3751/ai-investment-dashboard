from app.db.session import async_session_factory
from app.services import macro_service


async def update_macro_data():
    """Update market indices, sector performance."""
    async with async_session_factory() as db:
        try:
            await macro_service.update_indices(db)
            await macro_service.update_sectors(db)
            await db.commit()
        except Exception:
            await db.rollback()
