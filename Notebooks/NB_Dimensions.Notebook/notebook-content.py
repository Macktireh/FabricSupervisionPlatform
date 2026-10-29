# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "jupyter",
# META     "jupyter_kernel_name": "python3.12"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# # Dimensions 

# MARKDOWN ********************

# ## Importation de paquets

# CELL ********************

from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict
import os
# pour ne pas polluer le logs par les warnings concernant le type de parquet UNKNOWN
# https://github.com/delta-io/delta-kernel-rs/issues/1415

os.environ["RUST_LOG"] = "delta_kernel=error"
import polars as pl
from deltalake import DeltaTable, write_deltalake

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## Parametres dimensions et variables global

# PARAMETERS CELL ********************

ENABLE_DIM_UTILISATEUR = True
ENABLE_DIM_INSTANCE = True
ENABLE_DIM_LICENCE = True
ENABLE_DIM_INSTANCE_LICENCE_UTILISATEUR = True
ENABLE_DIM_PROJECT = True
ENABLE_DIM_USAGE = True

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

%run NB_Utils_Delta

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

"""class ItemReference(TypedDict):
    itemId: str
    workspaceId: str


VariableLib = notebookutils.variableLibrary.getLibrary("VL_ENV_SupervisionPlatform")
LAKEHOUSE_SUPERVISION_PLATFORM: ItemReference = getattr(VariableLib, "LakehouseSupervisionPlatform")
"""

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## Fonctions utilitaires

# CELL ********************

"""
def _abfs_base() -> str:
    return (
        f"abfss://{LAKEHOUSE_SUPERVISION_PLATFORM['workspaceId']}"
        f"@onelake.dfs.fabric.microsoft.com/{LAKEHOUSE_SUPERVISION_PLATFORM['itemId']}"
    )


def get_table_path(schema: str, table_name: str) -> str:
    return f"{_abfs_base()}/Tables/{schema}/{table_name}"


def get_file_path_abfs(relative_path: str) -> str:
    return f"{_abfs_base()}/Files/{relative_path}"

"""
def read_lakehouse_table(table_name: str, schema: str = "dbo") -> pl.DataFrame:
    path = get_table_path(schema, table_name)
    ds = DeltaTable(path).to_pyarrow_table()
    return pl.from_arrow(ds)


def read_lakehouse_file(
    relative_path: str, file_format: str | None = None, **kwargs
) -> pl.DataFrame:

    path = get_file_path_abfs(relative_path)

    fmt = (file_format or Path(relative_path).suffix.lower().lstrip(".")).lower()

    if fmt in ("parquet",):
        return pl.read_parquet(path, **kwargs)
    elif fmt in ("csv"):
        return pl.read_csv(path, **kwargs)
    elif fmt in ("json"):
        return pl.read_json(path, **kwargs)
    else:
        raise ValueError(
            f"Format fichier non supporté ou non détecté: '{fmt}'. "
            f"Passe file_format='csv'/'parquet'/'json' explicitement."
        )


def write_to_lakehouse(df: pl.DataFrame, table_name: str, schema: str = "dbo") -> None:
    path = get_table_path(schema, table_name)
    write_deltalake(path, df.to_arrow(), mode="overwrite", schema_mode="overwrite")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

def _require_cols(df: pl.DataFrame, cols: list[str], table_name: str = "df") -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes dans {table_name}: {missing}")


def _normalize_string(expr: pl.Expr) -> pl.Expr:
    return expr.cast(pl.Utf8, strict=False).str.strip_chars().replace("", None)


def _parse_date(expr: pl.Expr, fmt: str = "%Y-%m-%d") -> pl.Expr:
    return _normalize_string(expr).str.strptime(pl.Date, fmt, strict=False)


def _parse_datetime(expr: pl.Expr) -> pl.Expr:
    return _normalize_string(expr).str.strptime(
        pl.Datetime, "%Y-%m-%d %H:%M:%S%.f", strict=False
    )


def _coerce_int(expr: pl.Expr) -> pl.Expr:
    return expr.cast(pl.Int64, strict=False)


def _coerce_bool(expr: pl.Expr) -> pl.Expr:
    return (
        pl.when(
            expr.cast(pl.Utf8, strict=False).str.to_lowercase().is_in(["true", "false"])
        )
        .then(expr.cast(pl.Utf8, strict=False).str.to_lowercase() == "true")
        .otherwise(expr.cast(pl.Boolean, strict=False))
        .fill_null(False)
    )


def _parse_datetime_from_epoch_ms(expr: pl.Expr) -> pl.Expr:
    return (
        expr.cast(pl.Int64)
        .cast(pl.Datetime("ms"))
    )


def _with_audit_columns(df: pl.DataFrame) -> pl.DataFrame:
    now = datetime.now(timezone.utc)

    return df.with_columns(
        [
            pl.lit(now).alias("loaded_at"),
            pl.lit(now).alias("updated_at"),
        ]
    )


def _normalize_licence_type(expr: pl.Expr) -> pl.Expr:
    expr = expr.str.to_lowercase()

    return (
        pl.when(expr.is_in(["designer"]))
        .then(pl.lit("designer"))

        .when(expr.is_in(["reader"]))
        .then(pl.lit("reader"))

        .when(expr.is_in(["platform_admin", "platform admin"]))
        .then(pl.lit("platform admin"))

        .when(expr.is_in(["none"]))
        .then(pl.lit("none"))

        .when(expr.is_in(["ai consumer", "ai_consumer"]))
        .then(pl.lit("ai consumer"))

        .otherwise(expr)
    )

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## Dimensions

# MARKDOWN ********************

# ### Dim_Calendrier
# 
# > Réalisé depuis un Data Pipeline

# MARKDOWN ********************

# ### Dim_Utilisateur

# CELL ********************

def _extract_profile_code(group_expr: pl.Expr) -> pl.Expr:
    return _normalize_string(group_expr).str.to_lowercase().str.split("-").list.last()


def _map_profile_type(expr: pl.Expr) -> pl.Expr:
    expr = expr.fill_null("")
    return (
        pl.when(expr == "das").then(pl.lit("data scientist"))
        .when(expr == "da").then(pl.lit("data analyst"))
        .when(expr == "dev").then(pl.lit("dev IT"))
        .when(expr == "qua").then(pl.lit("testeurs"))
        .when(expr == "roa").then(pl.lit("ops"))
        .when(expr == "arc").then(pl.lit("architectes"))
        .when(expr == "adm").then(pl.lit("admin"))
        .when(expr == "dmr").then(pl.lit("managers"))
        .when(expr == "tld").then(pl.lit("tech lead"))
        .otherwise(pl.lit("métiers"))
    )


def _derive_contract_type(email_expr: pl.Expr, login_expr: pl.Expr) -> pl.Expr:
    email = _normalize_string(email_expr).str.to_lowercase()

    return (
        pl.when(email.str.split("@").list.first().str.contains(r"\.ext$"))
        .then(pl.lit("Externe"))
        .otherwise(pl.lit("Interne"))
    )



def build_dim_utilisateur(users_df: pl.DataFrame) -> pl.DataFrame:

    _require_cols(
        users_df, ["login", "displayname", "email", "group_utilisateur"], "users"
    )

    df = users_df.with_columns(
        [
            _normalize_string(pl.col("login")).alias("login_norm"),
            _normalize_string(pl.col("displayname")).alias("full_name_norm"),
            _normalize_string(pl.col("email")).str.to_lowercase().alias("email_norm"),
            _normalize_string(pl.col("group_utilisateur")).alias("group_norm"),
            _coerce_bool(pl.col("enabled")).alias("active"),
            _parse_date(pl.col("snapshot_date")).alias("snapshot_dt"),
        ]
    )

    df = df.with_columns(
        [
            pl.when(pl.col("login_norm").is_not_null())
            .then(pl.col("login_norm"))
            .otherwise(pl.col("email_norm"))
            .alias("user_key")
        ]
    )

    df = df.sort(
        ["user_key", "snapshot_dt", "creationdate"], descending=[False, True, True]
    ).unique(subset=["user_key"], keep="first")

    df = df.with_columns(
        [_extract_profile_code(pl.col("group_norm")).alias("profile_code")]
    )

    df = df.with_columns(
        [
            _map_profile_type(pl.col("profile_code")).alias("profile_type"),
            _derive_contract_type(pl.col("email_norm"), pl.col("login_norm")).alias(
                "contract_type"
            ),
        ]
    )

    dim = (
        df.select(
            [
                pl.col("login_norm").alias("username"),
                pl.col("full_name_norm").alias("full_name"),
                pl.col("email_norm").alias("email"),
                pl.col("profile_type"),
                pl.col("contract_type"),
                pl.col("group_norm"),
                pl.col("active"),
                pl.col("creationdate"),
                pl.col("snapshot_dt"),
            ]
        )
        .with_columns(
            [
                pl.when(pl.col("full_name").is_null())
                .then(pl.col("username"))
                .otherwise(pl.col("full_name"))
                .alias("full_name")
            ]
        )
        .sort("username")
        .with_columns(pl.struct(["username"]).hash().mod(2**63 - 1).cast(pl.Int64).alias("id"))
    )
    dim = dim.select(["id", "username", "full_name", "email", "profile_type", "group_norm", "contract_type", "active", "creationdate", "snapshot_dt"])

    return _with_audit_columns(dim)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ### Dim_Licence

# CELL ********************

def build_dim_licence(usage_licences_df: pl.DataFrame) -> pl.DataFrame:

    _require_cols(
        usage_licences_df,
        ["profile", "used", "max", "unlimited", "snapshot_date"],
        "usage_licences",
    )

    df = usage_licences_df.with_columns(
        [
            _normalize_string(pl.col("profile")).alias("type"),
            _coerce_int(pl.col("used")).alias("used_i"),
            _coerce_int(pl.col("max")).alias("max_i"),
            _coerce_bool(pl.col("unlimited")).alias("unlimited_b"),
            _parse_date(pl.col("snapshot_date")).alias("snapshot_dt"),
        ]
    )

    last_state = (
        df.sort(
            ["type", "snapshot_dt"],
            descending=[False, True],
        )
        .group_by(["type"])
        .agg(
            [
                pl.first("max_i").alias("max_licences"),
                pl.first("used_i").alias("licences_used"),
                pl.first("unlimited_b").alias("unlimited"),
                pl.max("snapshot_dt").alias("end_date"),
                pl.min("snapshot_dt").alias("start_date"),
            ]
        )
    )

    dim = last_state.with_columns(
        [
            _normalize_licence_type(pl.col("type")).alias("type"),
            pl.when(pl.col("unlimited"))
            .then(None)
            .otherwise(pl.col("max_licences") - pl.col("licences_used"))
            .alias("quotas")
        ]
    )

    dim = dim.with_columns(
        pl.struct(["type"]).hash().mod(2**63 - 1).cast(pl.Int64).alias("id")
    ).select(["id", "type", "max_licences", "licences_used", "quotas", "unlimited", "end_date", "start_date"])
    

    return _with_audit_columns(dim)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ### Dim_Instance

# CELL ********************

_ENV_MAP = {
    "sandbox": "SANDBOX",
    "dev": "DEV",
    "int": "INT",
    "rpp": "RPP",
    "prod": "PROD",
}


def build_dim_instance(
    *dfs_with_instance: pl.DataFrame, instance_col: str = "instance"
) -> pl.DataFrame:

    instances = []
    for df in dfs_with_instance:
        if instance_col in df.columns:
            instances.append(
                df.select(_normalize_string(pl.col(instance_col)).alias("instance"))
            )

    all_instances = pl.concat(instances).unique()

    dim = (
        all_instances.with_columns(
            [
                pl.when(pl.col("instance").is_not_null())
                .then(pl.col("instance").str.to_lowercase().str.split("_").list.first())
                .otherwise(None)
                .alias("type"),
                pl.when(pl.col("instance").is_not_null())
                .then(pl.col("instance").str.to_lowercase().str.split("_").list.last())
                .otherwise(None)
                .alias("env_raw"),
            ]
        )
        .with_columns(
            [
                pl.col("env_raw").replace_strict(_ENV_MAP, default=None).alias("environment"),
                pl.col("instance").alias("instance_name"),
            ]
        )
        .with_columns(pl.struct(["environment", "type"]).hash().mod(2**63 - 1).cast(pl.Int64).alias("id"))
        .select(["id", "environment", "type", "instance_name"])
    )

    return _with_audit_columns(dim)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ### Dim_Instance_Licence_Utilisateur

# CELL ********************

def build_dim_instance_licence_utilisateur(
    users_df: pl.DataFrame,
    dim_users: pl.DataFrame,
    dim_instance: pl.DataFrame,
    dim_licence: pl.DataFrame,
) -> pl.DataFrame:
    """
    Table de liaison entre Utilisateur, Instance et Licence.
    """
    _require_cols(
        users_df, ["login", "instance", "userprofile", "snapshot_date"], "users_prep"
    )

    # 1) Normaliser la source users_prep
    u = (
        users_df.with_columns(
            [
                _normalize_string(pl.col("login")).alias("username"),
                _normalize_string(pl.col("instance")).alias("instance_raw"),
                _normalize_string(pl.col("userprofile")).alias("licence_type_raw"),
                _parse_date(pl.col("snapshot_date")).alias("snapshot_dt"),
            ]
        )
        .with_columns(
            [
                pl.col("username").str.to_lowercase().alias("username_norm"),
                _normalize_licence_type(pl.col("userprofile")).alias("licence_type_norm"),
                pl.when(pl.col("instance_raw").is_not_null())
                .then(
                    pl.col("instance_raw")
                    .str.to_lowercase()
                    .str.split("_")
                    .list.first()
                )
                .otherwise(None)
                .alias("type"),
                pl.when(pl.col("instance_raw").is_not_null())
                .then(
                    pl.col("instance_raw").str.to_lowercase().str.split("_").list.last()
                )
                .otherwise(None)
                .alias("env_raw"),
            ]
        )
        .with_columns(
            [
                pl.col("env_raw")
                .replace_strict(_ENV_MAP, default=None)
                .alias("environment")
            ]
        )
        .select(
            ["username_norm", "type", "environment", "licence_type_norm", "creationdate", "snapshot_dt"]
        )
    )

    # 2) Préparer les dims pour des joins case-insensitive
    du = (
        dim_users.select([pl.col("id").alias("user_id"), pl.col("username")])
        .with_columns(pl.col("username").str.to_lowercase().alias("username_norm"))
        .select(["user_id", "username_norm"])
        .unique()
    )

    di = (
        dim_instance.select(
            [pl.col("id").alias("instance_id"), "environment", pl.col("type")]
        )
        .select(["instance_id", "environment", "type"])
        .unique()
    )

    dl = (
        dim_licence.select(
            [pl.col("id").alias("licence_id"), pl.col("type").alias("licence_type_norm")]
        )
        .select(["licence_id", "licence_type_norm"])
        .unique()
    )

    # 3) Joindre pour obtenir les IDs
    link = (
        u.join(du, on="username_norm", how="left")
        .join(di, on=["environment", "type"], how="left")
        .join(dl, on="licence_type_norm", how="left")
    )

    # 4) Garder uniquement les enregistrements résolus
    link = link.drop_nulls(["user_id", "instance_id", "licence_id", "snapshot_dt"])

    # 5) état courant
    link = link.sort(
        ["user_id", "instance_id", "snapshot_dt"], descending=[False, False, True]
    ).unique(
        subset=["user_id", "instance_id", "licence_id", "snapshot_dt"], keep="first"
    )

    # 6) ID technique (hash)
    link = link.with_columns(
        pl.struct(["instance_id", "licence_id", "user_id", "snapshot_dt"])
        .hash()
        .mod(2**63 - 1)
        .cast(pl.Int64)
        .alias("id")
    ).select(["id", "instance_id", "licence_id", "user_id", "creationdate", "snapshot_dt"])

    return _with_audit_columns(link)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ### Dim_Project

# CELL ********************

def build_dim_project(project_folder_df: pl.DataFrame) -> pl.DataFrame:

    _require_cols(
        project_folder_df,
        ["projectkey", "folderpath", "snapshot_date"],
        "project_folder",
    )

    df = project_folder_df.with_columns(
        [
            _normalize_string(pl.col("projectkey")).alias("project_key"),
            _normalize_string(pl.col("folderpath")).alias("folder_path"),
            _parse_date(pl.col("snapshot_date")).alias("snapshot_dt"),
        ]
    )

    latest = (
        df.sort(["project_key", "snapshot_dt"], descending=[False, True])
        .group_by("project_key")
        .agg(pl.first("folder_path"))
    )

    dim = latest.with_columns(pl.struct(["project_key"]).hash().mod(2**63 - 1).cast(pl.Int64).alias("id")).select(["id", "project_key", "folder_path"])

    return _with_audit_columns(dim)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ### Dim_Usage

# CELL ********************

def build_dim_usage(
    audit_logs_prep_df: pl.DataFrame, dss_action_type_df: pl.DataFrame
) -> pl.DataFrame:

    _require_cols(audit_logs_prep_df, ["asset", "action"], "audit_logs_prep")
    _require_cols(
        dss_action_type_df, ["asset", "action", "Type action"], "dss_action_type"
    )

    left = audit_logs_prep_df.select(
        [
            _normalize_string(pl.col("asset")).alias("asset"),
            _normalize_string(pl.col("action")).alias("activity"),
        ]
    ).unique()

    right = dss_action_type_df.select(
        [
            _normalize_string(pl.col("asset")).alias("asset"),
            _normalize_string(pl.col("action")).alias("activity"),
            _normalize_string(pl.col("Type action")).alias("activity_type"),
        ]
    ).unique()

    dim = left.join(right, on=["asset", "activity"], how="left")

    dim = dim.with_columns([pl.col("activity_type").fill_null("Inconnu")])

    dim = dim.with_columns(pl.struct(["asset", "activity"]).hash().mod(2**63 - 1).cast(pl.Int64).alias("id")).select(["id", "asset", "activity", "activity_type"])

    return _with_audit_columns(dim)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## Exécution

# CELL ********************

def run_dimensions():

    # --------------------------------------------------------
    # DIM_UTILISATEUR
    # --------------------------------------------------------
    if ENABLE_DIM_UTILISATEUR:
        execution_log = ExecutionLoggerDelta("silver","dim_utilisateur")
        execution_log.execution_start()
        users_df = read_lakehouse_table("users_prep", schema="bronze")
        dim_users = build_dim_utilisateur(users_df)
        write_to_lakehouse(dim_users, "Dim_Utilisateur", schema="silver")
        print(f"Dim_Utilisateur créé : {dim_users.shape[0]} lignes")
        metrics = {"inserted": dim_users.shape[0]}
        execution_log.execution_end(metrics)


    # --------------------------------------------------------
    # DIM_INSTANCE
    # --------------------------------------------------------
    if ENABLE_DIM_INSTANCE:
        execution_log = ExecutionLoggerDelta("silver","dim_instance")
        execution_log.execution_start()
        project_df = read_lakehouse_table("project_folder_prep", "bronze")
        usage_df = read_lakehouse_table("usage_licences_prep", "bronze")
        audit_df = read_lakehouse_table("audit_logs_prep", "bronze")

        dim_instance = build_dim_instance(project_df, usage_df, audit_df)
        write_to_lakehouse(dim_instance, "Dim_Instance", "silver")
        print(f"Dim_Instance créé : {dim_instance.shape[0]} lignes")
        metrics = {"inserted": dim_instance.shape[0]}
        execution_log.execution_end(metrics)


    # --------------------------------------------------------
    # DIM_LICENCE
    # --------------------------------------------------------
    if ENABLE_DIM_LICENCE:
        execution_log = ExecutionLoggerDelta("silver","dim_licence")
        execution_log.execution_start()
        usage_df = read_lakehouse_table("usage_licences_prep", "bronze")
        dim_licence = build_dim_licence(usage_df)
        write_to_lakehouse(dim_licence, "Dim_Licence", "silver")
        print(f"Dim_Licence créé : {dim_licence.shape[0]} lignes")
        metrics = {"inserted": dim_licence.shape[0]}
        execution_log.execution_end(metrics)

    # --------------------------------------------------------
    # DIM_INSTANCE_LICENCE_UTILISATEUR
    # --------------------------------------------------------
    if ENABLE_DIM_INSTANCE and ENABLE_DIM_LICENCE and ENABLE_DIM_UTILISATEUR and ENABLE_DIM_INSTANCE_LICENCE_UTILISATEUR:
        execution_log = ExecutionLoggerDelta("silver","dim_instance_licence_utilisateur")
        execution_log.execution_start()
        users_df = read_lakehouse_table("users_prep", schema="bronze")

        bridge = build_dim_instance_licence_utilisateur(
            users_df=users_df,
            dim_users=dim_users,
            dim_instance=dim_instance,
            dim_licence=dim_licence,
        )

        write_to_lakehouse(bridge, "Dim_Instance_Licence_Utilisateur", schema="silver")
        print(f"Dim_Instance_Licence_Utilisateur créé : {bridge.shape[0]} lignes")
        metrics = {"inserted": bridge.shape[0]}
        execution_log.execution_end(metrics)


    # --------------------------------------------------------
    # DIM_PROJECT
    # --------------------------------------------------------
    if ENABLE_DIM_PROJECT:
        execution_log = ExecutionLoggerDelta("silver","dim_project")
        execution_log.execution_start()
        project_df = read_lakehouse_table("project_folder_prep", "bronze")
        dim_project = build_dim_project(project_df)
        write_to_lakehouse(dim_project, "Dim_Project", "silver")
        print(f"Dim_Project créé : {dim_project.shape[0]} lignes")
        metrics = {"inserted": dim_project.shape[0]}
        execution_log.execution_end(metrics)


    # --------------------------------------------------------
    # DIM_USAGE
    # --------------------------------------------------------
    if ENABLE_DIM_USAGE:
        execution_log = ExecutionLoggerDelta("silver","dim_usage")
        execution_log.execution_start()
        audit_df = read_lakehouse_table("audit_logs_prep", "bronze")
        action_df = read_lakehouse_file("Data sources/dss_actions_type.csv", separator=";")

        dim_usage = build_dim_usage(audit_df, action_df)
        write_to_lakehouse(dim_usage, "Dim_Usage", "silver")
        print(f"Dim_Usage créé : {dim_usage.shape[0]} lignes")
        metrics = {"inserted": dim_usage.shape[0]}
        execution_log.execution_end(metrics)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

run_dimensions()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }
