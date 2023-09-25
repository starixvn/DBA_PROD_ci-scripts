USE [master]
GO

if db_id('MonDB') is not null
	ALTER DATABASE MonDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
	DROP DATABASE [MonDB]
GO

CREATE DATABASE [MonDB]
GO

use MonDB
go
create procedure [dbo].[vnDBA_autoCS_restoreDB]
@restoreDBName	NVARCHAR(128)	= null,
@restorePath	NVARCHAR(500)	= null,
@fullBKPath		NVARCHAR(500)	= null,
@diffBKPath		NVARCHAR(500)	= '',
@freeDisk		FLOAT			= 1000000000000
as
begin
	declare @dbSize float, @sql  varchar(max)
	--2.2 check disk space/ db space
	IF	OBJECT_ID('tempdb..#data_files') IS NOT NULL DROP TABLE	#data_files
	CREATE TABLE	#data_files (
						LogicalName				NVARCHAR(1000)
					,	PhysicalName			NVARCHAR(1000)
					,	Type					VARCHAR(10)
					,	FileGroupName			VARCHAR(1000)
					,	Size					VARCHAR(100)
					,	MaxSize					VARCHAR(100)
					,	FileId					VARCHAR(10)
					,	CreateLSN				VARCHAR(1000)
					,	DropLSN					VARCHAR(1000)
					,	UniqueId				VARCHAR(1000)
					,	ReadOnlyLSN				VARCHAR(100)
					,	ReadWriteLSN			VARCHAR(100)
					,	BackupSizeInBytes		VARCHAR(100)
					,	SourceBlockSize			VARCHAR(100)
					,	FileGroupId				VARCHAR(100)
					,	LogGroupGUID			VARCHAR(100)
					,	DifferentialBaseLSN		VARCHAR(1000)
					,	DifferentialBaseGUID	VARCHAR(1000)
					,	IsReadOnly				VARCHAR(100)
					,	IsPresent				VARCHAR(10)
					,	TDEThumbprint			VARCHAR(10)
					,   SnapshotUrl				VARCHAR(1000)
					);

	--get fullBK and diffBK full path + name, priority: copied file -> parameter file
	if @fullBKPath = ''
	begin
		RAISERROR ('full backup file is not found', 16, 1)
		RETURN
	end

	--get database size
	INSERT INTO	#data_files
			(LogicalName, PhysicalName, Type, FileGroupName, Size, MaxSize, FileId, CreateLSN, DropLSN, UniqueId, ReadOnlyLSN, ReadWriteLSN, BackupSizeInBytes, SourceBlockSize, FileGroupId, LogGroupGUID, DifferentialBaseLSN, DifferentialBaseGUID, IsReadOnly, IsPresent, TDEThumbprint,SnapshotUrl)
	EXECUTE	('RESTORE FILELISTONLY FROM DISK = ''' + @fullBKPath + ''';');
	
	update #data_files
	set PhysicalName = replace(PhysicalName,'/','\')


	select * from #data_files	
	--get restored DB size if had DB already
	declare @currentDBSize bigint = 0
	SELECT @currentDBSize = isnull(CAST(SUM(size) * 8. * 1024 AS bigint),0)
	FROM sys.master_files WITH(NOWAIT)
	WHERE database_id = DB_ID(@restoreDBName) and physical_name like '%'+ @restorePath +'%'
	GROUP BY database_id
	--compare dbSize and freeSpace
	if @dbSize * 1.2 > @freeDisk + @currentDBSize
	begin
		print('need more space for restoring')
		return
	end

	--2.3 restore


	--restore full BK with norecovery option
	if object_id('tempdb..#RSresult') is not null
		drop table #RSresult
	create table #RSresult (value int)
	if db_id(@restoreDBName) is not null
	begin
		begin try
			select @sql =''
			select @sql = 'USE master;
			ALTER DATABASE ' + @restoreDBName + ' SET SINGLE_USER WITH ROLLBACK IMMEDIATE;'
			exec(@sql)
			print 'seted single user mode'
		end try
		begin catch
			RAISERROR ('Can not set single user mode for wanted restoring DB', 16, 1)
			RETURN
		end catch
	end
	select @sql =''
	select @sql = '
	begin try
	RESTORE DATABASE ' + @restoreDBName + ' FROM DISK = N''' + @fullBKPath + ''' 
	WITH FILE = 1,norecovery,' 
	select @sql = @sql + '
	MOVE N''' + LogicalName + ''' TO N''' + REPLACE(PhysicalName, SUBSTRING(PhysicalName,1,LEN(PhysicalName)-CHARINDEX('\',REVERSE(PhysicalName))+1), @restorePath) + ''','
	from #data_files

	select @sql = @sql + '
	NOUNLOAD, STATS = 10;
	print ''restored full BK success''
	end try
	begin catch
		print ''restored full BK error''
		insert into #RSresult values(0)
	end catch
	'
	print @sql
	--exec sp_executesql @sql, @Params = N'@RSresult INT OUTPUT', @RSresult = @RSresult OUTPUT
	--insert into @RSresult exec (@sql)
	exec (@sql)
	--select* from #RSresult
	if not exists(select * from #RSresult)
	begin
		--check diff BK file and restore if having, restore with recovery if not 
		if isnull(@diffBKPath,'') = ''
		begin
			select @sql = '
			RESTORE DATABASE ' + @restoreDBName + ' WITH recovery;'
		end
		else
		begin
			--print 'diffBK file path: ' + @diffBKPath
			select @sql =''
			select @sql ='
			begin try
			RESTORE DATABASE ' + @restoreDBName + ' FROM DISK = N''' + @diffBKPath + '''
			WITH FILE = 1,RECOVERY, NOUNLOAD, STATS = 10;
			print ''restored diff BK success''
			end try
			begin catch
				print ''restored diff BK error''
				insert into #RSresult values(0)
			end catch;
					'
	
		end
		--print len(@sql)
		--print @sql
			
		--exec sp_executesql @sql, @Params = N'@RSresult INT OUTPUT', @RSresult = @RSresult OUTPUT
		exec (@sql)

	end

if (db_id(@restoreDBName) is not null) and (not exists(select * from #RSresult))
begin
	begin try
		select @sql =''
		select @sql = 'USE master;
		ALTER DATABASE ' + @restoreDBName + ' SET MULTI_USER;'
		exec(@sql)
		print 'seted multi user mode'
	end try
	begin catch
		RAISERROR ('Can not set multi user mode for wanted restoring DB', 16, 1)
		RETURN
	end catch
end
		
--mapping user
if not exists(select * from #RSresult)
begin
	select @sql =''
	select @sql = 'USE ' + @restoreDBName + '
					declare @sql nvarchar(max) = ''''

					select @sql = @sql + ''
					EXEC sp_change_users_login ''''update_one'''','' + QUOTENAME(u.name) + '','' + QUOTENAME(sp.name)
					from sys.server_principals sp
						inner join ' + @restoreDBName + '.sys.sysusers u on sp.name =u.name
					where sp.type not in (''G'', ''R'')
						and issqlrole = 0
						and hasdbaccess = 1
						and uid > 1 

					print @sql

					exec sp_executesql @sql'


	--exec sp_executesql @sql
	exec (@sql)
end
	--/2.3 restore
end