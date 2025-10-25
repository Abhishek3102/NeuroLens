import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Dict, Any

# --- Import the new settings ---
from .config import settings

# --- Constants are now read from settings ---
MONGO_CONNECTION_STRING = settings.MONGO_CONNECTION_STRING
DATABASE_NAME = settings.DATABASE_NAME
COLLECTION_NAME = "logs"

logger = logging.getLogger(__name__)

async def connect_to_mongo() -> AsyncIOMotorClient:
    """Establishes an asynchronous connection to MongoDB."""
    logger.info("Attempting to connect to MongoDB...")
    try:
        client = AsyncIOMotorClient(MONGO_CONNECTION_STRING, serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        logger.info("MongoDB connection successful.")
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        await collection.create_index("target_role")
        logger.info(f"Index on 'target_role' ensured in '{COLLECTION_NAME}'.")
        
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"MongoDB connection failed: {e}", exc_info=True)
        return None

async def close_mongo_connection(client: AsyncIOMotorClient):
    """Closes the MongoDB connection."""
    if client:
        client.close()
        logger.info("MongoDB connection closed.")

async def log_analysis_to_db(client: AsyncIOMotorClient, log_document: Dict[str, Any]):
    """Logs a single analysis document to the MongoDB collection."""
    try:
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        await collection.insert_one(log_document)
        logger.info(f"Logged analysis for {log_document.get('file_name')} to MongoDB.")
    except Exception as e:
        logger.error(f"Failed to log analysis to MongoDB: {e}", exc_info=True)

async def get_analysis_metrics(client: AsyncIOMotorClient) -> Dict[str, Any]:
    """Calculates aggregate metrics from the MongoDB logs."""
    metrics = {
        "total_analyses": 0,
        "avg_duration_ms": 0,
        "avg_score": 0,
        "role_breakdown": []
    }
    try:
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # MongoDB Aggregation Pipeline
        pipeline = [
            {
                "$facet": {
                    "overview": [
                        {
                            "$group": {
                                "_id": None,
                                "total_analyses": { "$sum": 1 },
                                "avg_duration_ms": { "$avg": "$analysis_duration_ms" },
                                "avg_score": { "$avg": "$match_score" }
                            }
                        }
                    ],
                    "role_breakdown": [
                        {
                            "$group": {
                                "_id": "$target_role",
                                "count": { "$sum": 1 }
                            }
                        },
                        { "$sort": { "count": -1 } }
                    ]
                }
            }
        ]
        
        result = await collection.aggregate(pipeline).to_list(1)
        
        if result:
            if result[0]["overview"]:
                overview_data = result[0]["overview"][0]
                metrics["total_analyses"] = overview_data.get("total_analyses", 0)
                metrics["avg_duration_ms"] = overview_data.get("avg_duration_ms", 0)
                metrics["avg_score"] = overview_data.get("avg_score", 0)
            
            if result[0]["role_breakdown"]:
                metrics["role_breakdown"] = result[0]["role_breakdown"]
                
        logger.info("Successfully fetched /metrics data.")
            
    except Exception as e:
        logger.error(f"Error fetching analysis metrics from MongoDB: {e}", exc_info=True)
            
    return metrics




