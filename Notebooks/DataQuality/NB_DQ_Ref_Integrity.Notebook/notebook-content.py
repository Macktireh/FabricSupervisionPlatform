# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

from functools import reduce
from pyspark.sql.functions import col, lit, lower, trim, current_timestamp, concat_ws, concat
from pyspark.sql import functions as F

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

def apply_referential_checks(df, checks):
    """
    Vérifie l'integrité de FK pour le dataframe df et table de 
    reference indiquée dans le parameter check.

    format de la liste checks:
    checks = [
        {
            "name": "usage_exists",         --> nom sera affiché dans la dataframe de rejets
            "ref_df": dim_usage_df,         --> dataframe de référence 
            "keys": ["asset", "action"],    --> la liste des champs clés
            "ignore_nulls": True            --> si la FK peut être null (on l'ignore dans ce cas)
        },
        ...
    ]

    returne :
        data frame nettoyé
        data frame des rejets au format suivant:  
        (date de rejet, cause de rejet (checks.name), champs vérifiés (checks.keys), ligné rejetée)
        Les deux derniers champs contiennent tous les champs necessaires concaténés en string avec le séparateur "|"
    """
    clean_df = df
    reject_dfs = []
    all_columns = [c for c in df.columns]
    for check in checks:

        keys = check["keys"]

        ref_df = (
            check["ref_df"]
            .select(*keys)
            .distinct()
        )

        ignore_nulls = check.get("ignore_nulls", True)

        # condition : toutes les clés non nulles
        key_conditions = []

        for k in keys:
            cond = col(k).isNotNull()
            cond = cond & (lower(trim(col(k).cast("string"))) != "undefined")
            key_conditions.append(cond)
        
        valid_key_condition = reduce(
            lambda a, b: a & b, key_conditions
        )

        if ignore_nulls:

            # lignes soumises au contrôle FK
            df_to_validate = clean_df.filter(valid_key_condition)

            # lignes ignorées mais conservées
            df_null_keys = clean_df.filter(~valid_key_condition)

        else:

            df_to_validate = clean_df
            df_null_keys = None

        # lignes invalides
        invalid_df = (
            df_to_validate
            .join(ref_df, on=keys, how="left_anti")
            .withColumn("reject_reason", lit(check["name"]))
        )

        # lignes valides
        valid_df = (
            df_to_validate
            .join(
                invalid_df.select(*keys).distinct(),
                on=keys,
                how="left_anti"
            )
        )
        invalid_df =  invalid_df.withColumn("reject_date", current_timestamp()) \
                         .withColumn("rejected_line", concat_ws(
                            ",",
                            *[
                                concat(lit(f"{c}: "), col(c).cast("string"))
                                for c in all_columns
                            ]
                            )) \
                         .withColumn("reject_field", concat_ws('|', *keys)) \
                         .select("reject_date", "reject_reason", "reject_field", "rejected_line")
        reject_dfs.append(invalid_df)

        # on remet les lignes nulles ignorées
        if ignore_nulls:
            clean_df = valid_df.unionByName(df_null_keys)
        else:
            clean_df = valid_df

    if reject_dfs:
        reject_df = reduce(
            lambda a, b: a.unionByName(b, allowMissingColumns=True),
            reject_dfs
        )
    else:
        reject_df = spark.createDataFrame([], clean_df.schema)
    return clean_df, reject_df

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
