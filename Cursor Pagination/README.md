# Cursor Pagination — Complete FastAPI Learning Project

This is a **standalone FastAPI project** that demonstrates how to build reliable **cursor/keyset pagination** using:

- **FastAPI** — HTTP API framework
- **SQLAlchemy 2.0** — database ORM/query layer
- **Pydantic v2** — request/response validation
- **SQLite** — local database
- **HMAC-SHA256** — cursor tamper detection
- **Pytest** — automated testing

The project is intentionally small enough to understand completely, but the same ideas are used in production APIs that need to paginate large or frequently changing datasets.

---

# 1. What problem are we solving?

Imagine the database contains thousands or millions of events and a client asks:

```http
GET /events?limit=3
```

We do **not** want to send every event in one response. Instead, we send a small page:

```text
Page 1
------
Event 10
Event 9
Event 8
```

The client then asks for the next page:

```text
Page 2
------
Event 7
Event 6
Event 5
```

There are two common ways to implement this.

## Offset pagination

```sql
SELECT *
FROM events
ORDER BY created_at DESC
LIMIT 3 OFFSET 6;
```

This corresponds to page-number style pagination such as:

```http
/events?page=3&page_size=3
```

Offset pagination is easy to understand, but it has problems when the table becomes large or when rows are inserted/deleted while a user is paging through the results.

## Cursor/keyset pagination

Instead of remembering a page number, we remember the position of the **last record returned**.

For this project the ordering is:

```text
created_at DESC, id DESC
```

So our cursor represents:

```text
(last_created_at, last_id)
```

If Page 1 finishes with:

```text
created_at = 2026-09-01 12:05:00
id         = 8
```

then Page 2 asks the database for records that come **after that position in the ordered result set**.

That is the central idea behind this entire project.

---

# 2. Why cursor pagination instead of OFFSET?

Suppose these rows exist:

```text
ID    created_at
10    12:10
9     12:09
8     12:08
7     12:07
6     12:06
5     12:05
```

The first request returns:

```text
10, 9, 8
```

Now imagine a new record is inserted at the top before the user requests Page 2:

```text
11    12:11   <- newly inserted
10    12:10
9     12:09
8     12:08
7     12:07
6     12:06
```

With an OFFSET-based query, the positions shifted. Depending on the timing, a record may be repeated or skipped.

With cursor pagination, Page 2 says:

> Give me records strictly older than `(12:08, id=8)`.

The newly inserted Event 11 does not change that boundary.

Cursor pagination is therefore especially useful for:

- activity feeds
- audit logs
- notifications
- transaction history
- chat messages
- events/telemetry
- social feeds
- APIs with large datasets
- continuously changing tables

---

# 3. Project structure

```text
Cursor-Pagination-Standalone/
├── app/
│   ├── __init__.py
│   ├── cursor.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── repository.py
│   └── schemas.py
│
├── scripts/
│   ├── __init__.py
│   └── seed.py
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_cursor.py
│
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

Think of the layers like this:

```text
Client / Browser
      |
      v
   main.py             <- HTTP/FastAPI layer
      |
      v
  schemas.py           <- validation and response shapes
      |
      v
 repository.py         <- database query logic
      |
      v
  models.py            <- database table definition
      |
      v
 database.py           <- engine + sessions
      |
      v
   SQLite

Cursor handling is separated into:

 main.py
    |
    +----> cursor.py   <- encode/decode/verify cursor
```

This separation is useful because each file has one main responsibility.

---

# 4. Installation and running the project

## Step 1 — Create a virtual environment

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Git Bash on Windows

```bash
python -m venv .venv
source .venv/Scripts/activate
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

## Step 3 — Set the cursor secret

For local development the application has a fallback secret, but deployed environments should set their own secret.

### PowerShell

```powershell
$env:CURSOR_SECRET="replace-this-with-a-long-random-secret"
```

### Git Bash/macOS/Linux

```bash
export CURSOR_SECRET="replace-this-with-a-long-random-secret"
```

## Step 4 — Seed sample data

Optional, but useful for testing pagination manually:

```bash
python -m scripts.seed
```

It creates 30 events.

## Step 5 — Start FastAPI

```bash
uvicorn app.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

OpenAPI JSON:

```text
http://127.0.0.1:8000/openapi.json
```

## Step 6 — Run tests

```bash
pytest -q
```

Expected result:

```text
..........                                                       [100%]
10 passed
```

---

# 5. Dependencies — what are we using and why?

`requirements.txt` contains:

```text
fastapi
uvicorn[standard]
SQLAlchemy
pydantic
httpx
pytest
```

## FastAPI

Provides routes such as:

```python
@app.get("/events")
```

It also automatically performs query/body validation and generates Swagger documentation.

## Uvicorn

FastAPI defines the application, but it still needs an ASGI web server to actually listen for HTTP requests.

Uvicorn does that:

```bash
uvicorn app.main:app --reload
```

Here:

```text
app.main
```

means:

```text
app/main.py
```

and:

```text
:app
```

means:

```python
app = create_app()
```

## SQLAlchemy

SQLAlchemy handles:

- database connections
- table models
- SQL query construction
- inserts
- selects
- sessions/transactions

Instead of manually writing all SQL, we can write Python expressions such as:

```python
select(Event)
```

## Pydantic

Pydantic validates external data.

For example:

```python
EventStatus = Literal["pending", "completed", "failed"]
```

means FastAPI/Pydantic will reject:

```json
{
  "status": "banana"
}
```

## HTTPX

FastAPI's `TestClient` uses HTTPX. It lets the automated tests call the API like a real HTTP client without starting a separate server process.

## Pytest

Runs automated tests and confirms pagination keeps working when code changes.

---

# 6. `app/database.py` — database connection and sessions

This file creates the connection between Python and the database.

## Database URL

```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./events.db")
```

First Python checks for an environment variable named:

```text
DATABASE_URL
```

If none exists, it uses:

```text
sqlite:///./events.db
```

which means:

> Use SQLite and store the database in a local file called `events.db`.

This is convenient because the project runs without installing PostgreSQL/MySQL.

In production you could change only the environment variable and use another supported database.

---

## SQLite `check_same_thread`

```python
connect_args = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)
```

SQLite normally restricts a connection to the thread that created it.

FastAPI may execute requests using different worker threads, so for this local FastAPI/SQLite setup we disable that restriction.

This setting is specific to SQLite.

---

## Engine

```python
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    future=True,
)
```

The SQLAlchemy **engine** manages communication with the database.

You can think of it as the database connection factory/infrastructure.

It does not represent one individual API request.

---

## Session factory

```python
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)
```

A SQLAlchemy `Session` represents a unit of database work.

For example one API request may:

```text
open session
   -> query database
   -> insert/update
   -> commit
close session
```

`SessionLocal` is a factory used to create those sessions.

### `autocommit=False`

Changes are not automatically committed.

We explicitly do:

```python
db.commit()
```

This makes transaction boundaries clear.

### `autoflush=False`

SQLAlchemy does not automatically flush pending changes at every possible opportunity.

### `expire_on_commit=False`

After `commit()`, SQLAlchemy keeps already-loaded attributes available on the Python object.

That is convenient for API responses.

---

## Declarative Base

```python
class Base(DeclarativeBase):
    pass
```

All SQLAlchemy ORM models inherit from this base.

For example:

```python
class Event(Base):
```

SQLAlchemy then knows `Event` belongs to its ORM metadata.

Later:

```python
Base.metadata.create_all(bind=engine)
```

can create all registered tables.

---

## FastAPI dependency: `get_db()`

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

This is one of the most important FastAPI patterns in the project.

A route declares:

```python
db: Session = Depends(get_db)
```

FastAPI then effectively does:

```text
1. Call get_db()
2. Create database session
3. Give session to route
4. Execute route
5. Run finally block
6. Close session
```

Why do this?

Because database connections/sessions must be cleaned up reliably even if an exception occurs.

---

# 7. `app/models.py` — database table definition

The `Event` class represents the `events` SQL table.

```python
class Event(Base):
    __tablename__ = "events"
```

So SQLAlchemy maps Python `Event` objects to rows in:

```text
events
```

---

## Status constraint

```python
CheckConstraint(
    "status IN ('pending', 'completed', 'failed')",
    name="ck_events_status",
)
```

This gives us validation at the **database level**.

Even though Pydantic already validates API input, database constraints are still useful because data may someday be inserted through:

- another service
- an admin script
- migrations
- direct SQL
- background jobs

So we use multiple layers of protection.

---

## Primary key

```python
id: Mapped[int] = mapped_column(
    Integer,
    primary_key=True,
    autoincrement=True,
)
```

Each event gets a unique integer ID.

Example:

```text
1
2
3
4
...
```

The ID is also important for pagination because it acts as our **tie-breaker** when two rows have the same timestamp.

---

## Status column

```python
status: Mapped[str] = mapped_column(
    String(20),
    nullable=False,
    index=True,
)
```

`nullable=False` means every event must have a status.

`index=True` asks SQLAlchemy to create an index because we filter using:

```http
/events?status=pending
```

Indexes help the database locate relevant records more efficiently.

---

## `created_at`

```python
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    nullable=False,
    index=True,
    default=lambda: datetime.now(timezone.utc),
)
```

When an event is created without specifying a timestamp, it receives the current UTC time.

Why UTC?

Because servers and clients may operate in different time zones. Storing timestamps in UTC gives us one consistent ordering system.

We order pagination by:

```text
created_at DESC
```

meaning newest first.

---

# 8. Why do we sort by BOTH `created_at` and `id`?

This is essential.

A tempting query is:

```sql
ORDER BY created_at DESC
```

But timestamps are not guaranteed to be unique.

Imagine:

```text
ID    created_at
5     12:00:00
4     12:00:00
3     12:00:00
2     11:59:00
```

If our cursor only says:

```text
created_at = 12:00:00
```

the database cannot know precisely whether Page 1 ended at ID 5, ID 4, or ID 3.

So we use a deterministic composite ordering:

```sql
ORDER BY created_at DESC, id DESC
```

Now the exact order is:

```text
(12:00:00, 5)
(12:00:00, 4)
(12:00:00, 3)
(11:59:00, 2)
```

Every row has an exact location in the ordered result set.

That is why the cursor stores both:

```text
created_at
id
```

---

# 9. `app/schemas.py` — API validation and response contracts

Database models describe database rows.

Pydantic schemas describe what the API accepts and returns.

Keeping these responsibilities separate is a common backend design pattern.

---

## Event status type

```python
EventStatus = Literal[
    "pending",
    "completed",
    "failed",
]
```

Only these exact strings are accepted.

FastAPI therefore rejects invalid input automatically with HTTP `422`.

---

## Create request

```python
class EventCreate(BaseModel):
    status: EventStatus = "pending"
```

This describes the JSON body for:

```http
POST /events
```

Example:

```json
{
  "status": "completed"
}
```

If the client sends no status, it defaults to:

```text
pending
```

---

## Event response

```python
class EventResponse(BaseModel):
    id: int
    status: EventStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

The important part is:

```python
from_attributes=True
```

A SQLAlchemy model is not a plain dictionary.

It has attributes:

```python
event.id
event.status
event.created_at
```

`from_attributes=True` tells Pydantic:

> You may build this schema by reading attributes from an ORM object.

That allows:

```python
EventResponse.model_validate(event)
```

---

## Pagination response

```python
class PaginationResponse(BaseModel):
    limit: int
    has_more: bool
    next_cursor: str | None
```

Example:

```json
{
  "limit": 5,
  "has_more": true,
  "next_cursor": "eyJ..."
}
```

### `limit`

How many records the client requested.

### `has_more`

Whether at least one additional record exists after this page.

### `next_cursor`

The opaque cursor that should be sent unchanged in the next request.

If there is no next page:

```json
{
  "has_more": false,
  "next_cursor": null
}
```

---

## Complete list response

```python
class EventListResponse(BaseModel):
    data: list[EventResponse]
    pagination: PaginationResponse
```

So `/events` returns a predictable structure:

```json
{
  "data": [...],
  "pagination": {...}
}
```

This is better than returning only an array because pagination metadata has a clear place to live.

---

# 10. `app/cursor.py` — the cursor system

This file converts:

```text
(created_at, id)
```

into an opaque string and converts it back safely.

This is the most security-sensitive part of the example.

---

# 11. What is inside a cursor?

Internally the payload is conceptually:

```json
{
  "created_at": "2026-09-01T12:05:00+00:00",
  "id": 8
}
```

But we do not want clients manually constructing and changing it.

So the application:

```text
JSON payload
    |
    v
Base64URL encode
    |
    +----> HMAC-SHA256 signature
    |
    v
payload.signature
```

The final result looks similar to:

```text
eyJjcmVhdGVkX2F0IjoiLi4uIiwiaWQiOjh9.L1h...
```

Clients should treat that string as opaque.

They do not need to understand it.

They only need to send it back unchanged.

---

# 12. Is Base64 encryption?

No.

Base64 is only an **encoding**.

It makes binary/text data safe to transport in URLs and JSON.

Someone can decode Base64.

What prevents cursor tampering is the **HMAC signature**, not Base64.

This project makes the cursor:

- opaque from the API user's perspective
- URL-safe
- tamper-evident

It does **not** attempt to make the timestamp/ID cryptographically secret.

If cursor contents must also be confidential, encryption would be a different requirement.

---

# 13. The secret key

```python
DEFAULT_DEVELOPMENT_SECRET = "development-only-change-me"
```

and:

```python
def _secret() -> bytes:
    return os.getenv(
        "CURSOR_SECRET",
        DEFAULT_DEVELOPMENT_SECRET,
    ).encode("utf-8")
```

HMAC requires a secret known by the server.

Production should set:

```text
CURSOR_SECRET
```

through environment/secrets management.

Why not hard-code the production secret in Git?

Because anyone with repository access would then possess the signing key and could create apparently valid cursors.

---

# 14. Base64URL helpers

## Encoding

```python
def _b64encode(data: bytes) -> str:
    return (
        base64.urlsafe_b64encode(data)
        .rstrip(b"=")
        .decode("ascii")
    )
```

We use **URL-safe Base64** because cursors are sent in query parameters.

Normal Base64 may contain characters such as:

```text
+
/
```

Base64URL uses URL-friendlier replacements.

Padding `=` is removed to make the cursor shorter and cleaner.

---

## Decoding

```python
padding = "=" * (-len(value) % 4)
```

Because encoding removed the padding, decoding reconstructs it.

Then:

```python
base64.b64decode(..., validate=True)
```

rejects malformed Base64 rather than silently accepting bad data.

---

# 15. Why `_to_utc()`?

```python
def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
```

A cursor must describe one unambiguous moment.

If one timestamp is stored in IST and another in UTC, comparisons become harder to reason about.

So cursor timestamps are normalized to UTC.

---

# 16. `encode_cursor()` step by step

Function:

```python
encode_cursor(created_at, event_id)
```

### Step 1 — Build payload

```python
payload = {
    "created_at": _to_utc(created_at).isoformat(),
    "id": int(event_id),
}
```

Example:

```json
{
  "created_at": "2026-09-01T12:00:00+00:00",
  "id": 42
}
```

---

### Step 2 — Convert JSON to bytes

```python
payload_bytes = json.dumps(
    payload,
    separators=(",", ":"),
    sort_keys=True,
).encode("utf-8")
```

`separators` removes unnecessary spaces.

`sort_keys=True` makes serialization deterministic.

Deterministic input is useful for signatures because the same logical payload should produce the same serialized representation.

---

### Step 3 — Base64URL encode the payload

```python
encoded_payload = _b64encode(payload_bytes)
```

Now the payload is URL-safe text.

---

### Step 4 — Sign it

```python
signature = hmac.new(
    _secret(),
    encoded_payload.encode("ascii"),
    hashlib.sha256,
).digest()
```

The server computes:

```text
HMAC-SHA256(secret, encoded_payload)
```

Without the secret, a client should not be able to modify the payload and generate the correct signature.

---

### Step 5 — Base64URL encode the signature

```python
encoded_signature = _b64encode(signature)
```

HMAC output is arbitrary binary bytes, so it must also be encoded before putting it in a URL.

---

### Step 6 — Join the two safe strings

```python
return f"{encoded_payload}.{encoded_signature}"
```

Result:

```text
payload.signature
```

The `.` separator is safe because Base64URL's alphabet does not contain `.`.

---

# 17. Why the original raw-HMAC approach was dangerous

An incorrect implementation may do something conceptually like:

```python
token = payload_bytes + b"." + raw_hmac_bytes
```

and later:

```python
payload, signature = token.rsplit(b".", 1)
```

The problem is that a SHA-256 HMAC is **arbitrary binary data**.

One of its bytes can itself equal:

```python
b"."
```

Then the decoder can split at the wrong location even though the cursor is valid.

This project avoids that bug by doing:

```text
Base64(payload) + "." + Base64(signature)
```

Both sides are text-safe before they are joined.

The automated tests perform **5,000 cursor round trips** specifically to protect against regression of that bug.

---

# 18. `decode_cursor()` step by step

When the client requests:

```http
GET /events?cursor=<cursor>
```

FastAPI calls:

```python
decode_cursor(cursor)
```

---

## Step 1 — Ensure the structure is correct

```python
parts = cursor.split(".")
if len(parts) != 2 or not all(parts):
    raise ValueError("Malformed cursor")
```

A valid cursor must contain exactly:

```text
payload.signature
```

---

## Step 2 — Decode the signature

```python
signature = _b64decode(encoded_signature)
```

---

## Step 3 — Recompute what the signature SHOULD be

```python
expected_signature = hmac.new(
    _secret(),
    encoded_payload.encode("ascii"),
    hashlib.sha256,
).digest()
```

---

## Step 4 — Compare signatures securely

```python
if not hmac.compare_digest(
    signature,
    expected_signature,
):
    raise ValueError(...)
```

We use:

```python
hmac.compare_digest()
```

rather than ordinary:

```python
signature == expected_signature
```

because `compare_digest()` is specifically designed for cryptographic comparison and reduces timing side-channel information.

If the client changes even one signed payload character, verification fails.

---

## Step 5 — Decode JSON

```python
payload_bytes = _b64decode(encoded_payload)
payload = json.loads(payload_bytes.decode("utf-8"))
```

---

## Step 6 — Strictly validate payload contents

The code checks that the payload contains exactly:

```text
created_at
id
```

and checks their types.

For example:

```python
if set(payload) != {"created_at", "id"}:
    raise ValueError(...)
```

Why validate something that was signed?

Because robust boundary code should verify all assumptions. It also protects against malformed tokens created under old versions, bugs, or unexpected internal usage.

---

## Step 7 — Return usable values

Finally:

```python
return (
    created_at.astimezone(timezone.utc),
    payload["id"],
)
```

The repository can now use:

```text
(cursor_created_at, cursor_id)
```

in its SQL query.

---

# 19. Why invalid cursors return HTTP 400

All cursor parsing errors become:

```python
HTTPException(
    status_code=400,
    detail="Invalid pagination cursor",
)
```

HTTP `400 Bad Request` means:

> The client's request contains an invalid value.

We intentionally do not expose detailed cryptographic/parser errors such as:

```text
signature mismatch at byte ...
```

The API gives a stable public error message instead.

---

# 20. `app/repository.py` — where the pagination query happens

The repository isolates database query logic from the HTTP route.

Function:

```python
list_events_from_database(...)
```

accepts:

```text
db
status filter
limit
cursor values
```

and returns SQLAlchemy `Event` rows.

---

# 21. Initial SQL query

```python
query = select(Event)
```

Conceptually:

```sql
SELECT * FROM events
```

We then progressively add filters, cursor conditions, ordering, and a limit.

This composition style is one of SQLAlchemy's strengths.

---

# 22. Status filtering

```python
if event_status is not None:
    query = query.where(
        Event.status == event_status
    )
```

For:

```http
GET /events?status=pending
```

we effectively add:

```sql
WHERE status = 'pending'
```

---

# 23. The most important pagination condition

For descending order we use:

```python
or_(
    Event.created_at < cursor_created_at,
    and_(
        Event.created_at == cursor_created_at,
        Event.id < cursor_id,
    ),
)
```

Conceptually:

```sql
WHERE
    created_at < :cursor_created_at
    OR (
        created_at = :cursor_created_at
        AND id < :cursor_id
    )
```

Why exactly this condition?

Because the sort order is:

```sql
ORDER BY created_at DESC, id DESC
```

We want everything that appears **after the cursor** in that ordering.

---

# 24. Deriving the cursor condition with an example

Suppose rows are:

```text
created_at    id
12:05         10
12:05          9
12:05          8
12:04         20
12:03         30
```

Page 1 returns:

```text
(12:05, 10)
(12:05,  9)
```

So the cursor is:

```text
(12:05, 9)
```

What should come next?

First, rows with an **older timestamp**:

```text
created_at < 12:05
```

That gives:

```text
(12:04, 20)
(12:03, 30)
```

But we also need rows with the **same timestamp** that have a smaller ID:

```text
created_at = 12:05
AND id < 9
```

That gives:

```text
(12:05, 8)
```

Combining them:

```text
created_at < cursor_created_at
OR
(created_at = cursor_created_at AND id < cursor_id)
```

returns precisely the records after `(12:05,9)`.

---

# 25. Why `<` and not `<=`?

If we used:

```text
id <= cursor_id
```

then the last event from Page 1 would satisfy the Page 2 query again.

That would produce duplicates.

So the boundary must be **strictly after** the last returned item:

```text
<
```

not:

```text
<=
```

for this descending ordering.

---

# 26. Ordering

```python
query = query.order_by(
    desc(Event.created_at),
    desc(Event.id),
)
```

This must match the fields represented in the cursor.

Do not generate a cursor based on `(created_at, id)` and then later sort only by `status`, for example. The cursor only makes sense relative to its ordering contract.

---

# 27. Why query `limit + 1` records?

```python
.limit(limit + 1)
```

Suppose the client requests:

```text
limit = 3
```

Instead of querying exactly 3 rows, we ask for:

```text
4 rows
```

Why?

Because we want to know whether a fourth record exists.

### Database returns only 3

```text
A
B
C
```

Then:

```text
has_more = false
```

### Database returns 4

```text
A
B
C
D
```

We return only:

```text
A
B
C
```

but the presence of `D` tells us:

```text
has_more = true
```

This avoids performing a separate:

```sql
COUNT(*)
```

query for every page.

That is a simple and efficient technique.

---

# 28. Why not return the extra row?

Because the client requested a limit.

If:

```text
limit = 3
```

the API must return at most 3 data records.

The extra record exists only as an internal look-ahead signal.

---

# 29. Executing the query

```python
return list(db.scalars(query).all())
```

`db.scalars(query)` tells SQLAlchemy:

> Give me the ORM `Event` objects rather than full SQL row wrapper objects.

`.all()` executes/fetches all rows permitted by our small `limit + 1` query.

---

# 30. `app/main.py` — FastAPI application and routes

This file connects all of the layers together.

It imports:

```text
cursor functions
database dependencies
ORM model
repository
Pydantic schemas
```

This is the orchestration layer.

---

# 31. Application factory: `create_app()`

```python
def create_app(
    *,
    initialize_database: bool = True,
) -> FastAPI:
```

Instead of immediately defining only one global application, we wrap app creation in a function.

Why?

It makes testing easier.

Production/local usage can do:

```python
app = create_app()
```

Tests can do:

```python
create_app(initialize_database=False)
```

and control their own isolated test database.

This is called the **application factory pattern**.

---

# 32. Lifespan startup

```python
@asynccontextmanager
async def lifespan(...):
    if initialize_database:
        Base.metadata.create_all(bind=engine)
    yield
```

When FastAPI starts, this demo automatically creates missing database tables.

That is convenient for a standalone educational project.

For a serious production system, database schema evolution should usually be handled by migrations such as **Alembic** rather than `create_all()`.

---

# 33. Creating the FastAPI object

```python
application = FastAPI(
    title="Cursor Pagination API",
    version="1.0.0",
    description=...,
    lifespan=lifespan,
)
```

These values appear in generated API documentation.

---

# 34. Health endpoint

```python
@application.get("/health")
def health():
    return {"status": "ok"}
```

Used to verify that the application process is alive.

Request:

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

In deployed systems, health endpoints may also be used by:

- Docker
- Kubernetes
- load balancers
- monitoring systems

---

# 35. POST `/events` — creating data

Route:

```python
@application.post(
    "/events",
    response_model=EventResponse,
    status_code=201,
)
```

### `response_model=EventResponse`

FastAPI validates/serializes the returned object according to our public response schema.

### `201 Created`

HTTP 201 communicates that a new resource was successfully created.

---

## Request body

```python
body: EventCreate
```

FastAPI reads JSON and validates it using Pydantic.

For example:

```json
{
  "status": "pending"
}
```

becomes an `EventCreate` Python object.

---

## Database dependency

```python
db: Session = Depends(get_db)
```

FastAPI obtains a session using `get_db()` and guarantees cleanup afterward.

---

## Build ORM object

```python
event = Event(status=body.status)
```

We do not manually supply:

```text
id
created_at
```

because those are server/database-managed.

---

## Add

```python
db.add(event)
```

This tells SQLAlchemy the object should be inserted.

It is not necessarily committed yet.

---

## Commit

```python
db.commit()
```

This commits the transaction.

Now the insert is persisted.

---

## Refresh

```python
db.refresh(event)
```

The database generated values such as:

```text
id
created_at
```

`refresh()` reloads the ORM object so those values are available for the response.

---

# 36. GET `/events` — complete pagination flow

This is the core endpoint.

```python
@application.get(
    "/events",
    response_model=EventListResponse,
)
```

It accepts:

```text
status
limit
cursor
```

---

# 37. Query parameters

## Status

```python
event_status: EventStatus | None = Query(
    default=None,
    alias="status",
)
```

The Python variable is named:

```text
event_status
```

but API clients use:

```http
?status=pending
```

The alias keeps the API clean while avoiding naming ambiguity inside the route.

---

## Limit

```python
limit: int = Query(
    default=50,
    ge=1,
    le=100,
)
```

Rules:

```text
default = 50
minimum = 1
maximum = 100
```

Why cap the maximum?

Without a cap, a client could request something like:

```http
?limit=10000000
```

which defeats pagination and may consume excessive memory/database resources.

FastAPI automatically rejects invalid limits with HTTP `422`.

---

## Cursor

```python
cursor: str | None = Query(default=None)
```

For the first page there is no cursor:

```http
GET /events?limit=5
```

For later pages:

```http
GET /events?limit=5&cursor=<opaque-token>
```

---

# 38. Decode only when a cursor exists

```python
cursor_values = (
    decode_cursor(cursor)
    if cursor is not None
    else None
)
```

### First page

```text
cursor_values = None
```

So no cursor boundary is added to SQL.

### Later page

```text
cursor_values = (created_at, id)
```

The repository adds the keyset boundary.

---

# 39. Ask the repository for rows

```python
rows = list_events_from_database(
    db,
    event_status=event_status,
    limit=limit,
    cursor_values=cursor_values,
)
```

Remember: repository intentionally returns at most:

```text
limit + 1
```

rows.

---

# 40. Determine `has_more`

```python
has_more = len(rows) > limit
```

If the client requested 5 and repository returns 6:

```text
has_more = true
```

If repository returns 5 or fewer:

```text
has_more = false
```

---

# 41. Remove the look-ahead row

```python
page_rows = rows[:limit]
```

For:

```text
limit = 5
```

we only return the first five records even if six were fetched internally.

---

# 42. Generate the next cursor

```python
next_cursor = None
```

Then:

```python
if has_more and page_rows:
    last_event = page_rows[-1]
    next_cursor = encode_cursor(
        last_event.created_at,
        last_event.id,
    )
```

This is extremely important:

> The cursor is generated from the **last record actually returned to the client**, not the extra look-ahead row.

Suppose database gave:

```text
10
9
8
7   <- look-ahead
```

with `limit=3`.

Client receives:

```text
10
9
8
```

So cursor must represent:

```text
8
```

not:

```text
7
```

Otherwise Event 7 would be skipped.

---

# 43. Why is `next_cursor` null on the last page?

If there are no more rows:

```text
has_more = false
```

then there is no reason for the client to make another request.

So response is:

```json
{
  "has_more": false,
  "next_cursor": null
}
```

This makes client logic straightforward.

---

# 44. Converting ORM rows to response schemas

```python
EventResponse.model_validate(event)
```

is run for each returned SQLAlchemy event.

Then the route creates:

```python
EventListResponse(
    data=[...],
    pagination=PaginationResponse(...),
)
```

FastAPI serializes that into JSON.

---

# 45. Complete request flow — Page 1

Client sends:

```http
GET /events?limit=3
```

Internal flow:

```text
1. FastAPI receives request
       |
2. validates limit
       |
3. get_db() creates SQLAlchemy session
       |
4. cursor is None
       |
5. repository builds query
       |
       |  ORDER BY created_at DESC, id DESC
       |  LIMIT 4
       |
6. database returns up to 4 rows
       |
7. API sees whether row #4 exists
       |
8. return first 3 rows
       |
9. create cursor from row #3
       |
10. Pydantic serializes response
       |
11. get_db() closes session
```

Example response:

```json
{
  "data": [
    {"id": 10, "status": "pending", "created_at": "..."},
    {"id": 9,  "status": "failed",  "created_at": "..."},
    {"id": 8,  "status": "pending", "created_at": "..."}
  ],
  "pagination": {
    "limit": 3,
    "has_more": true,
    "next_cursor": "<cursor-for-event-8>"
  }
}
```

---

# 46. Complete request flow — Page 2

Client takes `next_cursor` exactly as returned:

```http
GET /events?limit=3&cursor=<cursor-for-event-8>
```

Internal flow:

```text
1. FastAPI receives cursor string
       |
2. decode_cursor()
       |
3. verify HMAC signature
       |
4. recover (created_at_of_8, id=8)
       |
5. repository adds boundary
       |
       | created_at < event8.created_at
       | OR
       | created_at = event8.created_at AND id < 8
       |
6. order descending
       |
7. fetch limit + 1
       |
8. return next page
```

The server does not need to store per-user pagination state.

The cursor itself carries the boundary information and the HMAC proves it was issued by someone who knows the server secret.

That is one reason cursor pagination scales nicely for APIs.

---

# 47. A concrete three-page example

Assume ordered events are:

```text
7
6
5
4
3
2
1
```

and:

```text
limit = 3
```

## Request 1

```http
GET /events?limit=3
```

Database internally fetches:

```text
7, 6, 5, 4
```

API returns:

```text
7, 6, 5
```

and:

```text
has_more = true
cursor = position of 5
```

## Request 2

```http
GET /events?limit=3&cursor=<position-of-5>
```

Database fetches:

```text
4, 3, 2, 1
```

API returns:

```text
4, 3, 2
```

and:

```text
has_more = true
cursor = position of 2
```

## Request 3

```http
GET /events?limit=3&cursor=<position-of-2>
```

Database fetches:

```text
1
```

API returns:

```text
1
```

and:

```text
has_more = false
next_cursor = null
```

Final client sequence:

```text
7, 6, 5, 4, 3, 2, 1
```

No duplicates.

No missing rows.

---

# 48. Filtering and cursors

The API supports:

```http
GET /events?status=pending&limit=5
```

The cursor produced by that request represents a boundary inside the **pending result set**.

So Page 2 should keep the same filter:

```http
GET /events?status=pending&limit=5&cursor=<cursor>
```

If the user changes the filter to:

```text
completed
```

start from the beginning:

```http
GET /events?status=completed&limit=5
```

Do **not** reuse a cursor from a different filter.

Why?

A cursor is meaningful only relative to the query/order that produced it.

A simple frontend rule is:

> Whenever sorting or filtering changes, clear the existing cursor and request the first page again.

---

# 49. `scripts/seed.py` — sample data

The seed script is not required for the API itself.

It exists to make manual testing easy.

```python
STATUSES = (
    "pending",
    "completed",
    "failed",
)
```

It creates 30 events with timestamps one minute apart:

```python
created_at = now - timedelta(minutes=i)
```

This makes the ordering easy to inspect visually in Swagger.

Run:

```bash
python -m scripts.seed
```

Then:

```http
GET /events?limit=5
```

and repeatedly copy `next_cursor` into the next request.

---

# 50. `tests/conftest.py` — isolated test database

We do not want tests modifying your real:

```text
events.db
```

So tests create a separate in-memory SQLite database:

```python
TEST_DATABASE_URL = "sqlite://"
```

---

## Why `StaticPool`?

An in-memory SQLite database normally belongs to a particular connection.

Tests and FastAPI may otherwise receive different connections and therefore appear to see different empty in-memory databases.

```python
poolclass=StaticPool
```

makes the test setup reuse the same underlying connection context so the fixtures and API can see the same test data.

---

# 51. Dependency override in tests

Production route uses:

```python
Depends(get_db)
```

Tests replace that dependency:

```python
app.dependency_overrides[get_db] = override_get_db
```

So when the API thinks it is requesting the normal DB session, pytest gives it the isolated testing session instead.

This is a powerful FastAPI testing technique because the application code does not need special testing branches.

---

# 52. Automatic database cleanup

```python
@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(...)
    Base.metadata.create_all(...)
    yield
    Base.metadata.drop_all(...)
```

Before each test:

```text
recreate clean tables
```

After each test:

```text
remove them
```

So one test cannot accidentally affect another.

This is called **test isolation**.

---

# 53. `tests/test_api.py` — what each API test proves

## `test_health`

Checks:

```http
GET /health
```

returns HTTP 200 and expected JSON.

---

## `test_create_event`

Checks:

```http
POST /events
```

actually creates a record and returns:

```text
id
status
created_at
```

---

## `test_invalid_status_is_rejected`

Sends an invalid status and confirms Pydantic/FastAPI rejects it with HTTP `422`.

This proves the public API contract is enforced.

---

## `test_cursor_pagination_returns_every_row_once`

Creates 7 events and requests them three at a time.

Expected final sequence:

```text
7, 6, 5, 4, 3, 2, 1
```

Then verifies:

```python
len(seen_ids) == len(set(seen_ids))
```

which proves no duplicates occurred.

---

## `test_same_timestamp_uses_id_as_tie_breaker`

Creates multiple rows with **exactly the same timestamp**.

This is a critical edge case.

Expected pages:

```text
Page 1: 5, 4
Page 2: 3, 2
Page 3: 1
```

This proves `id` correctly resolves timestamp ties.

---

## `test_filter_works_with_cursor_pagination`

Checks that:

```text
status filter
+
cursor pagination
```

work together.

The response must contain only pending rows while still progressing correctly through multiple pages.

---

## `test_invalid_cursor_returns_400`

Sends nonsense such as:

```text
not-a-valid-cursor
```

and confirms the API returns:

```json
{
  "detail": "Invalid pagination cursor"
}
```

with HTTP `400`.

---

## `test_limit_validation`

Checks invalid limits:

```text
0
101
```

and confirms FastAPI rejects both.

---

# 54. `tests/test_cursor.py` — testing the cursor itself

This file tests cursor behavior independently of the HTTP API.

That is useful because cryptographic/serialization code deserves focused tests.

---

# 55. Why 5,000 round trips?

```python
for event_id in range(1, 5001):
```

Each iteration performs:

```text
encode cursor
    -> decode cursor
    -> compare values
```

This test was added specifically because the original implementation had a random binary-delimiter failure mode.

A small test with only one cursor could easily miss a probabilistic bug.

Thousands of varied signatures give strong regression coverage for that exact failure.

---

# 56. Tampering test

The test creates a valid cursor and modifies part of the signed payload.

Then:

```python
decode_cursor(tampered)
```

must fail.

This proves that clients cannot simply edit:

```text
id=42
```

to:

```text
id=999999
```

without invalidating the HMAC signature.

---

# 57. `pyproject.toml`

The project contains:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
addopts = "-ra"
```

## `pythonpath = ["."]`

Adds the project root to pytest's Python import path.

This allows imports such as:

```python
from app.main import create_app
```

when running simply:

```bash
pytest -q
```

## `testpaths`

Tells pytest where the tests live.

---

# 58. `.env.example`

Example:

```text
CURSOR_SECRET=replace-with-a-long-random-secret
```

This documents environment variables without committing your real secrets.

A normal workflow is:

```text
.env.example   -> safe template in Git
real secret    -> environment / secret manager
```

The current application directly reads process environment variables using `os.getenv()`.

---

# 59. API reference

## Health

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

---

## Create event

```http
POST /events
Content-Type: application/json

{
  "status": "pending"
}
```

Valid statuses:

```text
pending
completed
failed
```

Example response:

```json
{
  "id": 1,
  "status": "pending",
  "created_at": "2026-09-01T12:00:00Z"
}
```

---

## First page

```http
GET /events?limit=5
```

---

## Next page

```http
GET /events?limit=5&cursor=<next_cursor>
```

---

## Filtered first page

```http
GET /events?status=pending&limit=5
```

---

## Filtered next page

```http
GET /events?status=pending&limit=5&cursor=<next_cursor>
```

---

# 60. Example frontend algorithm

A frontend does not need to decode the cursor.

Conceptually:

```text
cursor = null

load first page:
    GET /events?limit=20
    show data
    cursor = response.pagination.next_cursor

when user clicks "Load more":
    GET /events?limit=20&cursor=cursor
    append data
    cursor = response.pagination.next_cursor

if has_more == false:
    hide/disable "Load more"
```

If the user changes a filter:

```text
clear displayed data
cursor = null
request first page with new filter
```

---

# 61. Cursor pagination vs page numbers

Cursor pagination is excellent for:

```text
Next
Load more
Infinite scrolling
```

It is not naturally designed for:

```text
Jump directly to page 87
```

because Page 87 requires knowing the boundary reached after the preceding data.

If your product strictly requires arbitrary page-number navigation, offset pagination may be simpler.

Choose pagination based on product behavior, not because one technique is universally "better".

---

# 62. Why the server does not store cursors in the database

The cursor contains the necessary boundary:

```text
created_at
id
```

and is signed.

So the server can validate it and reconstruct the next query without maintaining a table such as:

```text
user_cursor_sessions
```

This makes the endpoint effectively stateless from a pagination-session perspective.

That is convenient for horizontally scaled APIs because any application instance with the same secret can validate the cursor.

---

# 63. What happens when new events are inserted during pagination?

Suppose Page 1 gives:

```text
10
9
8
```

and cursor is based on Event 8.

Then Event 11 is created before Page 2.

The next query asks for records after Event 8's boundary, so Event 11 does not cause 8/9/10 to shift into different offset positions.

This is one of cursor pagination's major strengths.

However, pagination semantics still depend on your business requirements. Concurrent updates to the actual sort fields can move records relative to a previously issued cursor.

For immutable creation timestamps and IDs, behavior is particularly easy to reason about.

---

# 64. Important production considerations

This project is complete and runnable, but a production system usually adds more infrastructure.

## Use a real production secret

Never rely on:

```text
development-only-change-me
```

in production.

Use environment-specific secret management.

---

## Use migrations

This demo uses:

```python
Base.metadata.create_all(...)
```

For a team/production database use Alembic migrations so schema changes are versioned and controlled.

---

## Consider PostgreSQL

SQLite is perfect for this standalone project and local learning.

A production multi-user service commonly uses PostgreSQL or another server database.

The SQLAlchemy structure already makes that transition much easier.

---

## Add a composite index for large datasets

The query repeatedly uses:

```text
status (sometimes)
created_at
id
```

and orders by:

```text
created_at DESC, id DESC
```

For a large production table, a carefully designed composite index can materially improve keyset pagination performance.

For example, depending on your query patterns/database:

```text
(created_at, id)
```

and potentially:

```text
(status, created_at, id)
```

may be appropriate.

Index design should be verified with your database's query plan rather than added blindly.

---

## Version cursors if the contract evolves

Today the cursor payload is:

```json
{
  "created_at": "...",
  "id": 123
}
```

If future versions change ordering substantially, consider adding a version field, for example:

```json
{
  "v": 1,
  "created_at": "...",
  "id": 123
}
```

Then the API can intentionally reject or support older cursor formats.

The current implementation deliberately accepts only exactly `created_at` and `id`, keeping the demo contract strict and simple.

---

## Bind filters into a cursor for stricter APIs

This demo expects the client to keep the same filter while following a cursor.

A more advanced API can include filter/sort information inside the signed cursor so that a cursor cannot accidentally be reused under a different query configuration.

That is a useful extension when an API has many filters or configurable sorting.

---

# 65. Common mistakes this project avoids

## Mistake 1 — Sorting only by a non-unique timestamp

Bad:

```text
ORDER BY created_at DESC
```

when many records can share the same timestamp.

Better:

```text
ORDER BY created_at DESC, id DESC
```

---

## Mistake 2 — Using `<=` at the cursor boundary

That repeats the final row from the previous page.

Use a strict boundary matching the sort direction.

---

## Mistake 3 — Generating the cursor from the look-ahead row

If you fetch `limit + 1`, the extra row is not returned.

The cursor must come from:

```text
last returned row
```

not:

```text
look-ahead row
```

---

## Mistake 4 — Trusting client-created cursor data

A client could modify an unsigned Base64 payload.

That is why we sign it with HMAC.

---

## Mistake 5 — Treating Base64 as encryption

Base64 provides transport encoding, not secrecy or authenticity.

HMAC provides authenticity/tamper detection here.

---

## Mistake 6 — Joining arbitrary binary signature data with a delimiter

Raw cryptographic bytes can contain your delimiter.

Encode the components first, then join their safe textual representations.

---

## Mistake 7 — Reusing cursors after changing filters

Reset pagination when the result-set definition changes.

---

## Mistake 8 — Forgetting a maximum page size

Always cap client-controlled limits.

---

# 66. Mental model to remember in interviews

If someone asks you to explain cursor pagination, you can say:

> Cursor pagination uses the sort values of the last item in the current page as the boundary for the next query. In this project, rows are ordered by `(created_at DESC, id DESC)`, so the cursor stores the final row's `(created_at, id)`. The next query selects rows where `created_at` is older, or where the timestamp is equal and the ID is smaller. We fetch `limit + 1` rows to detect whether another page exists and generate the next cursor from the last row actually returned. The cursor is Base64URL encoded and HMAC-signed so clients can pass it back as an opaque, tamper-evident token.

That explanation captures the core architecture.

---

# 67. Request lifecycle in one diagram

```text
CLIENT
  |
  | GET /events?limit=3&cursor=XYZ
  v
FASTAPI (main.py)
  |
  | validate status / limit / cursor type
  |
  +----> cursor.py
  |        |
  |        | verify HMAC
  |        | decode boundary
  |        v
  |      (created_at, id)
  |
  +----> repository.py
  |        |
  |        | SELECT Event
  |        | WHERE optional status
  |        | WHERE keyset boundary
  |        | ORDER BY created_at DESC, id DESC
  |        | LIMIT limit + 1
  |        v
  |      SQLAlchemy rows
  |
  | determine has_more
  | remove look-ahead row
  |
  +----> cursor.py
  |        |
  |        | encode last returned row
  |        | HMAC sign it
  |        v
  |      next_cursor
  |
  +----> schemas.py
  |        |
  |        | validate/serialize output
  |        v
  |
  v
JSON RESPONSE
{
  "data": [...],
  "pagination": {
    "limit": 3,
    "has_more": true,
    "next_cursor": "..."
  }
}
```

---

# 68. How the files work together

```text
database.py
    defines engine, Base, SessionLocal, get_db
          |
          v
models.py
    uses Base to define Event table
          |
          v
repository.py
    queries Event using a Session
          |
          v
main.py
    receives HTTP request and calls repository
          |
          +---- cursor.py signs/decodes page boundary
          |
          +---- schemas.py validates request/response data

scripts/seed.py
    uses database.py + models.py to insert sample rows

tests/
    exercises all of the above using an isolated database
```

---

# 69. What should you understand after studying this project?

You should be able to explain:

1. Why APIs paginate large datasets.
2. Difference between offset and cursor pagination.
3. Why stable deterministic ordering is required.
4. Why `(created_at, id)` is used instead of timestamp alone.
5. How the keyset `WHERE` condition is derived.
6. Why descending sort uses `<` for the next page.
7. Why we fetch `limit + 1`.
8. How `has_more` is determined without `COUNT(*)`.
9. Why `next_cursor` comes from the last returned row.
10. Why a cursor is not simply a page number.
11. Why Base64 is not encryption.
12. Why HMAC protects cursor integrity.
13. Why `compare_digest()` is used.
14. Why database sessions are dependencies.
15. Difference between SQLAlchemy models and Pydantic schemas.
16. Why API input and database constraints can both exist.
17. How FastAPI dependency overrides enable isolated tests.
18. Why timestamp ties require an ID tie-breaker.
19. Why filters must remain consistent across cursor requests.
20. What would need improvement for a large production deployment.

If you can explain those points without looking at the code, you understand the architecture rather than merely having copied it.

---

# 70. Suggested learning exercise

After running the project, do these manually in Swagger:

### Exercise 1

Create 8 events.

### Exercise 2

Request:

```http
GET /events?limit=3
```

Write down the returned IDs.

### Exercise 3

Copy `next_cursor` into the next request and continue until `has_more=false`.

Verify every ID appears exactly once.

### Exercise 4

Request only:

```http
GET /events?status=pending&limit=2
```

and paginate through the filtered set.

### Exercise 5

Change one character in a valid cursor and send it again.

Expected:

```http
400 Bad Request
```

### Exercise 6

Read `repository.py` and, without looking at this README, explain why this expression is correct:

```python
or_(
    Event.created_at < cursor_created_at,
    and_(
        Event.created_at == cursor_created_at,
        Event.id < cursor_id,
    ),
)
```

If you can derive it from the `ORDER BY`, you understand keyset pagination.

---

# 71. Final summary

The core algorithm can be reduced to five steps:

```text
1. Sort using a stable unique order
      created_at DESC, id DESC

2. Return a limited page

3. Store the final returned row's sort values in a signed cursor

4. On the next request, decode the cursor and query strictly after it
      created_at < cursor_created_at
      OR
      (created_at = cursor_created_at AND id < cursor_id)

5. Fetch limit + 1 to determine whether another page exists
```

Everything else in the project exists to make those five steps usable as a clean, validated, testable HTTP API.
