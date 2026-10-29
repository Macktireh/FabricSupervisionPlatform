# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "e5a494bb-2c9c-44ec-9fd3-494add93bd08",
# META       "default_lakehouse_name": "LH_Supervision_Platform_End_User",
# META       "default_lakehouse_workspace_id": "cae55539-e164-4a36-bb47-62c5bb2cbee7",
# META       "known_lakehouses": [
# META         {
# META           "id": "e5a494bb-2c9c-44ec-9fd3-494add93bd08"
# META         }
# META       ]
# META     },
# META     "environment": {}
# META   }
# META }

# MARKDOWN ********************

# Notebook de chargement de la table **audit_logs** de la couche bronze vers la couche silver.
# 
# Pendant le chargement, un contrôle d’intégrité référentielle est mis en place. Il vérifie la correspondance :
# - `project_key` avec les projets chargés dans la `Dim_Project`
# - `asset` + `action` avec les usages chargés dans la `Dim_Usages`
# - `user` avec les utilisateurs chargés dans la `Dim_Utilisateur`
# 
# Les lignes n’ayant pas de correspondance sont rejetées dans la table de rejets `tech.rejects`.
# 
# Le chargement s’effectue en mode delta à partir de la dernière heure de chargement réussie.


# CELL ********************

from functools import reduce
from pyspark.sql.functions import col, lit, lower, trim, current_timestamp, concat_ws, when
from pyspark.sql import functions as F
from delta.tables import DeltaTable
from pyspark.sql import DataFrame

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Pour accéder à la fonctionnalité de la fonction apply_referential_checks
# qui vérifie l'intégrité référentielle

# CELL ********************

%run NB_DQ_Ref_Integrity


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Pour accéder à la fonctionnalité de la fonction merge_dataframe_into_table
# qui effectue le merge d’un DataFrame avec une table existante en supprimant
# les doublons parfaits

# CELL ********************

%run NB_Merge


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# Pour avoir la possibilité d'accéder à la classe ExecutionLogger
# qui contient les méthodes de gestion des logs d'exécution

# CELL ********************


%run NB_Utils


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

audit_execution_log = ExecutionLogger("silver", "audit_logs")
audit_execution_log.execution_start()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Récupérer le delta depuis le dernier chargement
usages = spark.read.table("bronze.audit_logs_prep").where(
    col('timestamp') >= F.to_timestamp(F.lit(audit_execution_log.get_last_execution_time()))
)


# DataFrames contenant les PK des tables de référence
dim_usage = spark.read.table("silver.dim_usage").select("asset", "activity").distinct().withColumnRenamed("activity", "action")
dim_project = spark.read.table("silver.dim_project").select("project_key").distinct().withColumnRenamed("project_key", "projectkey")
dim_users = spark.read.table("silver.dim_utilisateur").select("username").distinct().withColumnRenamed("username", "user")
dim_instance = spark.read.table("silver.dim_instance").select("instance_name").distinct().withColumnRenamed("instance_name", "instance")
rejects_count = 0

# Liste de vérifications pour la table d'audit
# On ignore les valeurs nulles dans les clés étrangères
checks = [
    {
        "name": "asset action not found in dim_usage",
        "ref_df": dim_usage,
        "keys": ["asset", "action"],
        "ignore_nulls": True
    },
    {
        "name": "projectkey not found in dim project",
        "ref_df": dim_project,
        "keys": ["projectkey"],
        "ignore_nulls": True
    },
    {
        "name": "user not found in dim_utilisateur",
        "ref_df": dim_users,
        "keys": ["user"],
        "ignore_nulls": True
    },
    {
        "name": "instance not found in dim_instance",
        "ref_df": dim_instance,
        "keys": ["instance"],
        "ignore_nulls": False
    }
]

lignes_to_load, rejects = apply_referential_checks(usages, checks)
rejects.write.format("delta") \
    .mode("append") \
    .option("overwriteSchema", "true") \
    .saveAsTable("tech.rejects")
rejects_count = rejects.count()

# On supprime les doublons parfaits pendant le merge
metrics = merge_dataframe_into_table(
    lignes_to_load,
    "silver.audit_logs",
    [
        "instance",
        "user",
        "timestamp",
        "projectkey",
        "action",
        "asset",
        "messagetype",
        "topic",
        "calltime",
        "messagetime",
        "jobid"
    ],
    True
)
metrics["rejected"] = rejects_count


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

audit_execution_log.execution_end(metrics)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
