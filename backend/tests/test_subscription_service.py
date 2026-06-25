from unittest.mock import patch

from app.models import User, VpnServer
from app.services.subscription import activate_subscription, extend_subscription


def _servers(db_session):
    s1 = VpnServer(name="DE", protocol="vless_reality", host="1.1.1.1", port=443, sni="s", public_key="pk", short_id="sid", ssh_host="1.1.1.1", sort_order=0)
    s2 = VpnServer(name="NL", protocol="hysteria2", host="2.2.2.2", port=443, sni="s", ssh_host="2.2.2.2", sort_order=1)
    db_session.add_all([s1, s2])
    db_session.flush()
    return [s1, s2]


def test_activate_creates_one_config_per_server(db_session):
    user = User(telegram_id=1)
    db_session.add(user)
    db_session.flush()
    servers = _servers(db_session)
    with patch("app.services.subscription.add_client") as add_mock, \
         patch("app.services.subscription._get_enabled_servers", return_value=servers):
        activate_subscription(db_session, user, months=1)
    add_mock.assert_called()  # provisioned on both servers
    assert len(user.configs) == 2
    assert all(c.is_active for c in user.configs)
    assert user.subscription_token is not None
    # connection urls are correct protocol per server
    urls = sorted(c.connection_url.split("://")[0] for c in user.configs)
    assert urls == ["hy2", "vless"]


def test_extend_adds_days_from_now(db_session):
    user = User(telegram_id=2)
    db_session.add(user)
    db_session.flush()
    extend_subscription(db_session, user, months=3)
    assert user.subscription_until is not None
