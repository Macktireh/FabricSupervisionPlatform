# Orchestration – Data Pipelines & Variable Library

## Vue d'ensemble

L'orchestration repose sur **5 Data Pipelines Fabric** organisés en hiérarchie (Master → sous-pipelines). La configuration est centralisée via une **Variable Library** qui évite la duplication des paramètres et facilite les changements d'environnement.

## Hiérarchie des pipelines

```
Master.DataPipeline
├── DP_DATA_INGESTION_BRONZE        ← Ingestion Starburst → Bronze
│   └── DP_STARBURST_LAKEHOUSE_LOADER (parametrique)
│       └── DF_Starburst_Lakehouse_Loader_Append (Dataflow Gen2)
│
├── DP_Dimensions                   ← Bronze → Silver (dimensions)
│   ├── NB_Dimensions
│   ├── NB_Audit_Silver
│   └── NB_Dimensions_Gold
│
├── DP_FAITS                        ← Silver → Gold (faits)
│   ├── NB_Fait_Usage_Dataiku_Utilisateur
│   └── NB_Fait_Licence_Dataiku
│
└── Refresh Semantic Model          ← Rafraîchissement DirectLake
    └── PBISemanticModelRefresh
```

---

## Master.DataPipeline

Pipeline principal d'orchestration. Séquence les étapes dans l'ordre :

| Étape | Activité | Dépendance |
|-------|----------|------------|
| 1 | Invoke `DP_DATA_INGESTION_BRONZE` | – |
| 2 | Invoke `DP_Dimensions` (param: `DESTINATION_SCHEMA=silver`) | Étape 1 réussie |
| 3 | Invoke `DP_FAITS` | Étape 2 réussie |
| 4 | `PBISemanticModelRefresh` | Étape 3 réussie |

**Paramètre dataset** :
- Dataset ID : `94261c78-583f-418c-a59e-6b621f0c6c4f`
- Workspace ID : `cae55539-e164-4a36-bb47-62c5bb2cbee7`
- Timeout : 12 heures
- Mode de commit : transactionnel

---

## DP_DATA_INGESTION_BRONZE

Invoque `DP_STARBURST_LAKEHOUSE_LOADER` pour chaque instance Dataiku configurée.

| Instance | Paramètres passés |
|----------|------------------|
| **Design DEV** | host: `starburst.paas-datalake-data-2.dev.fdj.fr:443`, database: `lab_mnp_plt_hive`, schema: `lab_mnp_plt_plt`, prefix: `design_monopole_dev` |
| **Automation INT** | host: `starburst.paas-datalake-data-2.int.fdj.fr:443`, database: `dlk_hive`, schema: `mrt_mnp_plt_plt`, prefix: `automation_monopole_int` |
| RPP | À configurer (même pattern) |
| PROD | À configurer (même pattern) |

---

## DP_STARBURST_LAKEHOUSE_LOADER

Pipeline paramétrique réutilisable. Reçoit les paramètres de connexion et exécute le Dataflow Gen2 `DF_Starburst_Lakehouse_Loader_Append` avec ces paramètres.

**Paramètres d'entrée** :
- `SOURCE_HOST`, `SOURCE_PORT`
- `SOURCE_DATABASE`, `SOURCE_SCHEMA`
- `SOURCE_INSTANCE_PREFIX_TABLE`, `SOURCE_INSTANCE_VALUE`
- `DESTINATION_SCHEMA` (défaut : `bronze`)

---

## DP_Dimensions

Orchestre les notebooks de construction des dimensions.

| Ordre | Notebook | Schema cible |
|-------|----------|-------------|
| 1 | `NB_Dimensions` | silver |
| 2 | `NB_Audit_Silver` | silver |
| 3 | `NB_Dimensions_Gold` | gold |

---

## DP_FAITS

Orchestre les notebooks de calcul des faits.

| Ordre | Notebook | Schema cible |
|-------|----------|-------------|
| 1 | `NB_Fait_Usage_Dataiku_Utilisateur` | gold |
| 2 | `NB_Fait_Licence_Dataiku` | gold |

---

## Variable Library : `VL_ENV_SupervisionPlatform`

Centralise les paramètres de configuration partagés entre tous les notebooks et pipelines.

### Variables définies

| Variable | Type | Valeur | Usage |
|----------|------|--------|-------|
| `WorkspaceId` | Guid | `cae55539-e164-4a36-bb47-62c5bb2cbee7` | Workspace Fabric contenant le Lakehouse et le Semantic Model |
| `LakehouseId` | Guid | `e5a494bb-2c9c-44ec-9fd3-494add93bd08` | ID du Lakehouse cible |
| `LakehouseSupervisionPlatform` | ItemReference | itemId + workspaceId | Référence complète pour l'accès ABFS aux tables Delta |
| `SourceServer` | String | `tdadev` | Identifiant de l'environnement TDA |
| `SourceEnv` | String | `INT3` | Label de l'environnement source |
| `SourceConnectionId` | Guid | `9366a7fd-3206-4f60-aefe-540bc1e07bcf` | Connexion Starburst dans Fabric |
| `DataflowStarburstLakehouseLoaderAppend` | ItemReference | itemId + workspaceId | Référence du Dataflow Gen2 |

### Utilisation dans les notebooks

```python
# Récupération de la Variable Library dans un notebook
vl = notebookutils.variableLibrary.getLibrary("VL_ENV_SupervisionPlatform")
lakehouse_id = vl.get("LakehouseId")
workspace_id = vl.get("WorkspaceId")
```
