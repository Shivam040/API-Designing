from typing import Literal

from fastapi import (
    FastAPI,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from .pydantic_model import TaskUpdate, TaskResponse, TaskCreate, TaskReplace, TaskListResponse, Priority

app = FastAPI()


tasks: dict[int, dict[str, object]] = {}


def get_existing_task(task_id: int) -> dict[str, object]:
    task = tasks.get(task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    payload: TaskCreate,
    response: Response,
) -> TaskResponse:
    task_id = max(tasks, default=0) + 1

    task = {
        "id": task_id,
        **payload.model_dump(),
    }

    tasks[task_id] = task
    response.headers["Location"] = f"/tasks/{task_id}"

    return TaskResponse(**task)


@app.get(
    "/tasks",
    response_model=TaskListResponse,
    status_code=status.HTTP_200_OK,
)
def list_tasks(
    completed: bool | None = Query(default=None),
    priority: Priority | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> TaskListResponse:
    selected_tasks = list(tasks.values())

    if completed is not None:
        selected_tasks = [
            task
            for task in selected_tasks
            if task["completed"] is completed
        ]

    if priority is not None:
        selected_tasks = [
            task
            for task in selected_tasks
            if task["priority"] == priority
        ]

    paginated_tasks = selected_tasks[offset : offset + limit]

    return TaskListResponse(
        data=[
            TaskResponse(**task)
            for task in paginated_tasks
        ],
        limit=limit,
        offset=offset,
        returned=len(paginated_tasks),
    )


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
def get_task(
    task_id: int = Path(gt=0),
) -> TaskResponse:
    return TaskResponse(**get_existing_task(task_id))


@app.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
def replace_task(
    payload: TaskReplace,
    task_id: int = Path(gt=0),
) -> TaskResponse:
    get_existing_task(task_id)

    replacement = {
        "id": task_id,
        **payload.model_dump(),
    }

    tasks[task_id] = replacement
    return TaskResponse(**replacement)


@app.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
def update_task(
    payload: TaskUpdate,
    task_id: int = Path(gt=0),
) -> TaskResponse:
    task = get_existing_task(task_id)
    changes = payload.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one update field must be supplied",
        )

    updated_task = {
        **task,
        **changes,
    }

    tasks[task_id] = updated_task
    return TaskResponse(**updated_task)


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    task_id: int = Path(gt=0),
) -> Response:
    get_existing_task(task_id)
    del tasks[task_id]

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )

