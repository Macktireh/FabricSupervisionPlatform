# Semantic Model – SM_Composite_SupervisionPlatformEndUser

## Vue d'ensemble

Le Semantic Model est le **cœur analytique** de la plateforme. Il expose les tables Gold du Lakehouse en mode **DirectLake**, définit les relations, les mesures DAX et les KPIs métier utilisés à la fois par le rapport Power BI et le Data Agent IA.

**Nom** : `SM_Composite_SupervisionPlatformEndUser`  
**Mode** : DirectLake (connexion directe aux tables Delta du Lakehouse, sans import)  
**Format** : TMDL (Tabular Model Definition Language)

## Tables du modèle

### Tables de faits

| Table | Grain | Description |
|-------|-------|-------------|
| `fait_usage_dataiku_utilisateur` | User × Projet × Jour × Session | Activité utilisateur (sessions, durées, jobs, scénarios) |

### Dimensions conformées

| Table | Description |
|-------|-------------|
| `dim_utilisateur` | Utilisateurs (profil, contrat, groupe, isTechAccount) |
| `dim_licence` | Types de licences (type, max, quotas, priorité, dates) |
| `dim_instance` | Instances Dataiku (environnement, type) |
| `dim_project` | Projets (project_key, arborescence, domaine) |
| `dim_calendrier` | Calendrier (DATE, attributs ISO/Gregorian, flags MTD/YTD) |
| `dim_usage` | Types d'activités (asset, action, catégorie) |

### Tables ponts & helpers

| Table | Description |
|-------|-------------|
| `dim_instance_licence_utilisateur` | Pont utilisateur ↔ licence ↔ instance (assignation) |
| `dim_max_user_licence` | Licence de plus haute priorité par utilisateur |
| `dim_status_opt` | Référentiel des statuts d'optimisation |

### Tables de support / UI

| Table | Description |
|-------|-------------|
| `Indicateurs` | Table de regroupement des mesures DAX calculées |
| `Colors` | Palettes de couleurs (LightMode, DarkMode, palettes FDJ) |
| `Icons` | Icônes pour les visuels |
| `Theme` | Métadonnées du thème |
| `Date_Actualisation` | Date du dernier rafraîchissement du Semantic Model |

## Relations (11 relations actives)

```
dim_instance_licence_utilisateur.instance_id  ──M:1──▶  dim_instance.id
dim_instance_licence_utilisateur.licence_id   ──M:1──▶  dim_licence.id
dim_instance_licence_utilisateur.user_id      ──M:1──▶  dim_utilisateur.id

fait_usage_dataiku_utilisateur.instance_id    ──M:1──▶  dim_instance.id
fait_usage_dataiku_utilisateur.project_id     ──M:1──▶  dim_project.id
fait_usage_dataiku_utilisateur.user_id        ──M:1──▶  dim_utilisateur.id
fait_usage_dataiku_utilisateur.timestamp_dt   ──M:1──▶  dim_calendrier.DATE
fait_usage_dataiku_utilisateur.usage_id       ──M:1──▶  dim_usage.id
fait_usage_dataiku_utilisateur.licence_id     ──M:1──▶  dim_licence.id

dim_max_user_licence.user_id                  ──M:1──▶  dim_utilisateur.id  (bidirectionnel)
Date_Actualisation.Date_Actualisation         ──M:1──▶  LocalDateTable.Date
```

## Mesures DAX principales

Les mesures sont regroupées dans la table `Indicateurs`. Elles respectent les conventions de nommage suivantes :
- `Nb [Entité] [Période]` pour les counts
- `Taux [Indicateur]` pour les ratios
- `[KPI] M-1` pour la période précédente (Month-over-Month)

### Indicateurs d'adoption

| Mesure | Formule (simplifiée) |
|--------|---------------------|
| `Nb Utilisateurs Actifs` | `DISTINCTCOUNT(fait_usage[user_id])` (hors comptes techniques) |
| `Nb Utilisateurs Actifs M-1` | Idem, filtré sur le mois précédent |
| `Nb Nouveaux Utilisateurs` | Utilisateurs dont `first_connection` est dans les 7 derniers jours |
| `Nb Licences Attribuées` | `DISTINCTCOUNT(dim_instance_licence_utilisateur[user_id])` |
| `Nb Licences Max (Dotation)` | `SUM(dim_licence[max_licences])` WHERE `unlimited ≠ TRUE` |
| `Taux Activation Licences` | `Nb Licences Actives / Nb Licences Attribuées` |

### Indicateurs d'usage

| Mesure | Formule (simplifiée) |
|--------|---------------------|
| `Nb Sessions` | `COUNTROWS(fait_usage_dataiku_utilisateur)` |
| `Nb Sessions M-1` | Idem, mois précédent |
| `Durée Totale Sessions (min)` | `SUM(fait_usage[session_duration_minutes])` |
| `Durée Moy Session (min)` | `AVERAGE(fait_usage[session_duration_minutes])` |
| `Nb Projets Actifs` | `DISTINCTCOUNT(fait_usage[project_id])` |
| `Nb Jobs Exécutés` | `SUM(fait_usage[jobs_count])` |
| `Nb Scénarios Exécutés` | `SUM(fait_usage[scenarios_count])` |
| `Nb Sessions / Utilisateur` | `[Nb Sessions] / [Nb Utilisateurs Actifs]` |

### Indicateurs de pilotage licences

| Mesure | Formule (simplifiée) |
|--------|---------------------|
| `Nb Licences Inactives` | Licences attribuées avec `statut_optimisation = 'inactive'` |
| `Nb Licences Sous-utilisées` | Licences avec `statut_optimisation = 'sous_utilisee'` |
| `Ratio Dotation/Utilisation` | `Nb Utilisateurs Actifs / Nb Licences Attribuées` |
| `Quotas Restants` | `SUM(dim_licence[quotas])` |
