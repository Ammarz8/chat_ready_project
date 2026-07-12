import os
from dataclasses import dataclass

@dataclass(frozen=True)
class TransformerConfig:
    """
    Configuration loader and validator for the Transformer Service.
    Loads settings for reading from Bronze layer and writing to Silver layer.
    """
    source_db_host: str
    source_db_port: int
    source_db_user: str
    source_db_password: str
    source_db_name: str
    
    target_db_host: str
    target_db_port: int
    target_db_user: str
    target_db_password: str
    target_db_name: str
    
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "TransformerConfig":
        """
        Factory method to construct TransformerConfig from environment variables.
        Performs validation and type conversion.
        """
        source_db_host = os.getenv("SOURCE_DB_HOST", "source_db")
        source_db_port_str = os.getenv("SOURCE_DB_PORT", "5432")
        try:
            source_db_port = int(source_db_port_str)
        except ValueError:
            raise ValueError(f"SOURCE_DB_PORT must be an integer. Received: '{source_db_port_str}'")
            
        source_db_user = os.getenv("SOURCE_DB_USER")
        source_db_password = os.getenv("SOURCE_DB_PASSWORD")
        source_db_name = os.getenv("SOURCE_DB_NAME")
        
        target_db_host = os.getenv("TARGET_DB_HOST", "target_db")
        target_db_port_str = os.getenv("TARGET_DB_PORT", "5432")
        try:
            target_db_port = int(target_db_port_str)
        except ValueError:
            raise ValueError(f"TARGET_DB_PORT must be an integer. Received: '{target_db_port_str}'")
            
        target_db_user = os.getenv("TARGET_DB_USER")
        target_db_password = os.getenv("TARGET_DB_PASSWORD")
        target_db_name = os.getenv("TARGET_DB_NAME")
        
        # Validation checks
        if not all([source_db_user, source_db_password, source_db_name]):
            raise ValueError("All SOURCE_DB_* environment variables must be set.")
            
        if not all([target_db_user, target_db_password, target_db_name]):
            raise ValueError("All TARGET_DB_* environment variables must be set.")
            
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        
        return cls(
            source_db_host=source_db_host,
            source_db_port=source_db_port,
            source_db_user=source_db_user,
            source_db_password=source_db_password,
            source_db_name=source_db_name,
            target_db_host=target_db_host,
            target_db_port=target_db_port,
            target_db_user=target_db_user,
            target_db_password=target_db_password,
            target_db_name=target_db_name,
            log_level=log_level
        )
