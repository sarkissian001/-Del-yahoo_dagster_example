from datetime import datetime, timedelta
import pytz

import yfinance as yf
import pandas as pd
from dagster import (
    asset,
    AssetExecutionContext,
    get_dagster_logger,
    Output,
    MetadataValue,
    RetryPolicy,
    Backoff,
    op,
)

from sqlalchemy import create_engine
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup


# List of S&P 500 symbols
# sp500_symbols = ['AAPL', 'MSFT', 'GOOGL']  # Use a few symbols for the demo


@asset(group_name='StockAssets')
def download_active_snp500_companies():
    wiki_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(wiki_url)

    # Parse data from HTML into a BeautifulSoup object
    soup = BeautifulSoup(response.text, 'html.parser')
    snp_tbl = soup.find('table', {'class': "wikitable"})

    # Convert wiki table into a Python data frame
    snp_df = pd.read_html(str(snp_tbl))[0]

    # Replace . in symbols with - to match yfinance format
    snp_list = snp_df['Symbol'].tolist()
    snp_list = [i.replace('.', '-') if '.' in i else i for i in snp_list]

    # Return the list of symbols along with metadata for the number of companies
    return Output(
        snp_list,
        metadata={
            "company_count": len(snp_list),  # Count of companies
            "preview": MetadataValue.md(snp_df.head().to_markdown())  # Optional: preview of first few rows
        }
    )


@asset(group_name='StockAssets',
    compute_kind='Pandas',
    tags={"action": "data_extraction"},
    retry_policy=RetryPolicy(max_retries=3, delay=0.2, backoff=Backoff.EXPONENTIAL),)
def pull_stock_data(download_active_snp500_companies):
    logger = get_dagster_logger()
    data = pd.DataFrame()
    now_utc = datetime.now(pytz.UTC)  # Get the current time in UTC
    three_hours_ago_utc = now_utc - timedelta(hours=3)  # Set the time to 3 hours ago

    for symbol in download_active_snp500_companies:
        
        try:
            # Download the stock data for each symbol (1-minute interval for the past day)
            stock_data = yf.download(symbol, period="1d", interval="1m", prepost=True)  # prepost=True includes pre and post market data
            
            # Ensure the index is in UTC timezone
            stock_data.index = stock_data.index.tz_localize('UTC') if stock_data.index.tzinfo is None else stock_data.index.tz_convert('UTC')
            
            # Filter the data to include only the last 3 hours in UTC
            filtered_data = stock_data[stock_data.index >= three_hours_ago_utc]
            filtered_data["Symbol"] = symbol
            filtered_data["ingestion_time"] = datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S.%f")
            data = pd.concat([data, filtered_data])
        
        except Exception as e:
            logger.warning(f"Failed to download stock data for {symbol}: {e}")  
        
    logger.info("Pulled stock data successfully!")    
    return Output(
        data,
        metadata={
            "num_records": len(data), 
            "size": data.size,
            "preview": MetadataValue.md(data.head().to_markdown()),
        }
    )





# Define the asset to push data to MongoDB
@asset(group_name='StockAssets', metadata={"action": "data_push"})
def push_to_mongo(pull_stock_data):
    # Establish MongoDB connection
    client = MongoClient("mongodb://mongo:27017/")
    db = client["stock_db"]
    collection = db["stocks_raw_layer"]
    
    # Initialize logger
    logger = get_dagster_logger()
    logger.info("Pushing stock data to MongoDB")

    # Check if the input is a DataFrame
    if pull_stock_data.empty:
        logger.warning("Received empty DataFrame, nothing to push")
        return

    # Convert the DataFrame to a dictionary of records for MongoDB insertion
    stock_records = pull_stock_data.to_dict("records")

    # Insert records into MongoDB
    if stock_records:
        collection.insert_many(stock_records)
        logger.info(f"Successfully pushed {len(stock_records)} records to MongoDB")
    else:
        logger.warning("No data to push")

    # Close the MongoDB connection
    client.close()
    logger.info("MongoDB connection closed")



# Transform and push freshest data to the golden layer
@asset(group_name='StockAssets', metadata={"action": "data_transform"})
def push_to_golden_layer(push_to_mongo):
    client = MongoClient("mongodb://mongo:27017/")
    db = client["stock_db"]
    raw_collection = db["stocks_raw_layer"]
    golden_collection = db["stocks_golden_layer"]
    
    logger = get_dagster_logger()
    logger.info("Transforming data from raw to golden layer using MongoDB aggregation pipeline")

    ten_minutes_ago = datetime.now(pytz.UTC) - timedelta(minutes=1)

    pipeline = [
        {
            "$match": {
                "ingestion_time": {
                    "$gte": ten_minutes_ago.strftime("%Y-%m-%d %H:%M:%S.%f")
                }
            }
        },
        {
            "$out": "stocks_golden_layer"
        }
    ]

    raw_collection.aggregate(pipeline)

    logger.info("Successfully transformed and pushed records from raw layer to golden layer")
    client.close()
    logger.info("MongoDB connection closed")