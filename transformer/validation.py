import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DataQualityValidator:
    """
    Validates cleaned vehicle records against structural limits and domain rules
    prior to database loading into target_db.
    """
    def __init__(self, min_year: int = 1980, max_year: int = 2030):
        """
        Initializes the validator with custom boundary limits.
        
        Args:
            min_year (int): Minimum permissible vehicle year.
            max_year (int): Maximum permissible vehicle year.
        """
        self._min_year = min_year
        self._max_year = max_year

    def is_valid(self, record: Dict[str, Any]) -> bool:
        """
        Verifies that a cleaned record matches relational schema specs and constraints.
        
        Args:
            record (Dict[str, Any]): Cleaned record output from transformer.
            
        Returns:
            bool: True if constraints are satisfied, False if the record is rejected.
        """
        # 1. String length limits matching Silver DB definitions (VARCHAR(100))
        make = record.get("make")
        model = record.get("model_name")
        v_class = record.get("class")
        
        if not make or len(make) > 100:
            logger.warning(
                f"Validation failed: make '{make}' is empty or exceeds 100 chars."
            )
            return False
            
        if not model or len(model) > 100:
            logger.warning(
                f"Validation failed: model_name '{model}' is empty or exceeds 100 chars."
            )
            return False

        if v_class and len(v_class) > 100:
            logger.warning(
                f"Validation failed: vehicle class '{v_class}' exceeds 100 chars."
            )
            return False

        # 2. Production year logic validation
        year = record.get("year")
        if year is None or not (self._min_year <= year <= self._max_year):
            logger.warning(
                f"Validation failed: year '{year}' falls outside [{self._min_year}, {self._max_year}] range."
            )
            return False

        # 3. Numeric logic constraints (non-negativity bounds)
        cylinders = record.get("cylinders")
        if cylinders is not None and cylinders <= 0:
            logger.warning(
                f"Validation failed: cylinder count '{cylinders}' must be positive."
            )
            return False

        displacement = record.get("displacement")
        if displacement is not None and displacement <= 0.0:
            logger.warning(
                f"Validation failed: engine displacement '{displacement}' must be positive."
            )
            return False

        # MPG metrics (efficiency metrics must be positive numbers)
        for key in ["city_mpg", "highway_mpg", "combination_mpg"]:
            val = record.get(key)
            if val is not None and val <= 0:
                logger.warning(
                    f"Validation failed: fuel efficiency metric '{key}' ({val}) must be positive."
                )
                return False

        return True
