-- Fabric notebook source

-- METADATA ********************

-- META {
-- META   "kernel_info": {
-- META     "name": "synapse_pyspark"
-- META   },
-- META   "dependencies": {
-- META     "lakehouse": {
-- META       "default_lakehouse": "e5a494bb-2c9c-44ec-9fd3-494add93bd08",
-- META       "default_lakehouse_name": "Lakehouse_End_User_Platform",
-- META       "default_lakehouse_workspace_id": "cae55539-e164-4a36-bb47-62c5bb2cbee7",
-- META       "known_lakehouses": [
-- META         {
-- META           "id": "e5a494bb-2c9c-44ec-9fd3-494add93bd08"
-- META         }
-- META       ]
-- META     }
-- META   }
-- META }

-- CELL ********************

CREATE SCHEMA IF NOT EXISTS tech;

CREATE OR REPLACE TABLE tech.execution_log(
  run_id STRING NOT NULL,             -- surrogate key start_time|etape_name
  etape_name STRING NOT NULL,
  start_time TIMESTAMP NOT NULL,
  stat MAP<STRING, INT>,
  end_time TIMESTAMP
);

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

CREATE OR REPLACE TABLE tech.rejects(
    reject_date TIMESTAMP NOT NULL,
    reject_reason STRING,
    reject_field STRING,
    rejected_line STRING
)

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }
