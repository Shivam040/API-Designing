# API:
# Retriving one user
# Retriving a user collection
# Optional active-status filtering
# Optional department filtering
# Optional creation-date filtering
# Pagination
# Correct Validation and status code

from fastapi import FastAPI, HTTPException, Path, Query, status
from datetime import datetime, timezone

from .pydantic_model import UserResponse, PaginationResponse, UserListResponse


app = FastAPI()


users = [
    {
        "id": 1,
        "name": "Mansi",
        "department": "Analytics",
        "active": True,
        "created_at": datetime(
            2026, 1, 10, 9, 0, tzinfo=timezone.utc
        ),
    },
    {
        "id": 2,
        "name": "Aman",
        "department": "Engineering",
        "active": False,
        "created_at": datetime(
            2025, 12, 15, 10, 30, tzinfo=timezone.utc
        ),
    },
    {
        "id": 3,
        "name": "Priya",
        "department": "Engineering",
        "active": True,
        "created_at": datetime(
            2026, 3, 20, 12, 0, tzinfo=timezone.utc
        ),
    },
]


@app.get(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_user(
    user_id: int = Path(gt = 0)
) -> UserResponse:
    # Give me the first matching user. If there isn't one, return None
    user = next(
        (
            current_user
            for current_user in users
            if current_user["id"] == user_id
        ),
        None,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(**user)


@app.get(
    "/users",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,   
)
def list_users(
    active: bool | None = Query(default=None),
    department: str | None = Query(
        default = None,
        min_length=2,
        max_length=100,
    ),
    created_after: datetime | None = Query(default=None),
    limit: int | None = Query(default=20, ge=0, le=100),
    offset: int | None = Query(default=0, ge=0),
) -> UserListResponse:
    filtered_user = users

    if active is not None:
        filtered_user = [
            user
            for user in filtered_user
            if user["active"] == active
        ]

    if department is not None:
        filtered_user = [
            user
            for user in filtered_user
            if user["department"] == department
        ]

    if created_after is not None:
        filtered_user = [
            user
            for user in filtered_user
            if user["created_at"] > created_after
        ]

    selected_users = filtered_user[offset: limit+offset]

    return UserListResponse(
        data = [
            UserResponse(**user)
            for user in selected_users
        ],
        pagination=PaginationResponse(
            limit=limit,
            offset=offset,
            returned=len(selected_users),
        ),
    )

