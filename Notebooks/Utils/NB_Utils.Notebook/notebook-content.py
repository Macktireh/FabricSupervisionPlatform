# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "e5a494bb-2c9c-44ec-9fd3-494add93bd08",
# META       "default_lakehouse_name": "Lakehouse_End_User_Platform",
# META       "default_lakehouse_workspace_id": "cae55539-e164-4a36-bb47-62c5bb2cbee7",
# META       "known_lakehouses": [
# META         {
# META           "id": "e5a494bb-2c9c-44ec-9fd3-494add93bd08"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

import datetime

class ExecutionLogger():
    """
    Classe utilitaire pour journaliser l'exécution d'un traitement dans une table Delta
    (tech.execution_log).

    Cette classe permet de :
      - marquer le début d'une exécution (insertion d'une ligne dans tech.execution_log),
      - récupérer la date/heure de début de l'exécution courante,
      - récupérer la dernière date/heure d'exécution terminée pour une étape donnée,
      - marquer la fin de l'exécution et enregistrer des métriques associées.

    Paramètres
    ----------
    lh_level : str
        Niveau de la couche (ex. 'bronze', 'silver', 'gold').
    table_name : str
        Nom logique de la table/étape à tracer. Utilisé pour construire etape_name.
    """

    _lh_level:str = "";
    _table_name:str = "";
    _etape_name:str = "";
    _start_time:datetime;
    _run_id:str = ""

    def __init__(self, lh_level, table_name):
        """
        Initialise un nouvel ExecutionLogger pour une table/niveau donné.

        Parameters
        ----------
        lh_level : str
            Niveau de la couche (ex. 'bronze', 'silver', 'gold').
        table_name : str
            Nom de la table ou de l'étape fonctionnelle.
        """
        self._lh_level = lh_level
        self._table_name = table_name
        self._etape_name = f'{self._lh_level}.{self._table_name}'

    def execution_start(self):
        """
        Enregistre le début de l'exécution dans tech.execution_log.

        Crée un identifiant d'exécution (run_id) unique à partir de la date/heure
        courante et du nom d'étape, insère une ligne dans la table
        tech.execution_log et crée une vue temporaire
        'current_run_<table_name>' contenant les informations de cette exécution.

        """
        self._start_time = datetime.datetime.now()
        self._run_id = str(self._start_time)+'|' + self._etape_name
        log_line = spark.sql(f"""
        SELECT 
            '{self._run_id}' as run_id, 
            '{self._etape_name}' as etape_name, 
            cast('{self._start_time}' as timestamp) as start_time
        """)
        log_line.createOrReplaceTempView(f'current_run_{self._table_name}')
        print(f"Last starttime is also available in temp view 'current_run_{self._table_name}'")
        log_line.write.format("delta") \
            .mode("append") \
            .saveAsTable("tech.execution_log")
        
    def get_start_time(self) -> datetime:
        """
        Retourne la date/heure de début de l'exécution courante.

        Returns
        -------
        datetime.datetime
            Timestamp de début fixé lors de l'appel à execution_start().
        """
        return self._start_time

    def get_last_execution_time(self) -> datetime:
        """
        Récupère la dernière date/heure d'exécution terminée pour cette étape.

        La valeur retournée correspond au MAX(start_time) dans tech.execution_log
        pour l'etape_name courant, filtré sur les exécutions complétées
        (end_time IS NOT NULL). Si aucune exécution n'est trouvée, retourne
        le timestamp par défaut '2025-01-01 00:00:00'.

        Returns
        -------
        datetime.datetime
            Dernière date/heure d'exécution terminée ou valeur par défaut.
        """
        last_execution_time = spark.sql(f"""
            SELECT 
                COALESCE(MAX(start_time), TO_TIMESTAMP('2025-01-01 00:00:00')) as last_time
            FROM
                tech.execution_log
            CROSS JOIN
                (SELECT 1)
            WHERE
                etape_name = '{self._etape_name}'
                AND end_time IS NOT NULL
        """).first()["last_time"]
        return last_execution_time
    
    def execution_end(self, metrics:dict[str, int]=None):
        """
        Marque la fin de l'exécution et met à jour la ligne de log correspondante.

        Met à jour la table tech.execution_log pour le run_id courant avec :
          - la date/heure de fin (end_time),
          - éventuellement un champ stat de type MAP contenant des métriques
            (par exemple nombre de lignes maj/écrites).

        Parameters
        ----------
        metrics : dict[str, int], optional
            Dictionnaire de métriques à enregistrer dans la colonne stat
            (clé = nom de la métrique, valeur = entier). Si None, aucune métrique
            supplémentaire n'est enregistrée.
        """
        end_time = datetime.datetime.now()
        if metrics:
            metrics_kv = [f"'{metrics_field}',{metrics[metrics_field]}" for metrics_field in metrics.keys()]
            stat_field = ", stat = MAP(" + ",".join(metrics_kv) + ")"
        else:
            stat_field = ""
        spark.sql(f"""
            UPDATE tech.execution_log
            SET end_time = '{end_time}'
            {stat_field}
            WHERE run_id = '{self._run_id}'
        """)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
