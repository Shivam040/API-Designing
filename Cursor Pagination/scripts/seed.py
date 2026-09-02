from datetime import datetime, timedelta, timezone

from app.database import Base, SessionLocal, engine
from app.models import Event


STATUSES = ("pending", "completed", "failed")


def main() -> None:
    Base.metadata.create_all(bind=engine)

    now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        # Explicit timestamps make the sample ordering easy to inspect.
        events = [
            Event(
                status=STATUSES[i % len(STATUSES)],
                created_at=now - timedelta(minutes=i),
            )
            for i in range(30)
        ]
        db.add_all(events)
        db.commit()

    print("Seeded 30 events.")


if __name__ == "__main__":
    main()
