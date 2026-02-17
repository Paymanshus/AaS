from dataclasses import dataclass

from fastapi import Header, HTTPException, status


@dataclass(slots=True)
class CurrentUser:
    user_id: str
    handle: str


async def get_current_user(
    x_user_id: str | None = Header(default=None),
    x_user_handle: str | None = Header(default=None),
) -> CurrentUser:
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing x-user-id header. MVP auth expects a logged-in client user id.",
        )
    handle = x_user_handle or f"user-{x_user_id[:6]}"
    return CurrentUser(user_id=x_user_id, handle=handle)


async def get_optional_user(
    x_user_id: str | None = Header(default=None),
    x_user_handle: str | None = Header(default=None),
) -> CurrentUser | None:
    if not x_user_id:
        return None
    handle = x_user_handle or f"user-{x_user_id[:6]}"
    return CurrentUser(user_id=x_user_id, handle=handle)
