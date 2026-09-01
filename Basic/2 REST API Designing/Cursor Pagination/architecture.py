from typing import Annotated
from .pydantic_models import EventListResponse, EventStatus, EventResponse, PaginationResponse
from .cursor import decode_cursor, encode_cursor  
from .SQLAlcempy import list_events_from_database
from fastapi import Depends, FastAPI, Query
from sqlalchemy.orm import Session, sessionmaker

app = FastAPI()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@app.get(
    "/events",
    response_model=EventListResponse,
)
def list_events(
    db: Session = Depends(get_db),
    event_status: EventStatus | None = Query(
        default=None,
        alias="status",
    ),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> EventListResponse:
    cursor_values = (
        decode_cursor(cursor)
        if cursor is not None
        else None
    )

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
        next_cursor = encode_cursor(
            last_event.created_at,
            last_event.id,
        )

    return EventListResponse(
        data=[
            EventResponse.model_validate(event)
            for event in page_rows
        ],
        pagination=PaginationResponse(
            limit=limit,
            has_more=has_more,
            next_cursor=next_cursor,
        ),
    )