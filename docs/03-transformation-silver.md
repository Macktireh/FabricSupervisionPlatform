# Transformation – Couche Silver

## Vue d'ensemble

La couche Silver produit les **dimensions conformées** et les **logs validés** à partir des données brutes Bronze. Les transformations sont réalisées principalement en **Python/Polars** (notebooks Fabric), avec une logique métier explicite : normalisation des profils, dérivation des types de contrat, contrôles d'intégrité référentielle.

## Notebooks Silver

### `NB_Dimensions.Notebook`

Notebook principal de construction des dimensions Silver. Utilise **Python avec Polars** pour la performance sur les DataFrames.

#### Tables produites

| Table | Grain | Clé technique |
|-------|-------|---------------|
| `silver.dim_utilisateur` | 1 ligne par utilisateur unique | `hash(login, email)` |
| `silver.dim_licence` | 1 ligne par type de licence | `hash(type_licence)` |
| `silver.dim_instance` | 1 ligne par instance Dataiku | `hash(instance_name)` |
| `silver.dim_project` | 1 ligne par projet | `hash(project_key)` |
| `silver.dim_usage` | 1 ligne par couple (asset, action) | `hash(asset, activity)` |
| `silver.dim_instance_licence_utilisateur` | 1 ligne par (utilisateur, instance, licence) | `hash(user_id, instance_id, licence_id)` |

#### Logique métier par dimension

**`dim_utilisateur`**

| Transformation | Règle |
|---------------|-------|
| Déduplication | Tri par `snapshot_dt DESC`, on garde la ligne la plus récente par `(login, email)` |
| `type_contrat` | Email terminant par `.ext` → `Externe` ; sinon → `Interne` |
| `type_profil` | Extrait du suffixe du groupe (split sur `-`) selon la table ci-dessous |
| `group_norm` | Normalisation du nom de groupe (lower-case, strip) |

Mapping `type_profil` depuis le groupe utilisateur :

| Suffixe groupe | Profil |
|---------------|--------|
| `das` | data scientist |
| `da` | data analyst |
| `dev` | dev IT |
| `qua` | testeurs |
| `roa` | ops |
| `arc` | architectes |
| `adm` | admin |
| `dmr` | managers |
| (autre) | métiers |

**`dim_licence`**

Normalisation du champ `userprofile` source vers un type de licence standardisé :

| Valeur source | Type normalisé |
|---------------|---------------|
| `DESIGNER` | designer |
| `READER` | reader |
| `PLATFORM_ADMIN` | platform admin |
| `AI_CONSUMER` | ai consumer |
| (null / autre) | none |

`quotas` calculé = `max_licences - licences_used`

**`dim_instance`**

Mapping de l'environnement depuis le nom d'instance :

| Valeur source | Environnement |
|---------------|--------------|
| `dev` | DEV |
| `int` | INT |
| `rpp` | RPP |
| `prod` | PROD |
| `sandbox` | SANDBOX |

**`dim_usage`**

Mapping `(asset, action)` → `activity_type` via le fichier de référence `dss_action_type.csv` :

| activity_type | Exemples d'activités |
|---------------|---------------------|
| Consultation | lecture dataset, navigation projet |
| Développement | création/modification recette, dataset |
| Industrialisation | déclenchement scénario, job |
| Surveillance | visualisation logs, monitoring |

**`dim_instance_licence_utilisateur` (table pont)**

Relie les utilisateurs à leurs instances et licences. Supporte la relation many-to-many (un utilisateur peut avoir plusieurs licences sur plusieurs instances). Historise via `snapshot_dt`.

---

### `NB_Audit_Silver.Notebook`

Charge les logs d'audit depuis `bronze.audit_logs_prep` vers `silver.audit_logs` après **contrôles d'intégrité référentielle**.

#### Contrôles RI effectués

| Contrôle | Condition de rejet | Table rejet |
|----------|-------------------|-------------|
| Usage inconnu | `(asset, action)` absent de `dim_usage` | `tech.rejects` (raison: `asset_action_inconnu`) |
| Projet inconnu | `project_key` absent de `dim_project` | `tech.rejects` (raison: `projet_inconnu`) |
| Utilisateur inconnu | `user` absent de `dim_utilisateur` | `tech.rejects` (raison: `utilisateur_inconnu`) |
| Instance inconnue | `instance` absente de `dim_instance` | `tech.rejects` (raison: `instance_inconnue`) |

Les lignes valides sont écrites dans `silver.audit_logs`. Les lignes invalides vont dans `tech.rejects` pour investigation.

---

### `NB_Dimensions_Gold.Notebook`

Transforme les dimensions Silver vers Gold avec des enrichissements supplémentaires. Utilise SQL/Spark avec `ExecutionLogger`.

#### Enrichissements notables

**`gold.dim_utilisateur`** — Ajout du flag `isTechAccount` :
- Détecte les comptes de service / comptes techniques (ex: comptes de batch, d'intégration)
- Utilisé comme filtre dans toutes les analyses utilisateur (`WHERE isTechAccount = FALSE`)

Autres dimensions Gold (`dim_instance`, `dim_licence`, `dim_project`, `dim_usage`) copiées/optimisées depuis Silver.

---

## Schéma de toutes les colonnes Silver

### `silver.dim_utilisateur`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | BIGINT | Clé technique (hash) |
| `username` | STRING | Login utilisateur |
| `full_name` | STRING | Nom complet |
| `email` | STRING | Adresse email |
| `type_profil` | STRING | Profil métier (data scientist, analyste, ops…) |
| `type_contrat` | STRING | `Interne` / `Externe` |
| `active` | BOOLEAN | Utilisateur actif |
| `group_norm` | STRING | Groupe normalisé |
| `creationdate` | TIMESTAMP | Date de création du compte |
| `snapshot_dt` | TIMESTAMP | Date du snapshot source |
| `loaded_at` | TIMESTAMP | Horodatage d'ingestion |
| `updated_at` | TIMESTAMP | Horodatage de mise à jour |

### `silver.dim_licence`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | BIGINT | Clé technique (hash) |
| `type` | STRING | Type de licence normalisé |
| `max_licences` | INT | Nombre maximum de licences |
| `licences_used` | INT | Licences utilisées |
| `quotas` | INT | Licences disponibles (max - used) |
| `unlimited` | BOOLEAN | Licence sans limite |
| `start_date` | DATE | Début de validité |
| `end_date` | DATE | Fin de validité |
| `loaded_at` | TIMESTAMP | Horodatage d'ingestion |
| `updated_at` | TIMESTAMP | Horodatage de mise à jour |

### `silver.dim_instance`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | BIGINT | Clé technique (hash) |
| `environment` | STRING | DEV / INT / RPP / PROD |
| `type` | STRING | design / automation / autre |
| `instance_name` | STRING | Nom de l'instance Dataiku |
| `loaded_at` | TIMESTAMP | Horodatage d'ingestion |
| `updated_at` | TIMESTAMP | Horodatage de mise à jour |

### `silver.dim_project`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | BIGINT | Clé technique (hash) |
| `project_key` | STRING | Identifiant projet Dataiku |
| `folder_path` | STRING | Arborescence hiérarchique des dossiers |
| `loaded_at` | TIMESTAMP | Horodatage d'ingestion |
| `updated_at` | TIMESTAMP | Horodatage de mise à jour |

### `silver.dim_usage`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | BIGINT | Clé technique (hash) |
| `asset` | STRING | Type d'asset (dataset, project, scenario, job…) |
| `activity` | STRING | Action réalisée |
| `activity_type` | STRING | Catégorie (Consultation, Développement, Industrialisation, Surveillance) |
| `loaded_at` | TIMESTAMP | Horodatage d'ingestion |
| `updated_at` | TIMESTAMP | Horodatage de mise à jour |

### `silver.dim_instance_licence_utilisateur`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | BIGINT | Clé technique (hash) |
| `instance_id` | BIGINT | FK → dim_instance |
| `licence_id` | BIGINT | FK → dim_licence |
| `user_id` | BIGINT | FK → dim_utilisateur |
| `creationdate` | TIMESTAMP | Date d'attribution |
| `snapshot_dt` | TIMESTAMP | Date du snapshot |
| `loaded_at` | TIMESTAMP | Horodatage d'ingestion |
| `updated_at` | TIMESTAMP | Horodatage de mise à jour |
