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

CREATE SCHEMA IF NOT EXISTS gold;

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

CREATE TABLE IF NOT EXISTS gold.fait_usage_dataiku_utilisateur(
    id                          bigint,
    instance_id                 bigint,
    user_id                     bigint,
    project_id                  bigint,
    timestamp_dt                date,
    session_number              bigint,
    usage_id                    bigint,
    session_start               timestamp,
    session_end                 timestamp,
    session_duration_seconds    bigint,
    session_duration_minutes    bigint,
    jobs_count                  bigint,
    scenarios_count             bigint,
    loaded_at                   timestamp,
    updated_at                  timestamp
)

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }
