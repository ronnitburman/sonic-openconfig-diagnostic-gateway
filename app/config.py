from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8080

    device_mode: str = "fixture"  # "fixture" | "live"

    gnmi_host: str = ""
    gnmi_port: int = 50052
    gnmi_username: str = ""
    gnmi_password: str = ""
    gnmi_insecure: bool = False  # false = use TLS, true = plaintext
    gnmi_skip_verify: bool = True  # skip TLS certificate verification

    gnoi_host: str = ""
    gnoi_port: int = 50052
    gnoi_insecure: bool = False
    gnoi_skip_verify: bool = True

    audit_log_path: str = "./data/audit.jsonl"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
