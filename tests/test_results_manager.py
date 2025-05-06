# tests/test_results_manager.py
"""
Test module for the results management functionality
"""
import os
import sys
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import the ResultsManager
from src.utils.results_manager import ResultsManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_results_manager():
    """Test the ResultsManager class with sample data"""
    try:
        # Create a ResultsManager
        logger.info("Creating ResultsManager...")
        manager = ResultsManager()
        
        # Create some sample extraction results
        sample_results = [
            {
                "sample_size": "75 patients",
                "condition": "type 2 diabetes mellitus",
                "age_range": "45-70 years",
                "mean_age": "58.3 years",
                "gender_distribution": "60% male, 40% female"
            },
            {
                "sample_size": "150 patients",
                "condition": "hypertension",
                "age_range": "35-65 years",
                "mean_age": "52.7 years",
                "gender_distribution": "55% female, 45% male",
                "blood_pressure": "systolic > 140 mmHg"
            }
        ]
        
        # Save the sample results
        logger.info("Saving sample extraction results...")
        result_ids = []
        
        for i, result in enumerate(sample_results):
            # Create fake source file paths
            source_file = f"sample_article_{i+1}.pdf"
            
            # Create model info
            model_info = {
                "provider": "mock",
                "model_name": f"test-model-{i+1}"
            }
            
            # Save the result
            result_id = manager.save_extraction_result(
                result=result,
                source_file=source_file,
                model_info=model_info,
                prompt_id=f"test-prompt-{i+1}",
                metadata={"test_run": True}
            )
            
            result_ids.append(result_id)
            logger.info(f"Saved result with ID: {result_id}")
        
        # Test retrieving a result
        logger.info(f"Retrieving result {result_ids[0]}...")
        retrieved_result = manager.get_result(result_ids[0])
        logger.info(f"Retrieved result data: {retrieved_result['data']}")
        
        # Test listing results
        logger.info("Listing all results...")
        all_results = manager.list_results()
        logger.info(f"Found {len(all_results)} results")
        
        # Test filtering results
        logger.info("Filtering results by source file...")
        filtered_results = manager.list_results(filter_by={"source_file": "sample_article_1.pdf"})
        logger.info(f"Found {len(filtered_results)} matching results")
        
        # Test exporting to CSV
        logger.info("Exporting results to CSV...")
        csv_path = manager.export_to_csv()
        logger.info(f"Exported results to {csv_path}")
        
        # Test comparing results
        if len(result_ids) >= 2:
            logger.info(f"Comparing results {result_ids[0]} and {result_ids[1]}...")
            comparison = manager.compare_results([result_ids[0], result_ids[1]])
            logger.info(f"Comparison results: {comparison}")
        
        # Test getting statistics
        logger.info("Getting result statistics...")
        stats = manager.get_result_stats()
        logger.info(f"Result statistics: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in test_results_manager: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    test_successful = test_results_manager()
    logger.info(f"Test completed. Success: {test_successful}")