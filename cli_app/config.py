import os
from dataclasses import dataclass

@dataclass(frozen=True)
class CLIConfig:
    """
    Loads and validates settings from environment variables for the CLI Application.
    Interacts strictly with target_db (Silver Relational Layer).
    """
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "CLIConfig":
        """
        Factory method to construct CLIConfig.
        """
        db_host = os.getenv("TARGET_DB_HOST", "target_db")
        db_port_str = os.getenv("TARGET_DB_PORT", "5432")
        try:
            db_port = int(db_port_str)
        except ValueError:
            raise ValueError(f"TARGET_DB_PORT must be an integer. Received: '{db_port_str}'")
            
        db_user = os.getenv("TARGET_DB_USER")
        db_password = os.getenv("TARGET_DB_PASSWORD")
        db_name = os.getenv("TARGET_DB_NAME")
        
        if not all([db_user, db_password, db_name]):
            raise ValueError("All TARGET_DB_* environment variables must be configured.")
            
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        
        return cls(
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            db_password=db_password,
            db_name=db_name,
            log_level=log_level
        )
