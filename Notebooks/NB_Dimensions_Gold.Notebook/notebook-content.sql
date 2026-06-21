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

-- MAGIC %%pyspark
-- MAGIC %run NB_Utils

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC %run NB_Merge

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC schema = 'gold'
-- MAGIC table = 'dim_utilisateur'
-- MAGIC usage_execution_log = ExecutionLogger(schema, table)
-- MAGIC usage_execution_log.execution_start()

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

CREATE OR REPLACE TABLE gold.dim_utilisateur 
AS
SELECT 
    *,
    CASE WHEN group_norm LIKE '%service-account%' THEN
        1 
    ELSE 
        0
    END as isTechAccount
FROM silver.dim_utilisateur

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC metrics = get_last_metrics(schema + "." + table)
-- MAGIC usage_execution_log.execution_end(metrics)

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC table = 'dim_usage'
-- MAGIC usage_execution_log = ExecutionLogger(schema, table)
-- MAGIC usage_execution_log.execution_start()

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

CREATE OR REPLACE TABLE gold.dim_usage 
AS
SELECT * FROM silver.dim_usage

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC metrics = get_last_metrics(schema + "." + table)
-- MAGIC usage_execution_log.execution_end(metrics)

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC table = 'dim_project'
-- MAGIC usage_execution_log = ExecutionLogger(schema, table)
-- MAGIC usage_execution_log.execution_start()

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

CREATE OR REPLACE TABLE gold.dim_project
AS
WITH 
domains as (
    SELECT 
        *, 
        SPLIT(folder_path,"/") AS folders, 
        CASE WHEN folders[1]!='DATA-PRODUCTS' THEN 
            folders[1] 
        ELSE
            folders[2] 
        END AS domain_prep,
        CASE WHEN domain_prep='' THEN
            'HORS DOMAINE'
        ELSE
            domain_prep
        END as domain,
        CASE WHEN folders[1]!='DATA-PRODUCTS' THEN
            folders[2]
        ELSE
            NULL
        END as sub_domain
    FROM 
        silver.dim_project
)

SELECT
    id,
    project_key,
    folder_path,
    domain,
    sub_domain,
    loaded_at,
    updated_at
FROM
    domains

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC metrics = get_last_metrics(schema + "." + table)
-- MAGIC usage_execution_log.execution_end(metrics)

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC table = 'dim_licence'
-- MAGIC usage_execution_log = ExecutionLogger(schema, table)
-- MAGIC usage_execution_log.execution_start()

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

CREATE OR REPLACE TABLE gold.dim_licence 
AS 
WITH
licence_priority(priority, licence_type) as (
    VALUES(1, 'platform admin'),
    (2, 'designer'),
    (3, 'explorer'),
    (4, 'ai consumer'),
    (5, 'reader'),
    (6, 'none')
)

SELECT 
    l.*, priority 
FROM 
    silver.dim_licence l
LEFT OUTER JOIN
    licence_priority lp
ON 
    l.type = lp.licence_type

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC metrics = get_last_metrics(schema + "." + table)
-- MAGIC usage_execution_log.execution_end(metrics)

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC table = 'dim_instance_licence_utilisateur'
-- MAGIC usage_execution_log = ExecutionLogger(schema, table)
-- MAGIC usage_execution_log.execution_start()

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

CREATE OR REPLACE TABLE gold.dim_instance_licence_utilisateur 
AS
SELECT 
    ilu.*,
    FIRST(ilu.licence_id) OVER(PARTITION BY user_id ORDER BY priority) AS max_priority_licence_id
FROM 
    silver.dim_instance_licence_utilisateur ilu
INNER JOIN
    gold.Dim_Licence l
ON
    l.id = ilu.licence_id

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC metrics = get_last_metrics(schema + "." + table)
-- MAGIC usage_execution_log.execution_end(metrics)

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC table = 'dim_instance'
-- MAGIC usage_execution_log = ExecutionLogger(schema, table)
-- MAGIC usage_execution_log.execution_start()

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

CREATE OR REPLACE TABLE gold.dim_instance
AS
SELECT * FROM silver.dim_instance

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC metrics = get_last_metrics(schema + "." + table)
-- MAGIC usage_execution_log.execution_end(metrics)

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC table = 'dim_calendrier'
-- MAGIC usage_execution_log = ExecutionLogger(schema, table)
-- MAGIC usage_execution_log.execution_start()

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

CREATE OR REPLACE TABLE gold.dim_calendrier
AS
SELECT * FROM silver.dim_calendrier

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC metrics = get_last_metrics(schema + "." + table)
-- MAGIC usage_execution_log.execution_end(metrics)

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC table = 'dim_max_user_licence'
-- MAGIC usage_execution_log = ExecutionLogger(schema, table)
-- MAGIC usage_execution_log.execution_start()

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

CREATE OR REPLACE TABLE gold.dim_max_user_licence AS
WITH
dim_ilu as (
SELECT 
    DISTINCT
        username,
        user_id,
        type,
        max_priority_licence_id
FROM
    gold.dim_instance_licence_utilisateur ilu
INNER JOIN 
    gold.dim_utilisateur u
ON
    u.id = ilu.user_id
INNER JOIN
    gold.dim_licence l
ON 
    l.id = ilu.max_priority_licence_id
)

SELECT
    *,
    current_timestamp() as loaded_at,
    current_timestamp() as updated_at
FROM
    dim_ilu

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC metrics = get_last_metrics(schema + "." + table)
-- MAGIC usage_execution_log.execution_end(metrics)

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC table = 'dim_status_opt'
-- MAGIC usage_execution_log = ExecutionLogger(schema, table)
-- MAGIC usage_execution_log.execution_start()

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

CREATE OR REPLACE TABLE gold.dim_status_opt 
AS
SELECT 
    col1 as id, 
    col2 as status_label, 
    current_timestamp() as loaded_at,
    current_timestamp() as updated_at  FROM
VALUES (0, 'Inactive'),
(1, 'Sous-utilisé'),
(2, 'OK'),
(3, 'Sur-utilisé')

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC metrics = get_last_metrics(schema + "." + table)
-- MAGIC usage_execution_log.execution_end(metrics)

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }
