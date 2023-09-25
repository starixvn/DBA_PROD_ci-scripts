# Ci Scripts

1. build ENV
    1.1. preparation
         . DB config directory
         . DB backup directory (in case using restore DB)
         . DB schema directory (in case using schema DB)
         . 
         . mondb directory
         . cf1 (feature config) file, cf2 (running config) file
         . SSB directory (later)
         . directory map: /Ci
                            |_backup
                            |    |_allbackup
                            |    |_config
                            |    |  |_configfile (all config from dbbackup)
                            |    |_schema
                            |       |_yyyymmdd (all SB schema from dbdwcss)
                            |    |_mondb
                            |       |_initmondb.sql
                            |       |_linkedserver.sql
                            |    |_ssb (later)
                            |_pythyon
                            |_feature
                            |_log
    1.2. building process
2. run ENV

3. exec Packages
