from typing import Any

from pydantic import BaseModel, Field


class TelegramLoginRequest(BaseModel):
    # accepts the full Login Widget callback fields
    id: int
    auth_date: int
    hash: str
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    photo_url: str | None = None

    model_config = {"extra": "allow"}  # widget may send extra fields


class UserOut(BaseModel):
    telegram_id: int
    username: str | None = None
    subscription_until: str | None = None
    balance_rub: int = 0

    model_config = {"from_attributes": True}

    @classmethod
    def from_user(cls, user: Any) -> "UserOut":
        return cls(
            telegram_id=user.telegram_id,
            username=user.username,
            subscription_until=user.subscription_until.isoformat() if user.subscription_until else None,
            balance_rub=int(user.balance_rub or 0),
        )


class CreatePaymentRequest(BaseModel):
    plan_id: str = Field(min_length=2, max_length=16)
    promo_code: str | None = Field(default=None, max_length=64)


class PaymentCreatedOut(BaseModel):
    invoice_id: int
    pay_url: str
    amount_rub: int
    payable_rub: int
    status: str


class PaymentStatusOut(BaseModel):
    invoice_id: int
    status: str
    paid: bool


class RedeemPromoRequest(BaseModel):
    code: str = Field(min_length=2, max_length=64)


class IssueTokenRequest(BaseModel):
    telegram_id: int
    username: str | None = None


class ExchangeTokenRequest(BaseModel):
    token: str = Field(min_length=10, max_length=128)
