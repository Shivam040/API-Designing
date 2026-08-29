from typing import Annotated
from .pydantic_model import UserCreate, UserResponse
from fastapi import FastAPI, HTTPException, Header, Response, status

app = FastAPI()

users: dict[int, dict[str, object]] = {
    1: {
        "id": 1,
        "name": "Neha",
        "email": "neha@gmail.com",
    },
}


def get_authenticated_role(
        authorization: Annotated[
            str | None,
            Header(),
        ] = None,
) -> str:
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization credentials are required",
            headers={"WWW-Authenticaticat": "Bearer"},
        )

    if authorization == "Bearer admin-token":
        return "admin"

    if authorization == "Bearer user-token":
        return "user"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid access token",
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.get(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    )
def get_user(user_id: int) -> UserResponse:
    user = users.get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(**user)


@app.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    response: Response,
) -> UserResponse:
    duplicate_exists = any(
        str(user["email"]).casefold()
        == str(payload.email).casefold()
        for user in users.values()
    )
    if duplicate_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user_id = max(users, default=0) + 1
    user = {
        "id": user_id,
        "name": payload.name,
        "email": str(payload.email),
    }

    users[user_id] = user
    response.headers["Location"] = f"/users/{user_id}"
    return UserResponse(**user)


@app.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: int,
    authorization: Annotated[
        str | None,
        Header()
    ] = None,
) -> Response:
    role = get_authenticated_role(authorization)

    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator permission is required",
        )

    if user_id not in users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    del users[user_id]

    return Response(status_code=status.HTTP_204_NO_CONTENT)
