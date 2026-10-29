[StagingDefinition = [Kind = "FastCopy"]]
section Section1;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "design_usage_licences_prep_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared usage_licences_prep = let
  Source = loadIncrementalStarburstTable("usage_licences_prep", "snapshot_date")
in
  Source;
shared WorkspaceId = let
  Source = Variable.Value("$(/**/VL_ENV_SupervisionPlatform/WorkspaceId)")
in
  Source;
shared LakehouseId = let
  Source = Variable.Value("$(/**/VL_ENV_SupervisionPlatform/LakehouseId)")
in
  Source;
shared SOURCE_HOST = "starburst.paas-datalake-data-2.dev.fdj.fr" meta [IsParameterQuery = true, IsParameterQueryRequired = true, Type = type text];
shared SOURCE_PORT = "443" meta [IsParameterQuery = true, IsParameterQueryRequired = true, Type = type text];
shared SOURCE_DATABASE = "lab_mnp_plt_hive" meta [IsParameterQuery = true, IsParameterQueryRequired = true, Type = type text];
shared SOURCE_SCHEMA = "lab_mnp_plt_plt" meta [IsParameterQuery = true, IsParameterQueryRequired = true, Type = type text];
shared SOURCE_INSTANCE_PREFIX_TABLE = "design" meta [IsParameterQuery = true, IsParameterQueryRequired = true, Type = type text];
shared SOURCE_INSTANCE_VALUE = "design_monopole_dev" meta [IsParameterQuery = true, IsParameterQueryRequired = true, Type = type text];
shared DESTINATION_SCHEMA = "bronze" meta [IsParameterQuery = true, IsParameterQueryRequired = true, Type = type text];
shared getCurrentParisDateTime = let
    getCurrentParisDateTime = () as datetime =>
    let
        utcNow = DateTimeZone.FixedUtcNow(),
        currentDate = DateTime.Date(utcNow),
        currentYear = Date.Year(currentDate),

        startDST = Date.AddDays(
            #date(currentYear, 3, 31),
            -Date.DayOfWeek(#date(currentYear, 3, 31), Day.Sunday)
        ),

        endDST = Date.AddDays(
            #date(currentYear, 10, 31),
            -Date.DayOfWeek(#date(currentYear, 10, 31), Day.Sunday)
        ),

        isDST = currentDate >= startDST and currentDate < endDST,
        offset = if isDST then 2 else 1,

        localDateTimeZone = DateTimeZone.SwitchZone(utcNow, offset),
        localDateTime = DateTimeZone.RemoveZone(localDateTimeZone)
    in
        localDateTime
in
    getCurrentParisDateTime;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "design_project_folder_prep_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared project_folder_prep = let
  Source = loadIncrementalStarburstTable("project_folder_prep", "snapshot_date")
in
  Source;
shared getLatestSnapshotDateFromLakehouseTable = let
    getLatestSnapshotDateFromLakehouseTable = (schemaName as text, tableName as text, snapshotDateColumnName as text) as any =>
        let
            lakehouseSource = Lakehouse.Contents(null),
            selectedWorkspaceNavigation = try lakehouseSource{[workspaceId = WorkspaceId]}[Data],
            selectedWorkspace =
                if selectedWorkspaceNavigation[HasError] then
                    error
                        Error.Record(
                            "LakehouseWorkspaceNotFound",
                            "Le workspace Lakehouse est introuvable.",
                            [
                                workspaceId = WorkspaceId
                            ]
                        )
                else
                    selectedWorkspaceNavigation[Value],
            selectedLakehouseNavigation = try selectedWorkspace{[lakehouseId = LakehouseId]}[Data],
            selectedLakehouse =
                if selectedLakehouseNavigation[HasError] then
                    error
                        Error.Record(
                            "LakehouseNotFound",
                            "Le Lakehouse est introuvable dans le workspace.",
                            [
                                workspaceId = WorkspaceId,
                                lakehouseId = LakehouseId
                            ]
                        )
                else
                    selectedLakehouseNavigation[Value],
            fullTableName = schemaName & "." & tableName,
            lakehouseTableRows = Table.SelectRows(
                selectedLakehouse, each [Id] = fullTableName and [ItemKind] = "Table"
            ),
            selectedTable =
                if Table.IsEmpty(lakehouseTableRows) then
                    error
                        Error.Record(
                            "LakehouseTableNotFound",
                            "La table Lakehouse est introuvable.",
                            [
                                schema = schemaName,
                                table = tableName,
                                fullTableName = fullTableName,
                                expectedItemKind = "Table"
                            ]
                        )
                else
                    lakehouseTableRows{0}[Data],
            validatedInstanceTable =
                if not List.Contains(Table.ColumnNames(selectedTable), "instance") then
                    error
                        Error.Record(
                            "MissingInstanceColumn",
                            "La colonne 'instance' est introuvable dans la table Lakehouse.",
                            [
                                fullTableName = fullTableName,
                                missingColumn = "instance",
                                availableColumns = Table.ColumnNames(selectedTable)
                            ]
                        )
                else
                    selectedTable,
            filteredInstanceTable = Table.SelectRows(validatedInstanceTable, each [instance] = SOURCE_INSTANCE_VALUE),
            latestSnapshotDateCalculated =
                if Table.IsEmpty(filteredInstanceTable) then
                    null
                else if not List.Contains(Table.ColumnNames(filteredInstanceTable), snapshotDateColumnName) then
                    error
                        Error.Record(
                            "MissingSnapshotDateColumn",
                            "La colonne snapshot demandée est introuvable dans la table Lakehouse.",
                            [
                                fullTableName = fullTableName,
                                snapshotDateColumnName = snapshotDateColumnName,
                                availableColumns = Table.ColumnNames(filteredInstanceTable)
                            ]
                        )
                else
                    try List.Max(Table.Column(filteredInstanceTable, snapshotDateColumnName)) otherwise null
        in
            latestSnapshotDateCalculated
in
    getLatestSnapshotDateFromLakehouseTable;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "design_users_prep_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared users_prep = let
  Source = loadIncrementalStarburstTable("users_prep", "snapshot_date")
in
  Source;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "design_scenario_runs_prep_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared scenario_runs_prep = let
  Source = loadIncrementalStarburstTable("scenario_runs_prep", "timestamp_dt")
in
  Source;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "design_jobs_prep_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared jobs_prep = let
  Source = loadIncrementalStarburstTable("jobs_prep", "timestamp_dt")
in
  Source;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "design_audit_logs_prep_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared audit_logs_prep = let
  Source = loadIncrementalStarburstTable("audit_logs_prep", "timestamp_dt")
in
  Source;
shared design_usage_licences_prep_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = WorkspaceId]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = LakehouseId]}[Data],
  Navigation_3 = Navigation_2{[Id = DESTINATION_SCHEMA, ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "usage_licences_prep", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared design_project_folder_prep_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = WorkspaceId]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = LakehouseId]}[Data],
  Navigation_3 = Navigation_2{[Id = DESTINATION_SCHEMA, ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "project_folder_prep", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared design_users_prep_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = WorkspaceId]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = LakehouseId]}[Data],
  Navigation_3 = Navigation_2{[Id = DESTINATION_SCHEMA, ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "users_prep", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared design_scenario_runs_prep_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = WorkspaceId]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = LakehouseId]}[Data],
  Navigation_3 = Navigation_2{[Id = DESTINATION_SCHEMA, ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "scenario_runs_prep", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared design_jobs_prep_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = WorkspaceId]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = LakehouseId]}[Data],
  Navigation_3 = Navigation_2{[Id = DESTINATION_SCHEMA, ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "jobs_prep", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared design_audit_logs_prep_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = WorkspaceId]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = LakehouseId]}[Data],
  Navigation_3 = Navigation_2{[Id = DESTINATION_SCHEMA, ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "audit_logs_prep", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
[DataDestinations = {[Definition = [Kind = "Reference", QueryName = "cluster_tasks_prep_DataDestination", IsNewTarget = true], Settings = [Kind = "Automatic", TypeSettings = [Kind = "Table"]]]}]
shared cluster_tasks_prep = let
  Source = loadIncrementalStarburstTable("cluster_tasks_prep", "timestamp_dt")
in
  Source;
shared cluster_tasks_prep_DataDestination = let
  Pattern = Lakehouse.Contents([CreateNavigationProperties = false, EnableFolding = false, HierarchicalNavigation = true, EnableVorder = true, OutputMetadataRefresh = true]),
  Navigation_1 = Pattern{[workspaceId = WorkspaceId]}[Data],
  Navigation_2 = Navigation_1{[lakehouseId = LakehouseId]}[Data],
  Navigation_3 = Navigation_2{[Id = DESTINATION_SCHEMA, ItemKind = "Schema"]}[Data],
  TableNavigation = Navigation_3{[Id = "cluster_tasks_prep", ItemKind = "Table"]}?[Data]?
in
  TableNavigation;
shared loadIncrementalStarburstTable = let
    loadIncrementalStarburstTable = (sourceTableName as text, snapshotDateColumnName as text) as table =>
        let
            starburstSource = StarburstPresto.Contents(SOURCE_HOST, Number.FromText(SOURCE_PORT), null),
            selectedDatabaseNavigation = try starburstSource{[Name = SOURCE_DATABASE, Kind = "Database"]}[Data],
            selectedDatabase =
                if selectedDatabaseNavigation[HasError] then
                    error
                        Error.Record(
                            "SourceDatabaseNotFound",
                            "La base de données source Starburst est introuvable.",
                            [
                                sourceHost = SOURCE_HOST,
                                sourcePort = SOURCE_PORT,
                                sourceDatabase = SOURCE_DATABASE
                            ]
                        )
                else
                    selectedDatabaseNavigation[Value],
            selectedSchemaNavigation = try selectedDatabase{[Name = SOURCE_SCHEMA, Kind = "Schema"]}[Data],
            selectedSchema =
                if selectedSchemaNavigation[HasError] then
                    error
                        Error.Record(
                            "SourceSchemaNotFound",
                            "Le schéma source Starburst est introuvable.",
                            [
                                sourceDatabase = SOURCE_DATABASE,
                                sourceSchema = SOURCE_SCHEMA
                            ]
                        )
                else
                    selectedSchemaNavigation[Value],
            resolvedSourceTableName = SOURCE_INSTANCE_PREFIX_TABLE & "_" & sourceTableName,
            sourceTableNavigation = try selectedSchema{[Name = resolvedSourceTableName, Kind = "Table"]}[Data],
            sourceTable =
                if sourceTableNavigation[HasError] then
                    error
                        Error.Record(
                            "SourceTableNotFound",
                            "La table source Starburst est introuvable.",
                            [
                                sourceDatabase = SOURCE_DATABASE,
                                sourceSchema = SOURCE_SCHEMA,
                                logicalTableName = sourceTableName,
                                expectedSourceTableName = resolvedSourceTableName,
                                sourceInstancePrefixTable = SOURCE_INSTANCE_PREFIX_TABLE
                            ]
                        )
                else
                    sourceTableNavigation[Value],
            validatedSourceTable =
                if not List.Contains(Table.ColumnNames(sourceTable), snapshotDateColumnName) then
                    error
                        Error.Record(
                            "MissingSourceSnapshotDateColumn",
                            "La colonne snapshot demandée est introuvable dans la table source Starburst.",
                            [
                                sourceDatabase = SOURCE_DATABASE,
                                sourceSchema = SOURCE_SCHEMA,
                                sourceTableName = resolvedSourceTableName,
                                snapshotDateColumnName = snapshotDateColumnName,
                                availableColumns = Table.ColumnNames(sourceTable)
                            ]
                        )
                else
                    sourceTable,
            currentParisDateTime = DateTime.From(getCurrentParisDateTime()),
            tableWithLoadedAtColumn = Table.AddColumn(
                validatedSourceTable, "loaded_at", each currentParisDateTime, type datetime
            ),
            tableWithAuditColumns = Table.AddColumn(
                tableWithLoadedAtColumn, "updated_at", each currentParisDateTime, type datetime
            ),
            // latestSnapshotDate = getLatestSnapshotDateFromLakehouseTable(
            //     DESTINATION_SCHEMA, sourceTableName, snapshotDateColumnName
            // ),
            latestSnapshotDate = null,
            loadedIncrementalTable =
                if latestSnapshotDate = null then
                    tableWithAuditColumns
                else
                    Table.SelectRows(
                        tableWithAuditColumns, each Record.Field(_, snapshotDateColumnName) > latestSnapshotDate
                    )
        in
            loadedIncrementalTable
in
    loadIncrementalStarburstTable;
