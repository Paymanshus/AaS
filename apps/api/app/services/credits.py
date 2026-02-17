from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import CreditLedger, User

settings = get_settings()


async def ensure_user(session: AsyncSession, user_id: str, handle: str | None = None) -> User:
    user = await session.get(User, user_id)
    if user:
        if handle and handle != user.handle:
            user.handle = handle
            await session.flush()
        return user

    user = User(id=user_id, handle=handle or "anonymous")
    session.add(user)
    seed = CreditLedger(
        user_id=user.id,
        delta=settings.initial_credits,
        reason="signup_seed",
        balance_after=settings.initial_credits,
    )
    session.add(seed)
    await session.flush()
    return user


def _latest_balance_stmt(user_id: str) -> Select[tuple[int]]:
    return (
        select(CreditLedger.balance_after)
        .where(CreditLedger.user_id == user_id)
        .order_by(CreditLedger.created_at.desc())
        .limit(1)
    )


async def get_credit_balance(session: AsyncSession, user_id: str) -> int:
    result = await session.execute(_latest_balance_stmt(user_id))
    latest = result.scalar_one_or_none()
    return latest if latest is not None else settings.initial_credits


async def consume_start_credit(session: AsyncSession, user_id: str) -> int:
    balance = await get_credit_balance(session, user_id)
    if balance <= 0:
        raise ValueError("No credits remaining")
    new_balance = balance - 1
    entry = CreditLedger(
        user_id=user_id,
        delta=-1,
        reason="argument_start",
        balance_after=new_balance,
    )
    session.add(entry)
    await session.flush()
    return new_balance
