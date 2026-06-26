from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    tg_bot_token: str = ""
    tg_bot_username: str = ""
    public_base_url: str = "http://localhost:8000"

    crypto_pay_api_token: str = ""
    crypto_pay_base_url: str = "https://pay.crypt.bot/api"
    crypto_pay_invoice_expires_in: int = 86400
    crypto_pay_accepted_assets: str = "USDT,TON,BTC,ETH,LTC,BNB,TRX,USDC"

    jwt_secret: str = "change-me"
    session_cookie_name: str = "trumpvpn_session"
    session_ttl_seconds: int = 7 * 24 * 3600

    database_url: str = "sqlite:///./trumpvpn.db"

    @property
    def accepted_assets_list(self) -> list[str]:
        return [a.strip() for a in self.crypto_pay_accepted_assets.split(",") if a.strip()]


settings = Settings()
