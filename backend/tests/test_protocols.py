from app.models import VpnServer
from app.services.protocols import build_vless_url, build_hysteria2_url, build_subscription_b64


def make_server(**kw):
    base = dict(
        name="DE", protocol="vless_reality", host="1.2.3.4", port=443,
        sni="www.cloudflare.com", public_key="PBK", short_id="ab12cd34",
        fingerprint="chrome", hy2_alpn="h3", hy2_insecure=False,
        ssh_host="1.2.3.4",
    )
    base.update(kw)
    return VpnServer(**base)


def test_build_vless_url_shape():
    url = build_vless_url(make_server(), "11111111-1111-1111-1111-111111111111", "DE")
    assert url.startswith("vless://11111111-1111-1111-1111-111111111111@1.2.3.4:443?")
    assert "security=reality" in url
    assert "pbk=PBK" in url
    assert "sid=ab12cd34" in url
    assert url.endswith("#DE")


def test_build_hysteria2_url_shape():
    url = build_hysteria2_url(make_server(protocol="hysteria2"), "s3cr3t", "DE")
    assert url.startswith("hy2://s3cr3t@1.2.3.4:443?")
    assert "sni=www.cloudflare.com" in url
    assert "alpn=h3" in url


def test_subscription_b64_roundtrip():
    import base64
    payload = build_subscription_b64(["vless://a@h:443#A", "hy2://b@h:443#B"])
    decoded = base64.b64decode(payload).decode("utf-8")
    assert decoded == "vless://a@h:443#A\nhy2://b@h:443#B"
