# Retrive employee by primary key
# Check duplicate constraits where required
# Apply only supplied fields
# Commit the transaction
# Refresh and return the record

from fastapi import FastAPI, HTTPException, Path, Query, status
from .pydantic_model import EmployeeResponse, EmployeeUpdate, EmployeeUpdateResponse

app = FastAPI()


employees: dict[int, dict] = {
    "1": {
        "id": 1,
        "name": "Neha",
        "email": "neha@gmail.com",
        "department": "Engineering",
        "active": True,
    }
}

def email_exist(
        email: str,
        excluded_employee_id: int,
) -> bool:
    return any(
        employee["email"].lower() == email.lower()
        and employee["id"] != excluded_employee_id
        for employee in employees.value()
    )


@app.patch(
    "/employees/{employee_id}",
    response_model=EmployeeUpdateResponse,
    status_code=status.HTTP_200_OK,
)
def update_employee(
    payload: EmployeeUpdate,
    employee_id: int = Path(gt=0),
    send_notification: bool = Query(default=False),
):
    employee = employee.get(employee_id)

    if employee is None:
        return HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail="Employee ID Not Found",
        )

    changes = payload.model_dump(exclude_unset=True)

    if not changes:
        return HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail="At least one update field must be supplied",
        )

    new_email = changes.get("email")

    if new_email is not None and email_exist(
        str(new_email),
        exclude_employee_id=employee_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address already exists",
        )

    updated_employee = {
        **employee,
        **changes,
    }

    employees[employee_id] = updated_employee

    return EmployeeUpdateResponse(
        employee=EmployeeUpdate(**updated_employee),
        notification_requested=send_notification,
    )

