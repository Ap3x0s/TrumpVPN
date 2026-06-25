import base64
from urllib.parse import quote

PROTOCOL_VLESS_REALITY = "vless_reality"
PROTOCOL_HYSTERIA2 = "hysteria2"


def server_protocol(server) -> str:
    value = str(getattr(server, "protocol", "") or "").strip().lower()
    return value if value in {PROTOCOL_VLESS_REALITY, PROTOCOL_HYSTERIA2} else PROTOCOL_VLESS_REALITY


def build_vless_url(server, client_uuid: str, label: str) -> str:
    params = (
        "encryption=none"
        "&security=reality"
        f"&sni={quote(server.sni, safe='')}"
        f"&fp={quote(server.fingerprint, safe='')}"
        f"&pbk={quote(server.public_key, safe='')}"
        f"&sid={quote(server.short_id, safe='')}"
        "&type=tcp"
        "&flow=xtls-rprx-vision"
    )
    return f"vless://{client_uuid}@{server.host}:{server.port}?{params}#{quote(label, safe='')}"


def build_hysteria2_url(server, password: str, label: str) -> str:
    params: list[str] = []
    sni = str(getattr(server, "sni", "") or "").strip()
    if sni:
        params.append(f"sni={quote(sni, safe='')}")
    alpn = str(getattr(server, "hy2_alpn", "h3") or "h3").strip()
    if alpn:
        params.append(f"alpn={quote(alpn, safe=',')}")
    if bool(getattr(server, "hy2_insecure", False)):
        params.append("insecure=1")
    obfs = str(getattr(server, "hy2_obfs", "") or "").strip()
    if obfs:
        params.append(f"obfs={quote(obfs, safe='')}")
        obfs_password = str(getattr(server, "hy2_obfs_password", "") or "").strip()
        if obfs_password:
            params.append(f"obfs-password={quote(obfs_password, safe='')}")
    query = f"?{'&'.join(params)}" if params else ""
    auth = quote(str(password or ""), safe="")
    return f"hy2://{auth}@{server.host}:{int(server.port)}{query}#{quote(label, safe='')}"


def build_client_url(server, client_secret: str, label: str) -> str:
    if server_protocol(server) == PROTOCOL_HYSTERIA2:
        return build_hysteria2_url(server, client_secret, label)
    return build_vless_url(server, client_secret, label)


def build_subscription_b64(urls: list[str]) -> str:
    payload = "\n".join(urls).encode("utf-8")
    return base64.b64encode(payload).decode("utf-8")
