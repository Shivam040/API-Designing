from datetime import datetime

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.orm import Session

from .models import Event
from .schemas import EventStatus


def list_events_from_database(
    db: Session,
    *,
    event_status: EventStatus | None,
    limit: int,
    cursor_values: tuple[datetime, int] | None,
) -> list[Event]:
    """Return limit+1 rows so the API can determine whether another page exists."""
    query = select(Event)

    if event_status is not None:
        query = query.where(Event.status == event_status)

    if cursor_values is not None:
        cursor_created_at, cursor_id = cursor_values
        query = query.where(
            or_(
                Event.created_at < cursor_created_at,
                and_(
                    Event.created_at == cursor_created_at,
                    Event.id < cursor_id,
                ),
            )
        )

    query = query.order_by(
        desc(Event.created_at),
        desc(Event.id),
    ).limit(limit + 1)

    return list(db.scalars(query).all())
