from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user

OWNER = "Owner"
MANAGER = "Manager"
EMPLOYEE = "Employee"


def require_roles(allowed_roles: list[str]):
    def checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permission",
            )
        return current_user

    return checker 