# Rapport Power BI – Supervision Platform End User

## Vue d'ensemble

Le rapport Power BI est connecté au Semantic Model en mode **DirectLake** et expose les indicateurs de supervision Dataiku à travers avec un thème corporate FDJ (dark/light).

**Nom** : `Supervision Platform End User`  
**Source** : `SM_Composite_SupervisionPlatformEndUser` (DirectLake)  
**Thème** : Thème FDJ personnalisé (dark/light)
**Export** : Mode `AllowSummarized`

## Structure des pages

### Page 1 – Cockpit Licences (40+ visuels)

Vue synthétique globale du parc de licences Dataiku.

**Sections typiques** :
- KPI Cards : Nb licences attribuées, Nb utilisateurs actifs, Taux d'activation, Nb licences inactives
- Répartition des licences par type (Designer, Explorer, Reader, Platform Admin, AI Consumer)
- Taux d'activation par BU / équipe (graphique barres ou tableau)
- Licences inactives et sous-utilisées (highlighting)
- Ratio dotation/utilisation global et par environnement

**Filtres disponibles** :
- Environnement (DEV / INT / RPP / PROD)
- Type de licence
- Période (semaine, mois, trimestre)

---

### Page 2 – Analyse Détaillée (30+ visuels)

Analyse drill-down par dimension (équipe, utilisateur, environnement).

**Sections typiques** :
- Tableau détaillé utilisateurs : sessions, durée, projets actifs, statut licence
- Répartition par profil utilisateur (data scientist, analyste, ops…)
- Répartition Interne vs Externe
- Activité par environnement (barres groupées DEV/INT/RPP/PROD)
- Top N utilisateurs les plus actifs (hors comptes techniques)

**Filtres disponibles** :
- Direction / BU / Équipe
- Type de contrat (Interne / Externe)
- Profil utilisateur

---

### Page 3 – Adoption & Tendances (13 visuels)

Suivi de l'évolution de l'adoption dans le temps.

**Sections typiques** :
- Courbe évolution utilisateurs actifs (mensuelle)
- Comparaisons MoM (Month-over-Month) : M vs M-1
- Nouveaux utilisateurs par période
- Tendance sessions et durée moyenne
- Heatmap d'activité (jours × heures si disponible)

---

### Page 4 – Projets & Activités (40+ visuels)

Analyse centrée sur les projets, scénarios et jobs.

**Sections typiques** :
- Top projets actifs (nb d'utilisateurs actifs, nb sessions)
- Répartition par type d'activité (Développement, Industrialisation, Consultation, Surveillance)
- Nb scénarios et jobs exécutés par environnement et par équipe
- Projets avec peu ou pas d'activité (candidats à l'archivage)
- Distribution de l'activité par domaine projet

---

## Thème et design

### Thème FDJ

Le rapport utilise un thème JSON personnalisé FDJ avec :
- Support **dark mode** et **light mode**
- Palette de couleurs FDJ United (primaires, secondaires, accents)
- Logo FDJ UNITED
- Typographie et espacement cohérents avec la charte graphique FDJ

### Tables de support UI dans le Semantic Model

| Table | Rôle |
|-------|------|
| `Colors` | Palettes LightMode/DarkMode accessibles en DAX (`SELECTEDVALUE(Colors[LightMode])`) |
| `Icons` | Icônes utilisées dans les KPI cards et les slicers |
| `Theme` | Métadonnées du thème actif (couleur primaire, secondaire…) |

---

## Publication et accès

Le rapport est publié dans le workspace Fabric **FDJ-FR-EUP-FABRIC-FEATURES**.
