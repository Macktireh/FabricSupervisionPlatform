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
-- MAGIC licence_execution_log = ExecutionLogger('gold', 'Fait_Licence_Dataiku')
-- MAGIC licence_execution_log.execution_start()


-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- Welcome to your new notebook
-- Type here in the cell editor to add code!

--CREATE OR REPLACE TABLE gold.fait_licence_dataiku
/*MERGE INTO gold.fait_licence_dataiku AS tgt
USING (*/
WITH
 
dim_utilisateur AS (
    SELECT DISTINCT
        i.instance_name AS instance,
        i.id            AS instance_id,
        u.username      AS login,
        ilu.licence_id,
        ilu.user_id,
        ilu.snapshot_dt AS snapshot_date,
        UPPER(l.type)   AS userprofile,
        MIN(ilu.snapshot_dt) OVER (
            PARTITION BY i.instance_name, u.username, l.type
            ORDER BY ilu.snapshot_dt
        )               AS first_connection,
        ilu.creationdate
    FROM gold.dim_utilisateur u
    INNER JOIN gold.dim_Instance_Licence_Utilisateur ilu
        ON u.id = ilu.user_id
        -- AND u.snapshot_dt = ilu.snapshot_dt
    INNER JOIN gold.dim_instance i
        ON i.id = ilu.instance_id
    INNER JOIN gold.Dim_Licence l
        ON l.id = ilu.licence_id
),

dim_environnement AS (
   SELECT instance_name as instance, id from gold.dim_instance
),

users_snapshots AS (
    SELECT DISTINCT
        temps_env.instance,
        temps_env.instance_id,
        temps_env.date_jour,
        temps_env.userprofile,
        temps_env.login,
        temps_env.user_id,
        temps_env.licence_id,
        temps_env.creationdate,
        temps_env.first_connection
    FROM (
        SELECT
            e.instance,
            e.id as instance_id,
            u.user_id,
            snapshot_date as date_jour,
            u.userprofile,
            u.login,
            u.licence_id,
            u.creationdate,
            u.first_connection
        FROM dim_environnement e
        LEFT OUTER JOIN dim_utilisateur u
            ON u.instance      = e.instance
    ) temps_env
),

user_events AS (
    SELECT DISTINCT
        instance,
        user         AS login,
        timestamp_dt
    FROM bronze.audit_logs_prep a
    -- ?
),

match_user_audit_event AS (
    SELECT DISTINCT
        res.instance,
        res.instance_id,
        res.login,
        res.user_id,
        res.licence_id,
        res.date_jour,
        res.userprofile,
        res.creationdate,
        res.first_connection,
        MAX(res.timestamp) OVER (
            PARTITION BY res.instance, res.login, res.userprofile
            ORDER BY res.date_jour
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS derniere_user_date_action
    FROM (
        SELECT
            u.instance,
            u.instance_id,
            u.login,
            u.user_id,
            u.licence_id,
            u.date_jour,
            u.creationdate,
            u.first_connection,
            UPPER(u.userprofile)          AS userprofile,
            ue.timestamp_dt                           AS timestamp
        FROM users_snapshots u
        LEFT OUTER JOIN user_events ue
            ON ue.instance    = u.instance
           AND ue.login       = u.login
           AND ue.timestamp_dt = u.date_jour
    ) res
),

last_usage_nb_profils AS (
    SELECT
        instance,
        instance_id,
        login,
        licence_id,
        user_id,
        date_jour,
        userprofile,
        creationdate,
        first_connection,
        COALESCE(
            derniere_user_date_action,
            LAG(derniere_user_date_action, 1) OVER (
                PARTITION BY instance, userprofile, login, date_jour
                ORDER BY date_jour
            )
        ) AS dernire_user_date_action
    FROM match_user_audit_event e1
)

SELECT
    xxhash64(
        array_join(
            array(
                instance_id,
                user_id,
                licence_id,
                CAST(date_format(date_jour, 'yyyyMMdd') AS BIGINT)
            ),
            '|'
        )
    )                        AS id,
    instance_id,
    user_id,
    date_jour,
    licence_id,
    creationdate,
    dernire_user_date_action,
    first_connection,
    current_timestamp         AS loaded_at,
    current_timestamp         AS updated_at
FROM last_usage_nb_profils
WHERE instance IS NOT NULL
and user_id=1976824888885209769
/*)AS src
ON tgt.id = src.id

WHEN MATCHED THEN UPDATE SET
    tgt.instance_id                     = src.instance_id,
    tgt.user_id                         = src.user_id,
    tgt.date_jour                       = src.date_jour,
    tgt.licence_id                      = src.licence_id,
    tgt.creationdate                    = src.creationdate,
    tgt.dernire_user_date_action        = src.dernire_user_date_action,
    tgt.first_connection                = src.first_connection,
    tgt.updated_at                      = current_timestamp

WHEN NOT MATCHED THEN INSERT (
    instance_id,
    user_id,
    date_jour,
    licence_id,
    creationdate,
    dernire_user_date_action,
    first_connection,
    loaded_at,
    updated_at
)
VALUES (
    src.instance_id,
    src.user_id,
    src.date_jour,
    src.licence_id,
    src.creationdate,
    src.dernire_user_date_action,
    src.first_connection,
    src.loaded_at,
    src.updated_at
); */

-- METADATA ********************

-- META {
-- META   "language": "sparksql",
-- META   "language_group": "synapse_pyspark"
-- META }

-- CELL ********************

-- MAGIC %%pyspark
-- MAGIC licence_execution_log.execution_end()

-- METADATA ********************

-- META {
-- META   "language": "python",
-- META   "language_group": "synapse_pyspark"
-- META }
