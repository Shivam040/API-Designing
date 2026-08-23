from fastapi import FastAPI, HTTPException, Response, status
from .pydantic_models import UserCreate, UserReplace

app = FastAPI()

users: dict[int, dict[str, object]] = {
    1: {
        "id": 1,
        "name": "Neha",
        "active": True,
    }
}


@app.get("/users/{user_id}")
def get_user(user_id: int) -> dict[str, object]:
    # Safe and Idempotent retrieval
    user = users.get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )

    return user


@app.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate) -> dict[str, object]:
    user_id = max(users, default=0) + 1

    new_user = {
        "id": user_id,
        "name": payload.name,
        "active": True,
    }

    users[user_id] = new_user
    return new_user


@app.put("/users/{user_id}")
def replace_user(user_id: int, payload: UserReplace) -> dict[str, object]:
    # Change state but is Idempotent
    if user_id not in users:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"User with id {user_id} not found"
        )

    replaced_user = {
        "id": user_id,
        "name": payload.name,
        "active": payload.active,
    }

    users[user_id] = replaced_user
    return replaced_user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int) -> None:
    # Change state but is Idempotent
    if user_id not in users:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"User with id {user_id} not found"
        )

    del users[user_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


