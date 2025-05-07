# tests/test_csv_export.py
import os
import sys
import logging
import unittest
import csv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_export.csv_exporter import save_to_csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestCSVExport(unittest.TestCase):
    """Tests for CSV export functionality"""
    
    def setUp(self):
        """Set up test case - prepare output directory"""
        # Get project root directory
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Set up paths
        self.output_dir = os.path.join(self.project_root, "data", "output", "test_exports")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Sample data for testing
        self.sample_data = [
            {
                "characteristic": "Sample Size",
                "value": "50 patients"
            },
            {
                "characteristic": "Mean Age",
                "value": "67 years"
            },
            {
                "characteristic": "Gender Distribution",
                "value": "60% male, 40% female"
            },
            {
                "characteristic": "Condition",
                "value": "Heart Failure"
            }
        ]
    
    def test_save_to_csv(self):
        """Test saving data to a CSV file"""
        # Define output path
        output_path = os.path.join(self.output_dir, "test_export.csv")
        
        # Save data to CSV
        save_to_csv(self.sample_data, output_path)
        
        # Verify the file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Read the file and verify its contents
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Verify the number of rows
            self.assertEqual(len(rows), len(self.sample_data))
            
            # Verify the content of the rows
            for i, row in enumerate(rows):
                self.assertEqual(row["characteristic"], self.sample_data[i]["characteristic"])
                self.assertEqual(row["value"], self.sample_data[i]["value"])
        
        logger.info(f"Successfully verified CSV export to {output_path}")
    
    def test_save_empty_data(self):
        """Test saving empty data to a CSV file"""
        # Define output path
        output_path = os.path.join(self.output_dir, "test_empty_export.csv")
        
        # Save empty data to CSV
        save_to_csv([], output_path)
        
        # Verify the file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Read the file and verify it has a header row with "No data available"
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Verify there's exactly one row (the header)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0], "No data available")
        
        logger.info(f"Successfully verified empty CSV export to {output_path}")
    
    def test_save_nested_data(self):
        """Test saving nested data to a CSV file with flattening"""
        # Sample nested data
        nested_data = [
            {
                "patient_id": 1,
                "demographics": {
                    "age": 65,
                    "gender": "Male"
                },
                "condition": "Hypertension"
            },
            {
                "patient_id": 2,
                "demographics": {
                    "age": 42,
                    "gender": "Female"
                },
                "condition": "Diabetes"
            }
        ]
        
        # Flatten the nested data
        flattened_data = []
        for item in nested_data:
            flat_item = {
                "patient_id": item["patient_id"],
                "age": item["demographics"]["age"],
                "gender": item["demographics"]["gender"],
                "condition": item["condition"]
            }
            flattened_data.append(flat_item)
        
        # Define output path
        output_path = os.path.join(self.output_dir, "test_nested_export.csv")
        
        # Save flattened data to CSV
        save_to_csv(flattened_data, output_path)
        
        # Verify the file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Read the file and verify its contents
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Verify the number of rows
            self.assertEqual(len(rows), len(flattened_data))
            
            # Verify the content of the rows
            for i, row in enumerate(rows):
                self.assertEqual(int(row["patient_id"]), flattened_data[i]["patient_id"])
                self.assertEqual(int(row["age"]), flattened_data[i]["age"])
                self.assertEqual(row["gender"], flattened_data[i]["gender"])
                self.assertEqual(row["condition"], flattened_data[i]["condition"])
        
        logger.info(f"Successfully verified nested data CSV export to {output_path}")

if __name__ == "__main__":
    unittest.main()