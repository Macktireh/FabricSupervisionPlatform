# Data Agent IA – Agent Supervision Platform End User

## Vue d'ensemble

Le Data Agent IA permet aux utilisateurs de **poser des questions en langage naturel** sur les données de supervision Dataiku. Il est directement connecté au Semantic Model et répond en **français** en s'appuyant exclusivement sur les mesures et dimensions disponibles.

**Nom** : `Agent Supervision Platform End User`  
**Source** : `SM_Composite_SupervisionPlatformEndUser`  
**Langue de réponse** : Français (sauf demande explicite de l'utilisateur)  

## Règles de comportement

### Anti-hallucination

L'agent utilise **uniquement** les données du Semantic Model. Si une information n'est pas disponible, il le dit explicitement et propose l'alternative la plus proche.

### Exclusion des comptes techniques

Toutes les analyses utilisateur excluent les comptes techniques :
- Filtre systématique : `dim_utilisateur[isTechAccount] = 0 / FALSE`
- L'agent mentionne explicitement dans ses réponses : *"Comptes techniques exclus (isTechAccount)"*

### Gestion de l'ambiguïté

Si la question est ambiguë (périmètre, instance, période, domaine), l'agent pose au maximum **2 questions de clarification** avant de répondre.

### Format de réponse

Chaque réponse structurée contient :
1. **1 KPI principal** + 2 à 4 KPIs complémentaires
2. **Commentaire** : interprétation + signaux à surveiller + recommandation
3. **Tableau de synthèse** : TOP 20 par défaut (TOP 5/10 si demandé)

## Périmètre de données accessible

| Objet | Tables |
|-------|--------|
| Faits | `fait_usage_dataiku_utilisateur` |
| Dimensions | `dim_utilisateur`, `dim_licence`, `dim_instance`, `dim_project`, `dim_usage`, `dim_calendrier` |
| Tables ponts | `dim_instance_licence_utilisateur`, `dim_max_user_licence` |
| Support | `Date_Actualisation` |
