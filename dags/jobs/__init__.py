from dagster import define_asset_job, in_process_executor, graph, FilesystemIOManager


# ETL_JOB = define_asset_job(name="etl_job", selection="StockAssets",)
ETL_JOB = define_asset_job(name="etl_job", selection="*",)