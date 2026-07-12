import os
from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class ExtractorConfig:
    """
    Configuration loader and validator for the Extractor Service.
    Loads and validates settings from environment variables.
    """
    api_key: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    log_level: str = "INFO"
    
    # Default list of vehicle manufacturers to extract if not overridden
    target_makes: List[str] = field(default_factory=lambda: [
        "toyota", "honda", "ford", "chevrolet", "nissan", 
        "bmw", "mercedes-benz", "audi", "lexus", "volkswagen"
    ])
    
    # Default list of years to extract if not overridden
    target_years: List[int] = field(default_factory=lambda: [
        2020, 2021, 2022, 2023, 2024
    ])

    @classmethod
    def from_env(cls) -> "ExtractorConfig":
        """
        Factory method to construct ExtractorConfig from environment variables.
        Performs validation and type conversion.
        """
        api_key = os.getenv("API_NINJAS_API_KEY")
        if not api_key or api_key == "your_api_key_here":
            raise ValueError(
                "API_NINJAS_API_KEY must be set in environment variables and cannot be the default placeholder."
            )
        
        db_host = os.getenv("SOURCE_DB_HOST", "source_db")
        
        db_port_str = os.getenv("SOURCE_DB_PORT", "5432")
        try:
            db_port = int(db_port_str)
        except ValueError:
            raise ValueError(f"SOURCE_DB_PORT must be an integer. Received: '{db_port_str}'")
            
        db_user = os.getenv("SOURCE_DB_USER")
        db_password = os.getenv("SOURCE_DB_PASSWORD")
        db_name = os.getenv("SOURCE_DB_NAME")
        
        if not all([db_user, db_password, db_name]):
            raise ValueError(
                "Database parameters (SOURCE_DB_USER, SOURCE_DB_PASSWORD, SOURCE_DB_NAME) must be set."
            )
            
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Instantiate base config
        config = cls(
            api_key=api_key,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            db_password=db_password,
            db_name=db_name,
            log_level=log_level
        )
        
        # Override target makes if set as comma-separated list
        makes_env = os.getenv("TARGET_MAKES")
        if makes_env:
            parsed_makes = [m.strip().lower() for m in makes_env.split(",") if m.strip()]
            if parsed_makes:
                object.__setattr__(config, "target_makes", parsed_makes)
                
        # Override target years if set as comma-separated list
        years_env = os.getenv("TARGET_YEARS")
        if years_env:
            parsed_years = []
            for y in years_env.split(","):
                y_clean = y.strip()
                if y_clean.isdigit():
                    parsed_years.append(int(y_clean))
            if parsed_years:
                object.__setattr__(config, "target_years", parsed_years)
                
        return config
