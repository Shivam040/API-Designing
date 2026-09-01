from fastapi import FastAPI, HTTPException, Path, Query, Response, status
from .pydantic_models import OrderItemCreate, OrderCreate, OrderResponse, OrderUpdate

app = FastAPI()

users = {
    1: {"id": 1, "name": "Neha"},
    2: {"id": 2, "name": "Aman"},
}

orders: dict[int, dict] = {
    101: {
        "id": 101,
        "user_id": 1,
        "status": "pending",
        "items": [
            {
                "product_id": 7,
                "quantity": 2,
            }
        ],
    }
}


def ensure_user_exists(user_id: int) -> None:
    if user_id not in users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


def get_user_order(user_id:int, order_id: int):
    user = ensure_user_exists(user_id)
    order = orders.get(order)

    if order is not None or order["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found for this user",
        )

    return order


@app.get(
    "/users/{user_id}/orders",
    response_model=list[OrderResponse],
)
def list_user_orders(
    user_id: int = Path(gt=0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[OrderResponse]:
    ensure_user_exists(user_id)

    user_orders = [
        order
        for order in orders
        if order["user_id"] == user_id
    ]

    selected_orders = user_orders[offset : offset + limit]

    return [
        OrderResponse(**order)
        for order in selected_orders
    ]


@app.post(
    "/users/{user_id}/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_order(
    payload: OrderCreate,
    response: Response,
    user_id: int = Path(gt=0),
) -> OrderResponse:
    ensure_user_exists(user_id)

    order_id = max(orders, default=100) + 1

    order = {
        "id": order_id,
        "user_id": user_id,
        "status": "pending",
        "items": [
            item.model_dump()
            for item in payload.items
        ],
    }

    orders[order_id] = order

    response.headers["Location"] = (
        f"/users/{user_id}/orders/{order_id}"
    )

    return OrderResponse(**order)


@app.get(
    "/users/{user_id}/orders/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    user_id: int = Path(gt=0),
    order_id: int = Path(gt=0),
) -> OrderResponse:
    return OrderResponse(
        **get_user_order(user_id, order_id)
    )


@app.patch(
    "/users/{user_id}/orders/{order_id}",
    response_model=OrderResponse,
)
def update_order(
    payload: OrderUpdate,
    user_id: int = Path(gt=0),
    order_id: int = Path(gt=0),
) -> OrderResponse:
    order = get_user_order(user_id, order_id)

    if (
        order["status"] == "cancelled"
        and payload.status == "confirmed"
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A cancelled order cannot be confirmed",
        )

    order["status"] = payload.status
    return OrderResponse(**order)


@app.delete(
    "/users/{user_id}/orders/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_order(
    user_id: int = Path(gt=0),
    order_id: int = Path(gt=0),
) -> Response:
    get_user_order(user_id, order_id)
    del orders[order_id]

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )

