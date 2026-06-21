# Architecture – Supervision Platform End User

## Vue d'ensemble

La plateforme de supervision implémente une **architecture en médaillon** (Medallion Architecture) sur Microsoft Fabric, avec quatre couches successives : Bronze, Silver, Gold et Exposition.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        SOURCES (Starburst)                      │
│   DEV · INT · RPP · PROD  – instances Dataiku DSS                        │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │  Dataflow Gen2 (Power Query M)
                                 │  chargement incrémental par snapshot_date
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  BRONZE  (schema bronze, Delta Lake)                                     │
│  Snapshots bruts : users_prep · audit_logs_prep · usage_licences_prep    │
│  project_folder_prep · scenario_runs_prep · jobs_prep                    │
│  Tables techniques : tech.execution_log · tech.rejects                   │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │  Notebooks Python/Polars
                                 │  nettoyage · normalisation · dédup
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  SILVER  (schema silver, Delta Lake)                                     │
│  dim_utilisateur · dim_licence · dim_instance · dim_project              │
│  dim_usage · dim_instance_licence_utilisateur (pont)                     │
│  audit_logs (validés, RI contrôlée)                                      │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │  Notebooks SQL/Spark
                                 │  MERGE idempotent · sessions · agrégats
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  GOLD  (schema gold, Delta Lake)                                         │
│  fait_usage_dataiku_utilisateur · fait_licence_dataiku                   │
│  Dimensions enrichies : dim_utilisateur (isTechAccount)                  │
│  dim_calendrier · dim_max_user_licence · dim_status_opt                  │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │  DirectLake
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  EXPOSITION                                                               │
│  ┌─────────────────────────────────┐  ┌────────────────────────────────┐ │
│  │  Semantic Model (TMDL)          │  │  Rapport Power BI (4 pages)    │ │
│  │  Relations · Mesures DAX        │  │  Thème FDJ dark/light          │ │
│  │  DirectLake mode                │  │  Bookmarks · Navigation        │ │
│  └─────────────────────────────────┘  └────────────────────────────────┘ │
│  ┌─────────────────────────────────┐                                      │
│  │  Data Agent IA                  │                                      │
│  │  Q&A en français                │                                      │
│  │  Connecté au Semantic Model     │                                      │
│  └─────────────────────────────────┘                                      │
└──────────────────────────────────────────────────────────────────────────┘
```

## Principes architecturaux

### Médaillon (Bronze / Silver / Gold)

| Couche | Objectif | Format | Mise à jour |
|--------|----------|--------|-------------|
| **Bronze** | Landing brut, fidèle à la source | Delta Lake, append | Quotidienne (incremental) |
| **Silver** | Données nettoyées, normalisées, conformées | Delta Lake, SCD Type 1 | À chaque run pipeline |
| **Gold** | Modèle analytique optimisé pour la requête | Delta Lake, MERGE | À chaque run pipeline |

### Chargement incrémental

- **Bronze** : le Dataflow détecte la dernière `snapshot_date` dans la table cible et n'extrait que les nouvelles lignes depuis Starburst.
- **Silver** : les notebooks lisent l'intégralité du bronze pour reconstruire les dimensions (idempotent).
- **Gold** : les notebooks de faits utilisent `tech.execution_log` pour ne traiter que les événements arrivés depuis le dernier run réussi. Les MERGE garantissent l'idempotence.

### Clés techniques (hash)

Toutes les clés techniques de dimension sont calculées par :

```python
hash(struct(champs_métier)) % (2**63 - 1)  # Int64 stable cross-runs
```

Cela garantit la convergence des clés entre les runs sans séquence auto-incrémentale.

## Composants Fabric utilisés

| Composant Fabric | Rôle |
|------------------|------|
| **Lakehouse** | Stockage Delta Lake (schemas bronze/silver/gold/tech) |
| **Dataflow Gen2** | Ingestion Power Query M depuis Starburst |
| **Notebooks** | Transformations Python/Polars et SQL/Spark |
| **Data Pipelines** | Orchestration (Master + sous-pipelines paramétriques) |
| **Variable Library** | Configuration centralisée (WorkspaceId, LakehouseId, connexions…) |
| **Semantic Model** | Modèle DirectLake (TMDL), relations et mesures DAX |
| **Rapport Power BI** | Dashboard 4 pages avec thème FDJ |
| **Data Agent** | Agent IA connecté au Semantic Model |

## Environnements Dataiku supervisés

| Environnement | Type | Starburst host |
|---------------|------|----------------|
| DEV | Design (développement) | `starburst.paas-datalake-data-2.dev.fdj.fr:443` |
| INT | Automation (intégration) | `starburst.paas-datalake-data-2.int.fdj.fr:443` |
| RPP | Pré-production | À configurer |
| PROD | Production | À configurer |

## Flux de données complet (bout en bout)

```
1. Data Pipeline Master démarre (planifié ou manuel)
   │
   ├─ 2. DP_DATA_INGESTION_BRONZE
   │       └─ invoque DP_STARBURST_LAKEHOUSE_LOADER (params: host, schema, prefix)
   │           └─ exécute DF_Starburst_Lakehouse_Loader_Append (Dataflow Gen2)
   │               └─ extrait les nouveaux snapshots → bronze.*_prep
   │
   ├─ 3. DP_Dimensions (DESTINATION_SCHEMA=silver)
   │       └─ NB_Dimensions       → 6 dims silver + 1 table pont
   │       └─ NB_Audit_Silver     → audit_logs validés + tech.rejects
   │       └─ NB_Dimensions_Gold  → gold.dim_* (enrichissement)
   │
   ├─ 4. DP_FAITS
   │       └─ NB_Fait_Usage_Dataiku_Utilisateur → gold.fait_usage (MERGE)
   │       └─ NB_Fait_Licence_Dataiku           → gold.fait_licence (MERGE)
   │
   └─ 5. Refresh Semantic Model (PBISemanticModelRefresh)
           └─ DirectLake pointe sur les tables gold mises à jour
               └─ Rapport Power BI reflète les nouvelles données
               └─ Data Agent peut répondre avec les données fraîches
```
