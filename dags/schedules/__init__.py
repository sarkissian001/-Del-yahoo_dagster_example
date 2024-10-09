from dagster import schedule

from jobs import ETL_JOB

@schedule(cron_schedule="*/1 * * * *", job=ETL_JOB)
def etl_job_schedule(_context):
    
    return {}
