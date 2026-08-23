from fastapi import FastAPI, HTTPException, Response, status
from .Pydantic_models import UserCreate, UserReplace, UserUpdate, UserResponse

app = FastAPI()

users: dict[int, dict] = {
    1: {
        "id": 1,
        "name": "Neha",
        "email": "neha04@gmail.com",
        "active": True,
    }
}


def get_existing_user(user_id: int) -> dict:
    user = users.get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    return user


def ensure_unique_email(
        email: str,
        exclude_user_id: int | None = None,
) -> None:
    for existing_user in users.values():
        if (
            existing_user["email"].lower() == email.lower()
            and existing_user["id"] != exclude_user_id
        ):
            raise HTTPException(
                status_code = status.HTTP_409_CONFLICT,
                detail = f"User with email {email} already exists",
            )


@app.get("/users/{user_id}", response_model=UserResponse,)
def get_user(user_id: int) -> dict:
    # ** Use to unpack the dictionary
    return UserResponse(**get_existing_user(user_id))


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, response: Response) -> UserResponse:
    ensure_unique_email(str(payload.email))
    new_id = max(users, default=0) + 1
    user = {
        "id": new_id,
        **payload.model_dump(),
    }

    users[new_id] = user
    response.headers["Location"] = f"/users/{new_id}"

    return UserResponse(**user)


@app.put("/users/{user_id}", response_model=UserResponse)
def replace_user(user_id: int, payload: UserReplace) -> UserResponse:
    get_existing_user(user_id)
    ensure_unique_email(str(payload.email), exclude_user_id=user_id)

    replacement = {
        "id": user_id,
        **payload.model_dump()
    }

    users[user_id] = replacement
    return UserResponse(**replacement)


@app.patch("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate) -> UserResponse:
    user = get_existing_user(user_id)
    changes = payload.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No changes provided for update"
        )

    if "email" in changes and changes["email"] is not None:
        ensure_unique_email(str(payload.email), exclude_user_id=user_id)


    updated_user = {
        **user,
        **changes,
    }

    users[user_id] = updated_user
    return UserResponse(**updated_user)


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: id) -> None:
    get_existing_user(user_id)
    del users[user_id]

    return Response(status_code=status.HTTP_204_NO_CONTENT)


