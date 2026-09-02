from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI, Query, status
from sqlalchemy.orm import Session

from .cursor import decode_cursor, encode_cursor
from .database import Base, engine, get_db
from .models import Event
from .repository import list_events_from_database
from .schemas import (
    EventCreate,
    EventListResponse,
    EventResponse,
    EventStatus,
    PaginationResponse,
)


def create_app(*, initialize_database: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if initialize_database:
            # Convenient for this standalone demo. In a larger production system,
            # migrations (for example Alembic) should own schema changes.
            Base.metadata.create_all(bind=engine)
        yield

    application = FastAPI(
        title="Cursor Pagination API",
        version="1.0.0",
        description=(
            "Standalone FastAPI example of signed keyset/cursor pagination using "
            "the composite ordering (created_at DESC, id DESC)."
        ),
        lifespan=lifespan,
    )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.post(
        "/events",
        response_model=EventResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_event(
        body: EventCreate,
        db: Session = Depends(get_db),
    ) -> Event:
        event = Event(status=body.status)
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @application.get(
        "/events",
        response_model=EventListResponse,
    )
    def list_events(
        db: Session = Depends(get_db),
        event_status: EventStatus | None = Query(default=None, alias="status"),
        limit: int = Query(default=50, ge=1, le=100),
        cursor: str | None = Query(default=None),
    ) -> EventListResponse:
        cursor_values = decode_cursor(cursor) if cursor is not None else None

        rows = list_events_from_database(
            db,
            event_status=event_status,
            limit=limit,
            cursor_values=cursor_values,
        )

        has_more = len(rows) > limit
        page_rows = rows[:limit]

        next_cursor = None
        if has_more and page_rows:
            last_event = page_rows[-1]
            next_cursor = encode_cursor(last_event.created_at, last_event.id)

        return EventListResponse(
            data=[EventResponse.model_validate(event) for event in page_rows],
            pagination=PaginationResponse(
                limit=limit,
                has_more=has_more,
                next_cursor=next_cursor,
            ),
        )

    return application


app = create_app()
