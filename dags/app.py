from dagster import Definitions

from assets.financeAssets import pull_stock_data, push_to_mongo, push_to_golden_layer, download_active_snp500_companies


from jobs import ETL_JOB

from schedules import etl_job_schedule 



# Define all assets
asset_definitions = [
    download_active_snp500_companies,
    pull_stock_data,
    push_to_mongo,
    push_to_golden_layer
]

# Define all jobs
job_definitions = [
    ETL_JOB,
]

# Define all schedules
schedule_definitions = [
    etl_job_schedule,
]



# Combine all definitions
defs = Definitions(
    assets=asset_definitions,
    jobs=job_definitions,
    schedules=schedule_definitions,
)
