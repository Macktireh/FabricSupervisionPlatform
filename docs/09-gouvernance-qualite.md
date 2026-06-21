# Gouvernance, Qualité & Sécurité

## Contrôles qualité des données

### Intégrité référentielle (NB_Audit_Silver)

Avant d'écrire dans `silver.audit_logs`, chaque ligne de `bronze.audit_logs_prep` est validée contre les dimensions de référence.

| Contrôle | Dimension référence | Action si invalide |
|----------|--------------------|--------------------|
| `(asset, action)` connu | `silver.dim_usage` | Rejet → `tech.rejects` |
| `project_key` connu | `silver.dim_project` | Rejet → `tech.rejects` |
| `user` connu | `silver.dim_utilisateur` | Rejet → `tech.rejects` |
| `instance` connue | `silver.dim_instance` | Rejet → `tech.rejects` |

### Table `tech.rejects`

Chaque rejet est tracé avec :
- `reject_date` : date du contrôle
- `reject_reason` : motif (`asset_action_inconnu`, `projet_inconnu`, `utilisateur_inconnu`, `instance_inconnue`)
- `reject_field` : champ en cause
- `rejected_line` : ligne source brute

**Utilisation** : les rejets doivent être analysés régulièrement par l'équipe Data Platform pour identifier des écarts entre les référentiels source et les données d'usage.

### Cohérence du nombre de licences

Un contrôle de cohérence compare le nombre de licences dans `dim_licence` avec le référentiel maître Dataiku. Des ruptures brutales de volume (ex: 0 licence un jour) déclenchent une alerte vers la Data Platform.

### Détection d'anomalies

| Anomalie | Indicateur |
|----------|-----------|
| Rupture de volume d'usage | Baisse soudaine > X% du nombre de sessions par rapport à J-7 |
| Pipeline en échec | `end_time IS NULL` dans `tech.execution_log` après le délai attendu |
| Données figées | `Date_Actualisation` non mise à jour depuis > 48h |

---

## Traçabilité des exécutions

### `tech.execution_log`

Trace chaque run de notebook/pipeline :
- `start_time` : inséré dès le démarrage
- `end_time` : mis à jour à la fin (NULL = run en cours ou en échec)
- `stat` : métriques libres (`nb_inserted`, `nb_rejected`, etc.)

**Principe de résilience** : si un run échoue (`end_time` reste NULL), le prochain run reprend depuis le `MAX(start_time)` du dernier run **complet** (`end_time IS NOT NULL`). Aucune donnée n'est perdue.

### Idempotence

- **Bronze** : append only, la clé `snapshot_date` empêche le rechargement de données déjà présentes.
- **Silver** : reconstruction complète à chaque run (idempotent par nature).
- **Gold** : MERGE sur clé hash → les re-runs ne créent pas de doublons.

---

## Sécurité des accès

### Contrôle d'accès au rapport

| Profil | Périmètre accessible |
|--------|---------------------|
| **Data Platform / Licence Manager** | Toutes les données (tous environnements, toutes BU, utilisateurs nominatifs si autorisé) |
| **Manager BU / Référent Dataiku** | Données filtrées sur sa BU/équipe uniquement (RLS Power BI) |
| **Consommateurs métier** | Agrégats uniquement (vues sans données nominatives) |

### Row-Level Security (RLS)

Le Semantic Model peut être configuré avec des rôles RLS Power BI pour restreindre l'accès aux données par BU/équipe selon le profil de l'utilisateur connecté. Les vues managériales agrègent au niveau équipe sans exposer les identités individuelles.

### Pas d'élévation de privilège

Les consommateurs ne voient que les agrégats correspondant à leur niveau d'habilitation. L'accès nominatif (niveau utilisateur) est réservé aux profils Data Platform et aux référents licences légitimes.

---

## Conformité RGPD

### Données personnelles concernées

| Donnée | Justification de collecte |
|--------|--------------------------|
| Login / alias utilisateur | Pilotage des licences (identifiant licencié) |
| Email | Dérivation du type de contrat (Interne/Externe) |
| Groupe/équipe | Rattachement organisationnel pour agrégation |

### Mesures de protection

| Mesure | Implémentation |
|--------|---------------|
| Minimisation | Seules les données nécessaires au pilotage des licences sont intégrées (pas de contenu de projets, pas de logs fins) |
| Pseudonymisation | Possible dans les vues managériales (agrégation par équipe sans identité nominative) |
| Droit d'accès | Restreint par rôles Fabric et RLS Power BI |
| Traçabilité | Logs d'accès au dashboard (audit Fabric) + logs de rafraîchissement |
| Pas d'exposition inutile | Le Data Agent exclut les comptes techniques et filtre les résultats selon le contexte |

### Exclusion des données sensibles

Ne sont **pas** intégrés en V1 :
- Contenu des projets Dataiku (code, recettes, données métier)
- Détails techniques fins des logs (paramètres d'exécution, stack traces)
- Données d'environnements non maîtrisés par la Data Platform

---

## Gestion des incidents

### En cas d'échec d'ingestion

1. Le Lakehouse conserve le dernier jeu de données valide (les tables Gold ne sont pas écrasées).
2. Le Semantic Model continue d'exposer les données de la dernière mise à jour réussie.
3. `Date_Actualisation` indique la date de fraîcheur aux utilisateurs du rapport et du Data Agent.
4. Une alerte est remontée vers la Data Platform (via monitoring du pipeline).

### En cas d'anomalie qualité

1. Vérifier `tech.rejects` pour identifier la nature des rejets.
2. Investiguer le référentiel source (dim_usage, dim_project, etc.) pour les éventuels manques.
3. Corriger le référentiel et relancer le pipeline (idempotent, sans risque de doublon).

---

## Évolutivité

### Extension à d'autres sources (V2/V3)

Le modèle est conçu pour accueillir de nouveaux périmètres sans refonte majeure :

| Périmètre futur | Nouveaux composants nécessaires |
|----------------|--------------------------------|
| Microsoft Fabric | `fait_workspace_usage`, `dim_workspace`, `dim_artefact`, `dim_capacite` |
| Data Catalog | `fait_data_catalog_usage`, `dim_objet_catalogue`, `dim_domaine` |

### Enrichissement des dimensions

- Ajout de `domain` et `sub_domain` dans `dim_project` (extrait du `folder_path`)
- Connexion avec l'annuaire OKTA pour la gestion des utilisateurs (prévu)
- Table `Actions_Licence` (historique des décisions de réallocation)

### Nouveaux indicateurs

- Granularités plus fines (heure, semaine ISO)
- Indicateurs de maturité usage (diversité des types d'activités par utilisateur)
- Coût par utilisateur actif (si coûts unitaires disponibles)
- "Chat with my KPI Platform" (fonctionnalité Data Agent enrichie)
