使用前必读
===========

此脚本可用于扫描redis zombie key,large key及没有设置过期时间的key，通过type可选择.
<br/> 
<br/> 
### 使用需求:

#### Python requirements: 
    argparse==1.4.0
    progressbar==2.3
    redis==2.10.5
<br/> 
#### Redis Client:
    redis-cli >= 2.8 in /usr/bin/
<br/> 

使用介绍：
-----------
  
  scan_rediskey.py [-h] -T ['zombiekey','largekey','nottl'] -H IP -P Port [-D Days] [-S KeySize] [-M ModeType]\<br>
  -T  操作类型   可选'zombiekey','largekey','nottl'.\<br>
  -H  Host      支持域名，例如aws elasticache endpoint.\<br>
  -P  端口      校验使用6开头4位端口.\<br>
  -D  空闲时间  zombie key选项,单位:天,默认20天.\<br>
  -S  key大小   large key选项,单位:KB,默认1024KB.\<br>
  -M  连接类型  large key选项,可选local,remote,默认local.\<br>
  
  例如:
  扫描30天僵尸key:
    python scan_rediskey.py -T zombiekey -H 127.0.0.1 -P 6379 -D 30
  扫描large key(大于512KB):
    python scan_rediskey.py -T largekey -H 127.0.0.1 -P 6379 -S 512 [-M ModeType]
  扫描没有设置过期时间的key:
    python scan_rediskey.py -T nottl -H 127.0.0.1 -P 6379



参考：
-----------
  https://github.com/sripathikrishnan/redis-rdb-tools
