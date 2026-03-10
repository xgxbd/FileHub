from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FileHub API"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_debug: bool = True

    database_url: str = "sqlite:///./filehub.db"

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0
    upload_session_ttl_seconds: int = 86400
    upload_tmp_dir: str = "./tmp/uploads"

    minio_endpoint: str = "127.0.0.1:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "filehub"
    minio_secure: bool = False

    jwt_secret: str = "change_me_in_production"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
