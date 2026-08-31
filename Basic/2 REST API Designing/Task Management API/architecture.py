from fastapi import FastAPI, HTTPException, Query, Response, status
from .pydantic_model import TaskCreate, TaskResponse, TaskUpdate


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


@app.get(
    "/tasks",
    response_model=list[TaskResponse],
)
def list_tasks(
    completed: bool | None = Query(default=None),
) -> list[TaskResponse]:
    selected_tasks = list(tasks.values())

    if completed is not None:
        selected_tasks = [
            task
            for task in selected_tasks
            if task["completed"] is completed
        ]

    return [
        TaskResponse(**task)
        for task in selected_tasks
    ]


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
def get_task(task_id: int) -> TaskResponse:
    return TaskResponse(**get_existing_task(task_id))


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


@app.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
)
def update_task(
    task_id: int,
    payload: TaskUpdate,
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
def delete_task(task_id: int) -> Response:
    get_existing_task(task_id)
    del tasks[task_id]

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )

