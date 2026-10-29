-- Fabric notebook source

-- METADATA ********************

-- META {
-- META   "kernel_info": {
-- META     "name": "synapse_pyspark"
-- META   },
-- META   "dependencies": {
-- META     "lakehouse": {
-- META       "default_lakehouse": "e5a494bb-2c9c-44ec-9fd3-494add93bd08",
-- META       "default_lakehouse_name": "LH_Supervision_Platform_End_User",
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

CREATE TABLE IF NOT EXISTS tech.execution_log (
    run_id STRING NOT NULL,
    etape_name STRING NOT NULL,
    start_time TIMESTAMP NOT NULL,
    stat MAP<STRING, INT>,
    end_time TIMESTAMP
)
TBLPROPERTIES (
    'delta.enableDeletionVectors' = 'false'
);



-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

CREATE TABLE IF NOT EXISTS tech.rejects (
    reject_date TIMESTAMP NOT NULL,
    reject_reason STRING,
    reject_field STRING,
    rejected_line STRING
)
TBLPROPERTIES (
    'delta.enableDeletionVectors' = 'false'
);

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

DESCRIBE DETAIL tech.execution_log;

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

SHOW TBLPROPERTIES tech.execution_log;

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }
