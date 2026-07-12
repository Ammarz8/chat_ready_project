import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)

class CarDataTransformer:
    """
    Implements normalization, cleaning, and flattening logic for raw API Ninjas vehicle specifications.
    Transposes values to match the target database schema structure.
    """
    
    # Static mappings for standardizing attributes to human-readable values
    TRANSMISSION_MAP = {
        "a": "Automatic",
        "m": "Manual",
        "am": "Automated Manual",
        "cvt": "CVT",
        "auto": "Automatic"
    }

    DRIVE_MAP = {
        "fwd": "FWD",
        "rwd": "RWD",
        "awd": "AWD",
        "4wd": "4WD",
        "4x4": "4WD"
    }

    FUEL_MAP = {
        "gas": "Gasoline",
        "diesel": "Diesel",
        "electricity": "Electric",
        "cng": "CNG",
        "lpg": "LPG"
    }

    def clean_string(self, value: Optional[str]) -> Optional[str]:
        """Trims whitespace and standardizes null values."""
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned if cleaned else None

    def transform_record(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Transforms and normalizes a single raw vehicle record.
        
        Args:
            raw (Dict[str, Any]): A single raw vehicle record from the API response payload.
            
        Returns:
            Optional[Dict[str, Any]]: Cleaned and normalized record dict, 
                                      or None if the record fails structure requirements.
        """
        try:
            # 1. Extract and validate mandatory fields
            raw_make = self.clean_string(raw.get("make"))
            raw_model = self.clean_string(raw.get("model"))
            raw_year = raw.get("year")

            if not raw_make or not raw_model or raw_year is None:
                logger.warning(
                    f"Skipping record due to missing mandatory identifiers: "
                    f"make={raw_make}, model={raw_model}, year={raw_year}"
                )
                return None

            # Standardize identifiers (makes and models are kept lowercase in dimension logic)
            make = raw_make.lower()
            model_name = raw_model.title()  # e.g., "camry" -> "Camry"
            
            try:
                year = int(raw_year)
            except ValueError:
                logger.warning(f"Skipping record due to invalid year value: {raw_year}")
                return None

            # 2. Clean and map textual details
            raw_class = self.clean_string(raw.get("class"))
            vehicle_class = raw_class.lower() if raw_class else None

            # Normalize transmission type
            raw_trans = self.clean_string(raw.get("transmission"))
            transmission = None
            if raw_trans:
                raw_trans_lower = raw_trans.lower()
                # API Ninjas transmission often appends details e.g., "a5", "m6". Extract the core type.
                core_trans = "".join([c for c in raw_trans_lower if c.isalpha()])
                transmission = self.TRANSMISSION_MAP.get(core_trans, raw_trans.title())

            # Normalize drive train type
            raw_drive = self.clean_string(raw.get("drive"))
            drive_type = None
            if raw_drive:
                drive_type = self.DRIVE_MAP.get(raw_drive.lower(), raw_drive.upper())

            # Normalize fuel type
            raw_fuel = self.clean_string(raw.get("fuel_type"))
            fuel_type = None
            if raw_fuel:
                fuel_type = self.FUEL_MAP.get(raw_fuel.lower(), raw_fuel.capitalize())

            # 3. Clean and map numeric details
            # Cylinders (Nullable for Electric/Rotary engines)
            raw_cylinders = raw.get("cylinders")
            cylinders = None
            if raw_cylinders is not None:
                try:
                    cylinders = int(raw_cylinders)
                except ValueError:
                    pass

            # Displacement (Nullable for Electric vehicles)
            raw_disp = raw.get("displacement")
            displacement = None
            if raw_disp is not None:
                try:
                    displacement = round(float(raw_disp), 1)
                except ValueError:
                    pass

            # MPG details
            city_mpg = self.parse_int(raw.get("city_mpg"))
            highway_mpg = self.parse_int(raw.get("highway_mpg"))
            combination_mpg = self.parse_int(raw.get("combination_mpg"))

            return {
                "make": make,
                "model_name": model_name,
                "year": year,
                "class": vehicle_class,
                "transmission": transmission,
                "drive_type": drive_type,
                "fuel_type": fuel_type,
                "cylinders": cylinders,
                "displacement": displacement,
                "city_mpg": city_mpg,
                "highway_mpg": highway_mpg,
                "combination_mpg": combination_mpg
            }

        except Exception as e:
            logger.error(f"Unexpected error transforming raw record: {e}, Record: {raw}")
            return None

    def parse_int(self, value: Any) -> Optional[int]:
        """Utility parser for integer metrics."""
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def extract_dimensions(
        self, 
        cleaned_records: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """
        Identifies unique dimension table entries (makes, classes) from a batch of cleaned records.
        
        Args:
            cleaned_records (List[Dict[str, Any]]): Normalized vehicle records.
            
        Returns:
            Tuple[List[str], List[str]]: (unique_makes_list, unique_classes_list).
        """
        unique_makes = set()
        unique_classes = set()
        
        for record in cleaned_records:
            if record.get("make"):
                unique_makes.add(record["make"])
            if record.get("class"):
                unique_classes.add(record["class"])
                
        return sorted(list(unique_makes)), sorted(list(unique_classes))
