#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
# *Description
#
# *The scripts used to scan redis zombie key / large key / NoTTL key.
# *After the analysis can generate a txt file in current directory
# *named [OperType]_[Ip]_[Port].txt
# *Required :
# *   pip install redis argparse progressbar
#
#                                       2016.08.04 
'''

import os,sys,time,re,commands
import redis
import argparse
from progressbar import *


# ===*=== Format The Input Variables ===*===
UsageInfo = "\n  %(prog)s [-h] -T ['zombiekey','largekey','nottl'] -H IP -P Port [-D Days] [-S KeySize] [-M ModeType]"
DescriptionInfo = "%(prog)s Required install redis,argparse,progressbar python modules. If you choose remote-largerkey, also need install redis client and put redis-cli in /usr/bin/"
parser = argparse.ArgumentParser( usage = UsageInfo, description = DescriptionInfo )
parser.add_argument("-T","--type",type=str,required=True,metavar="Type",choices=['zombiekey','largekey','nottl'],help="Enter The Type Of Operation, zombiekey/largekey/nottl.",dest="OperType")
parser.add_argument("-H","--host",type=str,required=True,metavar="IP",help="Input Target Redis Host,it can be the domain name format, for example the aws endpoint.",dest="RedisHost")
parser.add_argument("-P","--port",type=int,required=True,metavar="Port",help="Input Target Redis Port, Must Be 4 Digits, And The First One Is 6.",dest="RedisPost")
parser.add_argument("-D","--obsday",type=int,default=20,metavar="Days",help="Enter The Number Of Days Overdue,The Key Parameter For Determining Whether A Zombie Key. Default 20 days.",dest="Obsolete_Days")
parser.add_argument("-S","--size",type=float,default=1024,metavar="KeySize",help="IF The Key Bytes Than This Size , It Is Determined Large Key, Unit KB. Default 1024KB.",dest="LargeKeySize")
parser.add_argument("-M","--mode",type=str,default="local",metavar="Platform Type",choices=['local','remote'],help="Choice model, local or remote.",dest="ModeType")
args = parser.parse_args()


OperType = args.OperType
RedisHost = args.RedisHost
RedisPost = args.RedisPost
Obsolete_Days = args.Obsolete_Days
LargeKeySize = args.LargeKeySize
ModeType = args.ModeType



# ===*=== Definition UDF ===*===	 
# -*- Verify IP is valid -*-
def RegexIP() :
	RegexFormatIP = "^(2[0-4][0-9]|25[0-5]|1[0-9][0-9]|[1-9]?[0-9])(\.(2[0-4][0-9]|25[0-5]|1[0-9][0-9]|[1-9]?[0-9])){3}$"
	RegexRstIP = re.match( RegexFormatIP , RedisHost )
	if ( not RegexRstIP ) :
		print "[ ERROR ] Input Variable(IP) Format Error."
		sys.exit()


# -*- Verify Port is valid -*-
def RegexPort() :
	RegexFormatPort = "^6[0-9]{3}$"
	RegexRstPort = re.match( RegexFormatPort , str(RedisPost) )
	if ( not RegexRstPort ) :
		print "[ ERROR ] Input Variable(Port) Format Error."
		sys.exit()


# -*- Get Conversion time -*-
def GetRunTime( DiffSec ) :
	DiffSec = int( DiffSec )
	DiffMin = int( DiffSec / 60 )
	if ( DiffMin > 0 ) :
		DiffHour = int( DiffMin / 60 )
		if ( DiffHour > 0 ) :
			ModSec = DiffSec - ( DiffHour * 60 * 60 )
			ModMin = int(ModSec/60)
			ModSec = ModSec%60
			return str(DiffHour) + " Hours " + str(ModMin) + " Minutes " + str(ModSec) + " Seconds"
		else :
			ModSec = DiffSec - ( DiffMin * 60 )
			return str(DiffMin) + " Minutes " + str(ModSec) + " Seconds"
	else :
		return str(DiffSec) + " Seconds"


# -*- Execute OS Command -*-
def ExecCmd( Cmd , Type = 'normal' ) :
	ComStatus,ComRst = commands.getstatusoutput(Cmd)
	if ( ComStatus <> 0 ) :	
		if ( Type <> 'normal' ) : 
				print "[ ERROR ] Execution failed : " + Cmd
				print ComRst
				sys.exit()
		else :
				return ComStatus , ComRst
	elif ( ComStatus == 0 ) and ( Type == 'normal' ):
			return ComStatus , ComRst


# -*- Get OS Files Authorize -*-
def GetCmdExecAuth( Path ):
	CmdExecInfo = int(oct(os.stat( RDBToolPath ).st_mode)[-3]) % 2
	if ( CmdExecInfo == 1 ) :
		return 1
	else :
		return 0


# -*- Analysis Of Key Is Whether Dead Key -*-
def DebugObj( SplitScanList ) :
	global ZombKeyCnt
	ScanKey = SplitScanList
	
	for key in range(len(ScanKey)):
		DebugObjIdle = MyRedis.object( infotype = 'idletime' , key = ScanKey[key] )
		if ( DebugObjIdle > 60 * 60 * 24 * Obsolete_Days ):
			ZombKeyCnt += 1
			RstFile.write(dbnum + " : " + ScanKey[key] + " Obsoleted " + str(round(DebugObjIdle/86400.00,2)) + " Days\n")
			
# -*- Check RDB-Tools Availabled -*-
def CheckRDBTool () :
	if ( os.path.exists( RDBToolPath ) ) :
		if ( GetCmdExecAuth( RDBToolPath ) == 0 ) :
			Cmd = "chmod +x " + RDBToolPath
			ExecCmd( Cmd , Type = 'authorize' )
	else :
		print " [ INFO ] Instanll RDB Tools......"
		ExecCmd( 'pip install rdbtools' , Type = 'install' )
		ExecCmd( 'yum install -y git' , Type = 'install' )
		ExecCmd( 'git clone https://github.com/sripathikrishnan/redis-rdb-tools' , Type = 'install' )
		ExecCmd( 'cd redis-rdb-tools && sudo python setup.py install' , Type = 'install' )
	
	if ( GetCmdExecAuth( RDBToolPath ) == 1 ) :
		print " [ INFO ] RDB Tools Availabled"
	else :
		print "[ ERROR ] RDB Tools Not Availabled"
		sys.exit()



# ===*=== Main ===*===
RegexPort()
#RegexIP()	--- example aws endpoint
StartTime = time.time()
CurDir = os.getcwd() + "/" 
RstFileName = CurDir + OperType + "_" + RedisHost + "_" + str(RedisPost) + ".txt"
RstFile = open( RstFileName,'w' )
print "=" * 80


# -*- Get Redis Information -*-
DBList = list()
DBKeyCnt = dict()
TotleKeyCnt = 0
ScanLimit = 100
GetRedisDB = redis.Redis(host=RedisHost, port=RedisPost, db=0)
InfoMemory = GetRedisDB.info( section='memory' )
InfoUseMem = InfoMemory['used_memory_human']
InfoKeyspace = GetRedisDB.info( section='keyspace' )
for dbname in InfoKeyspace :
	DBList.append(dbname)
	DBKeyCnt[dbname] = InfoKeyspace[dbname]['keys']
	TotleKeyCnt = TotleKeyCnt + DBKeyCnt[dbname]
print "[ Initial ] " + RedisHost + ":" + str(RedisPost) + " Use " + InfoUseMem + " Memory, Have " + str(TotleKeyCnt) + " Keys"


# -*- Analysis zombiekey -*-
if ( OperType == 'zombiekey' ) : 

	# -*- Start ProgressBar -*-
	print "[ Initial ] Operation Type: zombiekey, Host: " + RedisHost + ":" + str(RedisPost) + ", Obsolete Days :" +  str(Obsolete_Days)
	widgets = ['keys %d : ' % TotleKeyCnt, Percentage(), ' ', Bar(marker=RotatingMarker('>-=')),' ', ETA(), ' ', FileTransferSpeed()]
	pbar = ProgressBar(widgets=widgets, maxval=TotleKeyCnt).start()
	
	TotleZombKeyCnt = 0
	
	for dbnum in DBList :
		ZombKeyCnt = 0
		ScanInof = 0
		ScanCnt = 0
		Num = dbnum.replace('db','')
		MyRedis = redis.Redis(host=RedisHost, port=RedisPost, db=Num)
		
		while True: 
			SplitScanRst = MyRedis.scan( cursor = ScanInof ,count = ScanLimit )
			ScanCnt += 1
			ScanInof = int(SplitScanRst[0])
			DebugObj( SplitScanRst[1] )
			
			# -*- Update ProgressBar -*-
			pbar.update( min( TotleKeyCnt, ScanCnt * ScanLimit ) )
			
			if ( ScanInof == 0 ) :
				break
			
		TotleZombKeyCnt = TotleZombKeyCnt + ZombKeyCnt
		
	pbar.finish()

	# *Running Information Output Of The Script
	print "[ Totle ] " + RedisHost + ":" + str(RedisPost) + " Found " + str(TotleZombKeyCnt) + " Zombie Key"
	

# -*- Analysis largekey -*-
elif ( OperType == 'largekey' ) :
	
	# -*- Set Global Variables And Availability CheckRDBTool -*-
	print "[ Initial ] Operation Type: largekey, Host: " + RedisHost + ":" + str(RedisPost) + ", Size " + str(LargeKeySize) + "KB, Mode: " + ModeType
	RDBToolPath = '/usr/bin/rdb'
	RDBFilename = 'RDB_' + RedisHost + '_' + str(RedisPost) + '.txt'
	CheckRDBTool()
	
	if ( ModeType == 'local' ) :
		# -*- Validate The Input Variables -*-
		if ( RedisHost <> '127.0.0.1' ) :
			print "[ ERROR ] Input Variable(IP) Format Error, IP Must Enter 127.0.0.1"
			sys.exit()
		
		# -*- Analyze LargeKey -*-
		# *Generated RDB File
		GetRedisDB = redis.Redis(host=RedisHost, port=RedisPost, db=0)
		RedisCfgDir = GetRedisDB.config_get( pattern='dir' )['dir'] + '/'
		RedisCfgDBFileName = GetRedisDB.config_get( pattern='dbfilename' )['dbfilename']
		RedisCfgSave = GetRedisDB.config_get( pattern='save' )['save']
		
		BgsaveStartTime = time.time()
		
		if ( not RedisCfgSave ) :
			print " [ INFO ] RDB file generated by Bgsave......"
			GetRedisDB.bgsave()
			
			while True: 
				time.sleep(3)
				Cmd = "ps -ef | grep redis-rdb-bgsave | grep -v sh | grep :" +  str(RedisPost)
				CmdStatus , CmdRst = ExecCmd( Cmd )
				if ( CmdStatus <> 0 ) :
					break
		BgsaveEndTime = time.time()
		RunTime = GetRunTime( BgsaveEndTime - BgsaveStartTime )
		print " [ INFO ] RDB file is generated, Running " + RunTime + ", Start Analysis......"
		
	elif ( ModeType == 'remote' ) :
		
		RedisCfgDir = CurDir
		RedisCfgDBFileName = RedisHost + "_" + str(RedisPost) + ".rdb"
		#CmdStatus,RedisPath = ExecCmd('which redis-cli')
		#Cmd = RedisPath + " -h " + RedisHost + " -p " + str(RedisPost) + " --rdb " + RedisCfgDir + RedisCfgDBFileName
		Cmd = "/usr/bin/redis-cli -h " + RedisHost + " -p " + str(RedisPost) + " --rdb " + RedisCfgDir + RedisCfgDBFileName
		
		print " [ INFO ] RDB file generated by Bgsave......"
		BgsaveStartTime = time.time()
		ExecCmd( Cmd , Type = 'bgsave' )
		BgsaveEndTime = time.time()
		RunTime = GetRunTime( BgsaveEndTime - BgsaveStartTime )
		print " [ INFO ] RDB file is generated, Running " + RunTime + ", Start Analysis......"
	
	# *Analyze RDB File
	Cmd = RDBToolPath + ' -c memory ' + RedisCfgDir + RedisCfgDBFileName + ' > ' + CurDir + RDBFilename
	ExecCmd( Cmd , Type = 'analyze' )
		
	LineSequ =  0
	LargeKeyCnt = 0
	RDBFile = open( CurDir + RDBFilename )
	
	Cmd = 'cat ' + CurDir + RDBFilename + '| wc -l'
	CmdStatus, LineCnt = ExecCmd( Cmd )
	if ( CmdStatus <> 0 ) :
		sys.exit()
	
	# -*- Start ProgressBar -*-
	widgets = ['FileLine %d : ' % int(LineCnt), Percentage(), ' ', Bar(marker=RotatingMarker('>-=')),' ', ETA(), ' ', FileTransferSpeed()]
	pbar = ProgressBar(widgets=widgets, maxval=int(LineCnt)).start()
	
	for line in RDBFile :
		LineSequ += 1
		pbar.update( min( TotleKeyCnt, LineSequ ) )
		KeySplit = line.split(',')
		if ( LineSequ > 1 ) : 
			try:
				if ( int(KeySplit[3]) > 1024 * LargeKeySize ) :
					LargeKeyCnt += 1
					RstFile.write( 'db' + str(KeySplit[0]) + ': ' + ' key(' + str(KeySplit[1]) + ') ' + KeySplit[2] + ' size:' + str(round(float(KeySplit[3])/1024,2)) + "KB\n")
			except(ValueError):
				print(KeySplit[3] + "\n");
				
	pbar.finish()
	print "[ Totle ] " + RedisHost + ":" + str(RedisPost) + " Found " + str(LargeKeyCnt) + " Large Key(gather " + str(LargeKeySize) + "KB) "
	RDBFile.close()	

# -*- Analysis NoTTL -*-
elif ( OperType == 'nottl' ) :

	# -*- Start ProgressBar -*-
	print "[ Initial ] Operation Type: nottl, Host: " + RedisHost + ":" + str(RedisPost)
	widgets = ['keys %d : ' % TotleKeyCnt, Percentage(), ' ', Bar(marker=RotatingMarker('>-=')),' ', ETA(), ' ', FileTransferSpeed()]
	pbar = ProgressBar(widgets=widgets, maxval=TotleKeyCnt).start()
	
	TotleNoTTL = 0
	
	for dbnum in DBList :
		NoTTLCnt = 0
		ScanInof = 0
		ScanCnt = 0
		Num = dbnum.replace('db','')
		MyRedis = redis.Redis(host=RedisHost, port=RedisPost, db=Num)
		
		while True: 
			SplitScanRst = MyRedis.scan( cursor = ScanInof ,count = ScanLimit )
			ScanCnt += 1
			ScanInof = int(SplitScanRst[0])
			ScanKey = SplitScanRst[1]
	
			for key in range(len(ScanKey)):
				KeyTTL = MyRedis.ttl( ScanKey[key] )
				if ( KeyTTL is None ):
					NoTTLCnt += 1
					RstFile.write(dbnum + " : " + ScanKey[key] + " Not Set TTL\n")
			
			# -*- Update ProgressBar -*-
			pbar.update( min( TotleKeyCnt, ScanCnt * ScanLimit ) )
			
			if ( ScanInof == 0 ) :
				break
			
		TotleNoTTL = TotleNoTTL + NoTTLCnt
		
	pbar.finish()

	# *Running Information Output Of The Script
	print "[ Totle ] " + RedisHost + ":" + str(RedisPost) + " Found " + str(TotleNoTTL) + " Key Not Set TTL"

print "[ Completed ] Result File : " + RstFileName
RstFile.close()
print "=" * 80
