from datetime import datetime, timedelta, timezone

from app.models import PromoCode, User
from app.services.promo import apply_promo_percent


def _now():
    return datetime.now(timezone.utc)


def make_user(db_session, tid=100):
    u = User(telegram_id=tid)
    db_session.add(u)
    db_session.flush()
    return u


def test_valid_discount(db_session):
    p = PromoCode(code="WELCOME10", kind="discount_percent", value_int=10, enabled=True)
    db_session.add(p)
    db_session.flush()
    user = make_user(db_session)
    pct = apply_promo_percent(db_session, user, "welcome10", amount_rub=199)
    assert pct == 10
    assert user.pending_discount_promo_id == p.id


def test_expired_promo_rejected(db_session):
    p = PromoCode(code="OLD", kind="discount_percent", value_int=20, enabled=True,
                  ends_at=_now() - timedelta(days=1))
    db_session.add(p)
    db_session.flush()
    user = make_user(db_session)
    pct = apply_promo_percent(db_session, user, "OLD", amount_rub=199)
    assert pct == 0  # invalid -> no discount
