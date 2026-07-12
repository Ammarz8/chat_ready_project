import sys
from typing import List, Dict, Any, Optional
from cli_app.queries import VehicleAnalyticsQueries

class CLIMenu:
    """
    Manages terminal rendering, navigation menu loops, user prompt captures,
    and formatted display of analytical reports.
    """
    def __init__(self, queries: VehicleAnalyticsQueries):
        self._queries = queries

    def clear_screen(self) -> None:
        """Prints ansi code to clear terminal screen for cleaner UI."""
        print("\033[H\033[J", end="")

    def format_table(self, headers: List[str], rows: List[List[Any]]) -> None:
        """
        Custom, dependency-free grid formatting tool.
        Calculates column widths dynamically and renders bordered tables.
        """
        if not rows:
            print("\n  [!] No records available to display.")
            return

        # Determine max width for each column dynamically
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                val_str = str(val) if val is not None else "N/A"
                if len(val_str) > col_widths[i]:
                    col_widths[i] = len(val_str)

        # Print horizontal divider line
        divider = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
        
        print("\n" + divider)
        # Print Header Row
        header_row = "|" + "|".join([f" {headers[i].upper():<{col_widths[i]}} " for i in range(len(headers))]) + "|"
        print(header_row)
        print(divider)
        
        # Print Data Rows
        for row in rows:
            data_row = "|" + "|".join([
                f" {str(row[i]) if row[i] is not None else 'N/A':<{col_widths[i]}} " 
                for i in range(len(row))
            ]) + "|"
            print(data_row)
            
        print(divider + "\n")

    def show_header(self) -> None:
        """Renders standard ASCII title block."""
        print("=" * 60)
        print("          CAR SPECIFICATIONS ANALYTICS ENGINE (SILVER LAYER)   ")
        print("=" * 60)

    def print_menu_options(self) -> None:
        """Lists CLI operations."""
        print("  1. Search Vehicles by Manufacturer (Make)")
        print("  2. Search Vehicles by Production Year")
        print("  3. List All Available Manufacturers")
        print("  4. View Fuel Efficiency Stats by Fuel Type")
        print("  5. View Fuel Efficiency Stats by Vehicle Class")
        print("  6. View Dataset High-level Summary Metrics")
        print("  7. Exit Application")
        print("-" * 60)

    def run(self) -> None:
        """Main navigation prompt loop."""
        while True:
            self.clear_screen()
            self.show_header()
            self.print_menu_options()
            
            choice = input("Select an option (1-7): ").strip()
            
            if choice == "1":
                self.handle_search_by_make()
            elif choice == "2":
                self.handle_search_by_year()
            elif choice == "3":
                self.handle_list_makes()
            elif choice == "4":
                self.handle_stats_by_fuel()
            elif choice == "5":
                self.handle_stats_by_class()
            elif choice == "6":
                self.handle_summary_stats()
            elif choice == "7":
                print("\nExiting. Thank you for using the Analytics Engine.\n")
                break
            else:
                input("\nInvalid option. Press Enter to try again...")

    def handle_search_by_make(self) -> None:
        self.clear_screen()
        self.show_header()
        print("  [ SEARCH BY MANUFACTURER ]\n")
        make = input("Enter manufacturer name (or part of it): ").strip()
        if not make:
            input("\nSearch value cannot be empty. Press Enter to return...")
            return

        logger_msg = f"Searching for make: {make}"
        print(f"\n  Querying database for '{make}'...")
        records = self._queries.search_by_make(make)
        
        headers = ["Make", "Model", "Year", "Class", "Trans", "Drive", "Fuel", "Cyl", "Displ (L)", "Comb MPG"]
        rows = []
        for r in records:
            rows.append([
                r["make"].title(),
                r["model_name"],
                r["year"],
                r["class_name"].title() if r["class_name"] else None,
                r["transmission"],
                r["drive_type"],
                r["fuel_type"],
                r["cylinders"],
                r["displacement"],
                r["combination_mpg"]
            ])

        print(f"\n  Found {len(records)} matching records:")
        self.format_table(headers, rows)
        input("Press Enter to return to main menu...")

    def handle_search_by_year(self) -> None:
        self.clear_screen()
        self.show_header()
        print("  [ SEARCH BY YEAR ]\n")
        year_str = input("Enter production year (e.g. 2022): ").strip()
        if not year_str.isdigit():
            input("\nError: Year must be a positive integer. Press Enter to return...")
            return

        year = int(year_str)
        print(f"\n  Querying database for year {year}...")
        records = self._queries.search_by_year(year)
        
        headers = ["Make", "Model", "Year", "Class", "Trans", "Drive", "Fuel", "Cyl", "Displ (L)", "Comb MPG"]
        rows = []
        for r in records:
            rows.append([
                r["make"].title(),
                r["model_name"],
                r["year"],
                r["class_name"].title() if r["class_name"] else None,
                r["transmission"],
                r["drive_type"],
                r["fuel_type"],
                r["cylinders"],
                r["displacement"],
                r["combination_mpg"]
            ])

        print(f"\n  Found {len(records)} matching records:")
        self.format_table(headers, rows)
        input("Press Enter to return to main menu...")

    def handle_list_makes(self) -> None:
        self.clear_screen()
        self.show_header()
        print("  [ AVAILABLE MANUFACTURERS ]\n")
        
        makes = self._queries.get_all_makes()
        headers = ["ID", "Manufacturer Name"]
        rows = [[i + 1, make.title()] for i, make in enumerate(makes)]
        
        print(f"  Total unique manufacturers: {len(makes)}")
        self.format_table(headers, rows)
        input("Press Enter to return to main menu...")

    def handle_stats_by_fuel(self) -> None:
        self.clear_screen()
        self.show_header()
        print("  [ FUEL EFFICIENCY BY FUEL TYPE ]\n")
        
        stats = self._queries.get_efficiency_by_fuel_type()
        headers = ["Fuel Type", "Average MPG", "Min MPG", "Max MPG", "Models Count"]
        rows = []
        for s in stats:
            rows.append([
                s["fuel_type"],
                s["avg_mpg"],
                s["min_mpg"],
                s["max_mpg"],
                s["model_count"]
            ])
            
        self.format_table(headers, rows)
        input("Press Enter to return to main menu...")

    def handle_stats_by_class(self) -> None:
        self.clear_screen()
        self.show_header()
        print("  [ FUEL EFFICIENCY BY VEHICLE CLASS ]\n")
        
        stats = self._queries.get_efficiency_by_class()
        headers = ["Vehicle Class", "Average MPG", "Min MPG", "Max MPG", "Models Count"]
        rows = []
        for s in stats:
            rows.append([
                s["class_name"].title(),
                s["avg_mpg"],
                s["min_mpg"],
                s["max_mpg"],
                s["model_count"]
            ])
            
        self.format_table(headers, rows)
        input("Press Enter to return to main menu...")

    def handle_summary_stats(self) -> None:
        self.clear_screen()
        self.show_header()
        print("  [ HIGH-LEVEL DATASET METRICS ]\n")
        
        s = self._queries.get_database_summary_stats()
        if not s or s.get("total_models") == 0:
            print("  [!] Target analytical database is currently empty. Run Extractor & Transformer first.")
        else:
            print(f"  * Total Vehicle Models Recorded:  {s['total_models']}")
            print(f"  * Unique Manufacturers Available: {s['total_makes']}")
            print(f"  * Unique Vehicle Classes:         {s['total_classes']}")
            print(f"  * Model Year Coverage Range:       {s['min_year']} - {s['max_year']}")
            print(f"  * Fleet Combined Average MPG:     {s['avg_mpg']} MPG")
        
        print("\n" + "=" * 60 + "\n")
        input("Press Enter to return to main menu...")
