# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************


from pyspark.sql import functions as F
from delta.tables import DeltaTable
from pyspark.sql import DataFrame

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

def get_last_metrics_dlt(table: DeltaTable) -> dict[str, int]:
    """
    Récupère les métriques de la dernière opération réalisée sur une table Delta.

    Paramètres
    ----------
    table : DeltaTable
        Instance DeltaTable représentant la table cible dont on veut lire l'historique.

    Retour
    ------
    dict[str, int]
        Dictionnaire contenant :
        - "inserted" : nombre de lignes insérées lors de la dernière opération (0 si absent),
        - "updated"  : nombre de lignes mises à jour lors de la dernière opération (0 si absent).
    """
    metrics = (
        table.history(1)
        .select("operationMetrics")
        .first()["operationMetrics"]
    )
    return {
        "inserted": int(metrics.get("numTargetRowsInserted", 0)),
        "updated": int(metrics.get("numTargetRowsUpdated", 0)),
        "output_rows": int(metrics.get("numOutputRows", 0))
    }

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

def get_last_metrics(table_name:str) -> dict[str,int]:
    target = DeltaTable.forName(spark, table_name)
    return get_last_metrics_dlt(target)
    

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

def merge_dataframe_into_table(
    df: DataFrame,
    target_table: str,
    keys: list[str],
    dropDuplicates: bool = True
) -> dict[str, int]:
    """
    Effectue un merge générique d'un DataFrame dans une table Delta existante
    (ou la crée si elle n'existe pas).

    - Si la table n'existe pas encore, elle est créée à partir du DataFrame
      source (en écriture Delta, mode overwrite).
    - Si la table existe, un MERGE est réalisé sur les colonnes clés
      (null-safe) :
        * whenMatchedUpdate : mise à jour de toutes les colonnes non clés
          (sauf "loaded_at").
        * whenNotMatchedInsert : insertion de toutes les colonnes.
    - Deux colonnes techniques sont ajoutées dans le flux source :
        * "updated_at" : horodatage de l'opération,
        * "loaded_at"  : horodatage de l'opération.

    Paramètres
    ----------
    df : pyspark.sql.DataFrame
        DataFrame source à fusionner dans la table Delta cible.
        Si `df.count() == 0`, aucune opération n'est effectuée.
    target_table : str
        Nom complet de la table Delta cible.
    keys : list[str]
        Liste des noms de colonnes servant de clés de correspondance
        pour le MERGE. Toutes ces colonnes doivent être présentes dans
        le DataFrame. Si la liste est vide, une ValueError est levée.
    dropDuplicates : bool, optionnel (défaut = True)
        Si True, applique `df.dropDuplicates()` avant d'exécuter le merge
        afin de réduire les doublons potentiels dans la source.

    Retour
    ------
    dict[str, int]
        Dictionnaire contenant les métriques de la DERNIÈRE opération sur
        la table Delta (telles que renvoyées par l'historique Delta) :
        - "inserted" : nombre de lignes insérées,
        - "updated"  : nombre de lignes mises à jour.

        Cas particuliers :
        - Si `df.count() == 0`, retourne {"inserted": 0, "updated": 0}.

    Exceptions
    ----------
    ValueError
        Levée si la liste `keys` est vide ou si une ou plusieurs colonnes
        clés sont absentes du DataFrame source.

    """
    # rien à faire, on sort
    if df.count() == 0:
        return {
            "inserted": 0,
            "updated": 0,
        }
    if not keys:
        raise ValueError("keys list cannot be empty")

    missing_keys = [c for c in keys if c not in df.columns]
    if missing_keys:
        raise ValueError(f"Key columns missing from dataframe: {missing_keys}")

    operation_ts = F.current_timestamp()

    spark = df.sparkSession
    table_exists = spark.catalog.tableExists(target_table)
    
    if dropDuplicates:
        df = df.dropDuplicates()

    source_df = (
        df
        .withColumn("updated_at", operation_ts)
        .withColumn("loaded_at", operation_ts)
    )
    if not table_exists:
        (
            source_df.write
            .format("delta")
            .mode("overwrite")
            .saveAsTable(target_table)
        )
        return get_last_metrics(target_table)

    target = DeltaTable.forName(df.sparkSession, target_table)
    # null-safe comparaison
    merge_condition = " AND ".join(
        [f"target.`{key}` <=> source.`{key}`" for key in keys]
    )

    update_columns = [
        c for c in source_df.columns
        if (c not in keys) and (c not in ("loaded_at"))
    ]
    
    update_set = {
        c: f"source.`{c}`"
        for c in update_columns
    }

    insert_set = {
        c: f"source.`{c}`"
        for c in source_df.columns
    }

    (
        target.alias("target")
        .merge(
            source_df.alias("source"),
            merge_condition
        )
        .whenMatchedUpdate(set=update_set)
        .whenNotMatchedInsert(values=insert_set)
        .execute()
    )
    # on recoupère la stat pour les lignes maj/inserées/etc.
    # hypothèse : pas d'ecritures après notre execution et récuperation d'historie
    return get_last_metrics_dlt(target)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
