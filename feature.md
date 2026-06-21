1. Périmètre global

1.1 🎯 Objectif

Mettre en place, dans Microsoft Fabric, un cadre standardisé de supervision des usages “End User”, en commençant par Dataiku sur les environnements DEV, INT, RPP et PROD, afin de :

piloter finement l’attribution des licences (dotation vs utilisation réelle),

suivre l’adoption et l’intensité d’usage par périmètre (équipes, projets, profils d’utilisateurs),

identifier les optimisations possibles (surdotation, sous-dotation, licences inactives ou peu utilisées),

préparer l’extension du dispositif à l’ensemble du périmètre End User :

Microsoft Fabric

Data Catalog

Dataiku

V1 : se concentrer sur Dataiku, construire un modèle de supervision robuste (indicateurs, axes d’analyse) et un dashboard Fabric de référence.

1.2 ⚙️ Stack cible / sources

Cible principale : Microsoft Fabric

Lakehouse de supervision “End User” (zone de consolidation des métriques d’usage).

Semantic Model / Dataset de supervision :

tables de faits d’usage et de licences,

dimensions Temps, Utilisateur, Organisation, Environnement, Licence, Usage.

Dashboard Power BI (ou rapport Fabric) exposant :

vues synthétiques (cockpit licences),

vues détaillées (drill-down par équipe, utilisateur, environnement).

Sources de données V1 (Dataiku) :

Logs Dataiku des environnements DEV, INT, RPP, PROD :

connexions utilisateurs / sessions,

projets, scénarios, jobs exécutés,

Référentiel licences Dataiku :

type de licence (Designer, Explorer, etc.),

licence attribuée à quel utilisateur,

coût unitaire (espace données sensibles)

Référentiels organisation :

mapping utilisateur →  direction / équipe / projet,

Périmètre futur :

Microsoft Fabric : usages workspaces, artefacts (Lakehouse, notebooks, pipelines, Power BI), consommation ressources / capacités.

Data Catalog : consultation, contribution, complétude / fraîcheur de la documentation.

1.3 🚧 Contraintes et hypothèses

V1 limitée à Dataiku (DEV, INT, RPP, PROD).

Seules les métriques fiables et traçables sont intégrées en V1 :

logs d’authentification,

logs d’activité projet / scénario / job,

référentiel licences maîtrisé.

Les règles de sécurité (RGPD, confidentialité, etc.) s’appliquent :

pas d’exposition de données nominatives au-delà de ce qui est nécessaire pour le pilotage des licences,

possibilité d’agréger / pseudonymiser les utilisateurs dans certaines vues (ex : vues managériales).

L’usage de la supervision est read-only pour les consommateurs métier :

aucun impact direct sur la gestion des licences,

les décisions de réallocation sont portées par l’équipe Data Platform / référents utilisateurs.

La V1 privilégie :

un set d’indicateurs core (dotation/utilisation),

un scope limité d’axes (Temps, Organisation, Environnement, Utilisateur, Usage),

une fréquence de mise à jour adaptée (quotidienne ou hebdo selon la faisabilité d’ingestion).

2. Architecture logique de supervision “End User”

2.1 🗃️ Couches de données

Sources “End User” (V1 = Dataiku)

Logs Dataiku (connexions, sessions, jobs, projets).

Référentiel licences Dataiku.

Référentiel organisation (équipe, projet, référent).

Zone de landing / ingestion Fabric

Lakehouse Fabric – zone brute :

tables techniques issues des exports/logs Dataiku 

tables de mapping licences / utilisateurs (utilisateurs issus du ID Provider OKTA dans une version ultérieure)

Pipelines d’alimentation (séquencement, historisation basique).

Couche de préparation / modèle opératoire

Tables préparées :

table des événements d’usage (connexion, exécution de job, modification de projet),

table des périmètres organisationnels (jointure utilisateur ↔ équipe/projet/fonction),

table des licences attribuées.

Couche décisionnelle / BUS de supervision

Tables de faits :

Fait_Usage_Dataiku_Utilisateur,

Fait_Licence_Dataiku.

Dimensions :

Dim_Temps, Dim_Utilisateur, Dim_Organisation, Dim_Environnement, Dim_Licence, Dim_Usage.

Règles :

grains clairs (par jour, par période de reporting),

statuts d’optimisation calculés (ok, sous-utilisée, inactive).

Couche d’exposition (Semantic Model / rapport)

Semantic Model Fabric / Power BI :

indicateurs standardisés,

mesures d’analyse (taux d’activation, ratios dotation/utilisation, etc.).

Dashboard de supervision :

cockpit licences et adoption,

analyse détaillée par équipe, environnement, type d’usage.

2.2 🧩 Matrice de BUS (vue initiale)

Faits

Fait_Usage_Dataiku_Utilisateur

Grain :

par utilisateur et par jour

Mesures principales :

nb_sessions

duree_totale_session

nb_projets_actifs

nb_scenarios_executes

nb_jobs_executes (si distinction utile)

Fait_Licence_Dataiku

Grain :

une ligne par licence et par période de reporting (ex : hebdomadaire).

Mesures principales :

licence_attribuee (booléen)

date_attribution

date_derniere_utilisation

nb_connexions_periode

nb_jours_actifs_periode (j au moins une session)

statut_optimisation (ok, sous_utilisee, inactive)

cout_unitaire (si disponible)

Dimensions

Dim_Temps :

jour, semaine, mois, trimestre, année, flags (YTD, MTD…).

Dim_Utilisateur :

id_utilisateur,

login / alias (avec gestion RGPD à cadrer),

type_profil (data scientist, analyste, métier, IT, autre),

type_contrat (Interne vs Externe).

Dim_Organisation :

direction, équipe,

projet, type_projet (POC, RUN, expérimentation : a identifier en fonction de son emplacement dans l’arborescence DSS)

Dim_Environnement :

environnement (DEV, INT, RPP, PROD),

type_environnement (dev, intégration, pré-prod, prod).

Dim_Licence :

type_licence (Designer, Explorer, etc.),

cout_unitaire,

quotas

Date début de validité

Date de fin de validité

Dim_Usage :

type_activite (exploration, préparation, modélisation, industrialisation, consommation),

categorie_usage (développement, exécution, maintenance),

criticite_usage (ex : critique, standard, expérimental).

2.3 🌐 Extension future périmètre End User

Dans une phase ultérieure, le même modèle de supervision sera étendu à :

Microsoft Fabric :

Faits supplémentaires : usage workspaces, consommation capacités, exécutions pipelines/notebooks, vues Power BI.

Dimensions : Workspace, Artefact, Capacité, Type_ressource, etc.

Data Catalog :

Faits : consultations de fiches, créations/modifications, validations, commentaires.

Dimensions : Objet_catalogue, Domaine, Owner, Qualite_documentation (complétude, fraîcheur).

Objectif cible : cockpit unique de supervision End User (Fabric + Data Catalog + Dataiku).

3. Cadrage d’utilisation – supervision Dataiku (V1)

3.1 🔎 Périmètre fonctionnel V1

Produit : Dataiku
Environnements : DEV, INT, RPP, PROD

Population cible :

Équipe Data Platform (pilotage licences, capacity planning).

Responsables BU / Domaines / Équipes consommateurs de Dataiku.

Éventuellement, référents Dataiku locaux (per-BU, per-projet).

Principaux cas d’usage V1 :

Visualiser la dotation en licences par BU / équipe / type de licence.

Mesurer l’utilisation effective (activité) par utilisateur et par licence.

Identifier :

les licences inactives (0 usage sur période),

les licences sous-utilisées (usage marginal),

les périmètres en tension (usage très fort vs dotation limitée).

Suivre l’adoption de Dataiku :

évolution du nb d’utilisateurs actifs,

montée en charge des projets actifs, scénarios, jobs.

3.2 📊 Indicateurs V1

Indicateurs de volumétrie et d’adoption

Nombre total de licences Dataiku par type (Designer, Explorer…).

Nombre d’utilisateurs actifs (jour/semaine/mois).

Taux d’activation des licences =
nb_licences_ayant_au_moins_une_connexion / nb_licences_attribuees.

Répartition des utilisateurs actifs par environnement (DEV, INT, RPP, PROD).

Répartition des utilisateurs par BU / équipe / projet.

Nombre de nouveaux utilisateurs sur la période.

Indicateurs d’usage effectif

Nombre moyen de sessions par utilisateur et par période.

Durée moyenne des sessions.

Nombre de projets actifs (au moins une action dans la période).

Nombre de scénarios et de jobs exécutés par environnement.

Volumétrie des datasets manipulés (lignes, Go) si disponible.

Indicateurs de pilotage des licences

Ratio dotation/utilisation par BU, équipe, projet.

Nombre de licences inactives (aucune connexion sur la période).

Nombre de licences faiblement utilisées (en dessous d’un seuil à définir, ex : < X sessions / mois ou < Y jours actifs).

Gains potentiels estimés par :

réallocation de licences inactives ou sous-utilisées,

adaptation de la dotation par BU.

3.3 📥 Règles d’éligibilité des données

Sont intégrés :

les événements d’usage Dataiku tracés dans les logs ou API,

les licences gérées dans le référentiel officiel,

les mappings utilisateur ↔ organisation disponibles.

Ne sont pas intégrés en V1 :

données personnelles non nécessaires au pilotage (contenu des projets, détails techniques fins),

environnements / instances non maîtrisés par la Data Platform.

3.4 🔐 Sécurité & gouvernance

Accès au dashboard :

restreint aux équipes Data Platform, aux managers habilités et aux référents licences.

Pas d’élévation de privilège :

on ne voit que les agrégats autorisés (par BU/équipe) et les identités lorsqu’elles sont légitimes pour le rôle.

Traçabilité :

logs d’accès au dashboard,

logs des rafraîchissements (pipelines d’ingestion / calculs).

4. Scénarios d’usage et flux utilisateurs

4.1 👩‍💼 Data Platform / Licence Manager

Ouvre le cockpit licences Dataiku dans Fabric.

Visualise :

la dotation globale par type de licence,

le taux d’activation par BU / équipe.

Identifie les BU / équipes :

avec un fort taux de licences inactives ou sous-utilisées,

ou au contraire en tension (fort usage vs dotation faible).

Exporte la liste des licences concernées (niveau utilisateur si autorisé) pour :

proposer des réallocations,

ajuster les commandes / renouvellements.

4.2 👨‍💼 Manager BU / Référent Dataiku

Consulte la vue filtrée sur sa BU / équipe.

Suit l’adoption :

nb d’utilisateurs actifs, tendance,

projets actifs, activités clés.

Identifie :

des collaborateurs n’utilisant pas ou peu leur licence,

des équipes particulièrement consommatrices.

Partage ces éléments avec la Data Platform pour :

optimiser les dotations,

organiser des actions d’accompagnement (formation, onboarding).

5. Non-fonctionnel

5.1 📈 Performance

Fréquence de rafraîchissement cible : quotidien (à ajuster selon la charge).

Dashboard :

temps de réponse acceptable pour les principaux filtres (BU, période, environnement).

Surveillance :

temps de rafraîchissement des pipelines,

volumétrie des tables de faits (usage, licences).

5.2 🧱 Robustesse & résilience

En cas d’échec d’ingestion :

dernier jeu de données valide reste exposé,

alerte vers Data Platform.

Contrôles qualité :

cohérence du nombre de licences vs référentiel maître,

détection d’anomalies (rupture brutale de volume d’usage).

5.3 🔄 Évolutivité

Ajout progressif de :

nouveaux indicateurs (ex : granularités plus fines, indicateurs de maturité),

nouveaux périmètres (Fabric, Data Catalog).

Nouvelles fonctionnalités : “chat with my KPI Platform”

Capacité à :

enrichir les dimensions (organisation, usage),

historiser les décisions de réallocation (future table de faits “Actions_licence”).

6. Artefacts à produire (V1)

Diagramme d’architecture Fabric de la supervision End User :

Sources Dataiku / référentiels → Lakehouse → modèle BUS → Semantic Model → Dashboard.

Spécification BUS détaillée :

dictionnaire des faits et dimensions,

grain, règles de calcul des mesures.

Spécification des indicateurs :

définition métier,

formule de calcul,

grain temporel, filtres applicables.

Maquette du dashboard :

pages, sections, filtres,

visuels clés (cockpit, analyses détaillées).

Guide d’exploitation V1 :

qui utilise quoi, pour quelles décisions,

limites connues (données manquantes, approximations).