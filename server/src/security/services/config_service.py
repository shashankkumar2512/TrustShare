from sqlalchemy.orm import Session

from src.security.models.app_config import AppConfig


def get_config(db: Session, key: str, default: str | None = None) -> str | None:
    """
    Retrieve a configuration value from the database.
    """

    config = db.query(AppConfig).filter(AppConfig.config_key == key).first()

    if config:
        return config.config_value

    return default
