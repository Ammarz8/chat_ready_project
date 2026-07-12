import unittest
from transformer.transform import CarDataTransformer
from transformer.validation import DataQualityValidator

class TestTransformerComponents(unittest.TestCase):
    """
    Unit tests for Processing layer components (data transformer, validator).
    """

    def setUp(self) -> None:
        self.transformer = CarDataTransformer()
        self.validator = DataQualityValidator(min_year=1990, max_year=2025)

    def test_record_transformation_cleaning(self) -> None:
        """Verifies standard mapping adjustments for abbreviations and cases."""
        raw_car = {
            "make": "  Toyota  ",
            "model": "camry LE",
            "year": "2022",
            "class": "midsize car",
            "transmission": "a6",
            "drive": "fwd",
            "fuel_type": "gas",
            "cylinders": "4",
            "displacement": "2.45",
            "city_mpg": "28",
            "highway_mpg": "35",
            "combination_mpg": "31"
        }
        
        cleaned = self.transformer.transform_record(raw_car)
        self.assertIsNotNone(cleaned)
        
        self.assertEqual(cleaned["make"], "toyota")          # Lowercase make
        self.assertEqual(cleaned["model_name"], "Camry Le")   # Titlecase model
        self.assertEqual(cleaned["year"], 2022)               # Int year
        self.assertEqual(cleaned["class"], "midsize car")     # Lowercase class
        self.assertEqual(cleaned["transmission"], "Automatic")# Mapped trans
        self.assertEqual(cleaned["drive_type"], "FWD")        # Mapped drive
        self.assertEqual(cleaned["fuel_type"], "Gasoline")    # Mapped fuel
        self.assertEqual(cleaned["cylinders"], 4)             # Int cylinders
        self.assertEqual(cleaned["displacement"], 2.5)         # Rounded float
        self.assertEqual(cleaned["city_mpg"], 28)
        self.assertEqual(cleaned["combination_mpg"], 31)

    def test_record_validation_limits(self) -> None:
        """Verifies validator constraints for bounds and sizes."""
        # Cleaned valid record
        valid_car = {
            "make": "honda",
            "model_name": "Civic",
            "year": 2020,
            "class": "compact car",
            "transmission": "Manual",
            "drive_type": "FWD",
            "fuel_type": "Gasoline",
            "cylinders": 4,
            "displacement": 2.0,
            "city_mpg": 32,
            "highway_mpg": 40,
            "combination_mpg": 36
        }
        
        self.assertTrue(self.validator.is_valid(valid_car))

        # Test invalid year bounds (1989 < 1990)
        invalid_year_car = valid_car.copy()
        invalid_year_car["year"] = 1989
        self.assertFalse(self.validator.is_valid(invalid_year_car))

        # Test negative cylinder count
        invalid_cylinders_car = valid_car.copy()
        invalid_cylinders_car["cylinders"] = -2
        self.assertFalse(self.validator.is_valid(invalid_cylinders_car))

        # Test zero engine displacement
        invalid_displacement_car = valid_car.copy()
        invalid_displacement_car["displacement"] = 0.0
        self.assertFalse(self.validator.is_valid(invalid_displacement_car))

        # Test negative MPG value
        invalid_mpg_car = valid_car.copy()
        invalid_mpg_car["combination_mpg"] = -10
        self.assertFalse(self.validator.is_valid(invalid_mpg_car))

    def test_ev_handles_null_values(self) -> None:
        """Ensures EVs (which have null cylinders/displacement) pass validations."""
        ev_car = {
            "make": "tesla",
            "model_name": "Model 3",
            "year": 2021,
            "class": "midsize car",
            "transmission": "Automatic",
            "drive_type": "AWD",
            "fuel_type": "Electric",
            "cylinders": None,
            "displacement": None,
            "city_mpg": 120,
            "highway_mpg": 110,
            "combination_mpg": 115
        }
        
        # Test transformation mapping of EV details
        raw_ev = {
            "make": "tesla",
            "model": "model 3",
            "year": 2021,
            "class": "midsize car",
            "transmission": "auto",
            "drive": "awd",
            "fuel_type": "electricity",
            "cylinders": None,
            "displacement": None,
            "city_mpg": 120,
            "highway_mpg": 110,
            "combination_mpg": 115
        }
        
        cleaned = self.transformer.transform_record(raw_ev)
        self.assertIsNotNone(cleaned)
        self.assertEqual(cleaned["fuel_type"], "Electric")
        self.assertIsNone(cleaned["cylinders"])
        self.assertIsNone(cleaned["displacement"])
        
        # Test validation passes
        self.assertTrue(self.validator.is_valid(cleaned))

    def test_dimension_sets_extraction(self) -> None:
        """Verifies unique list generation for lookup dimensions."""
        cleaned_batch = [
            {"make": "toyota", "class": "midsize car"},
            {"make": "honda", "class": "compact car"},
            {"make": "toyota", "class": "compact car"}
        ]
        
        makes, classes = self.transformer.extract_dimensions(cleaned_batch)
        self.assertEqual(makes, ["honda", "toyota"])
        self.assertEqual(classes, ["compact car", "midsize car"])

if __name__ == "__main__":
    unittest.main()
