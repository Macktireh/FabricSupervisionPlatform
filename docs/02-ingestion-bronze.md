# Ingestion & Couche Bronze

## Vue d'ensemble

La couche Bronze est le point d'entrée de toutes les données brutes issues des instances Dataiku. Les données sont extraites depuis **Starburst** via un **Dataflow Gen2** paramétrique, puis stockées en Delta Lake dans le Lakehouse sous le schema `bronze`.

## Dataflow Gen2 : `DF_Starburst_Lakehouse_Loader_Append`

### Rôle

Extraire de manière **incrémentale** les tables de logs et référentiels Dataiku depuis Starburst, et les charger en mode **append** dans le Lakehouse (schema `bronze`).

### Paramètres (Power Query M)

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `SOURCE_HOST` | Hostname du serveur Starburst | `starburst.paas-datalake-data-2.dev.fdj.fr` |
| `SOURCE_PORT` | Port HTTPS | `443` |
| `SOURCE_DATABASE` | Base de données Starburst | `lab_mnp_plt_hive` |
| `SOURCE_SCHEMA` | Schéma source dans Starburst | `lab_mnp_plt_plt` |
| `SOURCE_INSTANCE_PREFIX_TABLE` | Préfixe des tables source | `design_monopole_dev` |
| `SOURCE_INSTANCE_VALUE` | Valeur de l'instance (pour filtrage) | `DEV` |
| `DESTINATION_SCHEMA` | Schéma cible dans le Lakehouse | `bronze` |

### Fonctions Power Query internes

| Fonction | Description |
|----------|-------------|
| `getLatestSnapshotDateFromLakehouseTable()` | Retourne la dernière `snapshot_date` dans la table cible → point de reprise incrémentale |
| `loadIncrementalStarburstTable()` | Exécute la requête Starburst avec filtre `snapshot_date > dernière date` |
| `getCurrentParisDateTime()` | Horodatage aligné sur le fuseau Europe/Paris |

### Logique incrémentale

```
1. Lire la MAX(snapshot_date) de la table Bronze cible dans le Lakehouse
2. Interroger Starburst : WHERE snapshot_date > MAX(snapshot_date) connu
3. Appender les nouvelles lignes dans la table Bronze Delta
```

Premier run (table vide) → extraction complète depuis la date initiale.

### Tables chargées

| Table Bronze | Source Starburst | Contenu |
|--------------|-----------------|---------|
| `bronze.users_prep` | `*_users_prep` | Registre utilisateurs (login, email, groupe, profil, actif, snapshot_date) |
| `bronze.usage_licences_prep` | `*_usage_licences_prep` | Inventaire licences (type, nb utilisé, max alloué, unlimited, snapshot_date) |
| `bronze.project_folder_prep` | `*_project_folder_prep` | Métadonnées projets (project_key, arborescence dossier, snapshot_date) |
| `bronze.audit_logs_prep` | `*_audit_logs_prep` | Logs d'activité (instance, user, project, asset, action, timestamp) |
| `bronze.scenario_runs_prep` | `*_scenario_runs_prep` | Exécutions de scénarios |
| `bronze.jobs_prep` | `*_jobs_prep` | Exécutions de jobs |
| `bronze.cluster_tasks_prep` | `*_cluster_tasks_prep` | Tâches cluster |

## Configuration des instances (Data Pipeline)

Le pipeline `DP_DATA_INGESTION_BRONZE` invoque `DP_STARBURST_LAKEHOUSE_LOADER` avec les paramètres de chaque instance :

| Instance | Starburst Host | Schema | Préfixe table |
|----------|---------------|--------|---------------|
| Design DEV | `starburst.paas-datalake-data-2.dev.fdj.fr:443` | `lab_mnp_plt_hive.lab_mnp_plt_plt` | `design_monopole_dev` |
| Automation INT | `starburst.paas-datalake-data-2.int.fdj.fr:443` | `dlk_hive.mrt_mnp_plt_plt` | `automation_monopole_int` |
| RPP | À configurer | | |
| PROD | À configurer | | |

## Variable Library (référence)

Les paramètres de connexion partagés sont stockés dans `VL_ENV_SupervisionPlatform` :

| Variable | Valeur | Usage |
|----------|--------|-------|
| `WorkspaceId` | GUID workspace | Référence workspace Fabric |
| `LakehouseId` | GUID lakehouse | Destination des données |
| `SourceServer` | `tdadev` | Identifiant environnement TDA |
| `SourceEnv` | `INT3` | Environnement source |
| `SourceConnectionId` | GUID connexion | Connexion Starburst dans Fabric |
| `DataflowStarburstLakehouseLoaderAppend` | ItemReference | Référence du Dataflow Gen2 |
