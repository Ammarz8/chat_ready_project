from typing import List, Dict, Any
from cli_app.database import TargetDatabaseClient

class VehicleAnalyticsQueries:
    """
    Houses pre-compiled, optimized SQL queries and mapping utilities 
    for pulling data from target_db (Silver Layer).
    """
    def __init__(self, db_client: TargetDatabaseClient):
        self._db = db_client

    def get_all_makes(self) -> List[str]:
        """Retrieves a list of all unique manufacturer names in the database."""
        query = "SELECT name FROM makes ORDER BY name ASC;"
        results = self._db.execute_query(query)
        return [row["name"] for row in results]

    def search_by_make(self, make_name: str) -> List[Dict[str, Any]]:
        """
        Queries all vehicle specifications for a given manufacturer (make).
        Uses case-insensitive pattern matching.
        """
        query = """
            SELECT 
                m.model_name, 
                m.year, 
                mk.name AS make, 
                vc.name AS class_name, 
                m.transmission, 
                m.drive_type, 
                m.fuel_type, 
                m.cylinders, 
                m.displacement, 
                m.city_mpg,
                m.highway_mpg,
                m.combination_mpg 
            FROM car_models m 
            JOIN makes mk ON m.make_id = mk.make_id 
            LEFT JOIN vehicle_classes vc ON m.class_id = vc.class_id 
            WHERE mk.name ILIKE %s 
            ORDER BY m.year DESC, m.model_name ASC;
        """
        # Wrap string in wildcards to allow partial matches
        return self._db.execute_query(query, (f"%{make_name}%",))

    def search_by_year(self, year: int) -> List[Dict[str, Any]]:
        """Queries all vehicle specifications produced in a specific year."""
        query = """
            SELECT 
                m.model_name, 
                m.year, 
                mk.name AS make, 
                vc.name AS class_name, 
                m.transmission, 
                m.drive_type, 
                m.fuel_type, 
                m.cylinders, 
                m.displacement, 
                m.city_mpg,
                m.highway_mpg,
                m.combination_mpg 
            FROM car_models m 
            JOIN makes mk ON m.make_id = mk.make_id 
            LEFT JOIN vehicle_classes vc ON m.class_id = vc.class_id 
            WHERE m.year = %s 
            ORDER BY mk.name ASC, m.model_name ASC;
        """
        return self._db.execute_query(query, (year,))

    def get_efficiency_by_fuel_type(self) -> List[Dict[str, Any]]:
        """Retrieves aggregated efficiency statistics grouped by fuel type."""
        query = """
            SELECT 
                fuel_type, 
                ROUND(AVG(combination_mpg), 1) AS avg_mpg, 
                MIN(combination_mpg) AS min_mpg,
                MAX(combination_mpg) AS max_mpg,
                COUNT(*) AS model_count 
            FROM car_models 
            WHERE fuel_type IS NOT NULL 
            GROUP BY fuel_type 
            ORDER BY avg_mpg DESC;
        """
        return self._db.execute_query(query)

    def get_efficiency_by_class(self) -> List[Dict[str, Any]]:
        """Retrieves aggregated efficiency statistics grouped by vehicle class."""
        query = """
            SELECT 
                vc.name AS class_name, 
                ROUND(AVG(m.combination_mpg), 1) AS avg_mpg, 
                MIN(m.combination_mpg) AS min_mpg,
                MAX(m.combination_mpg) AS max_mpg,
                COUNT(*) AS model_count 
            FROM car_models m 
            JOIN vehicle_classes vc ON m.class_id = vc.class_id 
            GROUP BY vc.name 
            ORDER BY avg_mpg DESC;
        """
        return self._db.execute_query(query)

    def get_database_summary_stats(self) -> Dict[str, Any]:
        """Retrieves high-level summary metrics about the entire dataset."""
        query = """
            SELECT 
                COUNT(*) AS total_models, 
                COUNT(DISTINCT make_id) AS total_makes, 
                COUNT(DISTINCT class_id) AS total_classes,
                MIN(year) AS min_year, 
                MAX(year) AS max_year, 
                ROUND(AVG(combination_mpg), 1) AS avg_mpg 
            FROM car_models;
        """
        results = self._db.execute_query(query)
        return results[0] if results else {}
