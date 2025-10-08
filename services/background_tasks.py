import asyncio
from datetime import datetime
from typing import Dict, Any
import logging
from .occComparison import compare_models

async def process_model_comparison(
    submission_id: str,
    submitted_path: str,
    reference_path: str,
    submissions_collection: Any
) -> None:
    """Process model comparison in background"""
    try:
        start_time = datetime.utcnow()
        logging.info(f"Starting background comparison for submission {submission_id}")
        
        # Do the comparison
        result = compare_models(submitted_path, reference_path)
        
        # Calculate time taken
        time_taken = (datetime.utcnow() - start_time).total_seconds()
        logging.info(f"Comparison completed in {time_taken:.2f} seconds")
        
        # Update submission with results
        await submissions_collection.update_one(
            {"_id": submission_id},
            {
                "$set": {
                    "status": "completed",
                    "cad_comparison": result,
                    "processing_time": time_taken,
                    "completed_at": datetime.utcnow()
                }
            }
        )
    except Exception as e:
        logging.error(f"Error in background comparison: {str(e)}")
        await submissions_collection.update_one(
            {"_id": submission_id},
            {
                "$set": {
                    "status": "error",
                    "error": str(e),
                    "completed_at": datetime.utcnow()
                }
            }
        )