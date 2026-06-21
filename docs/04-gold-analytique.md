# Couche Gold – Faits & Dimensions Analytiques

## Vue d'ensemble

La couche Gold contient les **tables de faits** et les **dimensions enrichies** optimisées pour l'analyse et le Semantic Model. Les faits sont calculés par des notebooks SQL/Spark via des opérations **MERGE idempotentes**, garantissant un chargement sûr et répétable.

## Tables de faits

### `gold.fait_usage_dataiku_utilisateur`

**Grain** : 1 ligne par (utilisateur × instance × projet × type d'usage × jour × numéro de session)

#### Définition d'une session

Une session est une **séquence d'actions consécutives** d'un utilisateur sur une instance/projet/usage, où l'intervalle entre deux actions consécutives ne dépasse pas **1 heure**. Au-delà de 1 heure sans activité, une nouvelle session commence.

```
Groupe : (instance, user, project, date, usage_type)
Session N° : incrémenté à chaque gap > 1h entre deux audit_logs consécutifs
Durée = session_end - session_start (en secondes et en minutes)
```

#### Chargement incrémental

```sql
-- Filtre delta : uniquement les audit_logs postérieurs au dernier run réussi
WHERE audit_log.timestamp > (
    SELECT MAX(start_time)
    FROM tech.execution_log
    WHERE etape_name = 'gold.fait_usage_dataiku_utilisateur'
      AND end_time IS NOT NULL
)
```

#### MERGE idempotent

```sql
MERGE INTO gold.fait_usage_dataiku_utilisateur AS target
USING staging AS source ON target.id = source.id
WHEN MATCHED THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT ...
```

La clé `id` est un hash des champs de grain → pas de doublons en cas de re-run.

#### Colonnes

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | BIGINT | Clé technique (hash du grain) |
| `instance_id` | BIGINT | FK → gold.dim_instance |
| `user_id` | BIGINT | FK → gold.dim_utilisateur |
| `project_id` | BIGINT | FK → gold.dim_project |
| `usage_id` | BIGINT | FK → gold.dim_usage |
| `licence_id` | BIGINT | FK → gold.dim_licence |
| `timestamp_dt` | DATE | Date de la session (FK → gold.dim_calendrier) |
| `session_number` | INT | Numéro de session dans la journée |
| `session_start` | TIMESTAMP | Début de session |
| `session_end` | TIMESTAMP | Fin de session |
| `session_duration_seconds` | INT | Durée de la session en secondes |
| `session_duration_minutes` | FLOAT | Durée de la session en minutes |
| `jobs_count` | INT | Nombre de jobs exécutés dans la session |
| `scenarios_count` | INT | Nombre de scénarios exécutés dans la session |
| `loaded_at` | TIMESTAMP | Horodatage d'ingestion |
| `updated_at` | TIMESTAMP | Horodatage de mise à jour |

---

## Dimensions Gold

### `gold.dim_utilisateur`

Extension de `silver.dim_utilisateur` avec :

| Colonne ajoutée | Type | Description |
|----------------|------|-------------|
| `isTechAccount` | BOOLEAN | `TRUE` si compte de service/technique (à exclure des analyses utilisateur) |

Tous les visuels et mesures filtrent `isTechAccount = FALSE` par défaut.

### `gold.dim_calendrier`

Table calendrier pré-calculée, non dérivée des faits. Utilisée comme axe temporel principal.

| Attribut | Description |
|----------|-------------|
| `DATE` | Clé primaire (format DATE) |
| `ANNEE` | Année civile |
| `TRIMESTRE` | Numéro de trimestre |
| `MOIS` | Numéro de mois |
| `SEMAINE_ISO` | Numéro de semaine ISO |
| `JOUR_SEMAINE` | Numéro de jour de la semaine |
| `NOM_MOIS` | Libellé mois (français) |
| `NOM_JOUR` | Libellé jour (français) |
| `IS_LEAP_YEAR` | Année bissextile |
| `IS_53_WEEK_YEAR` | Année avec 53 semaines ISO |
| Flags YTD/MTD/WTD | Indicateurs pour les calculs de période |

### `gold.dim_max_user_licence`

Table helper calculée : pour chaque utilisateur, identifie la licence de **plus haute priorité** attribuée (utile pour les analyses d'allocation par profil dominant).

| Colonne | Description |
|---------|-------------|
| `user_id` | FK → dim_utilisateur |
| `licence_id` | Licence de plus haute priorité |
| `priority` | Rang de priorité |

Relation **bidirectionnelle** avec `dim_utilisateur` dans le Semantic Model pour les calculs d'allocation.

### `gold.dim_status_opt`

Table de référence pour les statuts d'optimisation.

| Colonne | Valeurs |
|---------|---------|
| `statut` | `ok`, `sous_utilisee`, `inactive` |
| `libelle` | Libellé long en français |
| `order` | Ordre d'affichage dans les visuels |

### Autres dimensions Gold

| Table | Description |
|-------|-------------|
| `gold.dim_instance` | Copie enrichie depuis silver |
| `gold.dim_licence` | Copie enrichie depuis silver |
| `gold.dim_project` | Copie enrichie depuis silver (avec `domain`, `sub_domain` extraits du `folder_path`) |
| `gold.dim_usage` | Copie enrichie depuis silver |

## Notebook DDL initial

`NB_Ddl_Tables_De_Fait.Notebook` crée les tables de faits Gold si elles n'existent pas (DDL SQL/Spark). À exécuter une seule fois lors de l'initialisation ou en cas de reset complet du schema Gold.

`NB_Ddl_Tech_Tables.Notebook` crée les tables du schema `tech` (`execution_log`, `rejects`).
