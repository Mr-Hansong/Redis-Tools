使用前必读
===========
此脚本可用于扫描redis zombie key，large key及没有设置过期时间的key，通过type可选择.
<br/> 
<br/> 
<br/> 

## 使用需求:
#### Python requirements : 
    argparse==1.4.0
    progressbar==2.3
    redis==2.10.5
#### Redis requirements(仅当remote扫描largekey) :
    redis-cli >= 2.8 in /usr/bin/
<br/> 

## 使用介绍：
    scan_rediskey.py [-h] -T ['zombiekey','largekey','nottl'] -H IP -P Port [-D Days] [-S KeySize] [-M ModeType]
    
    help :
    -T：操作类型，可选zombiekey，largekey，nottl.
    -H：Host，支持域名，例如：aws elasticache endpoint.
    -P：端口，校验使用6开头4位端口.
    -D：空闲时间，zombie key选项，单位：天，默认：20天.
    -S：key大小，large key选项，单位：KB，默认：1024KB.
    -M：连接类型，large key选项，可选local，remote，默认：local.
#### 例如:
##### 扫描30天僵尸key:
```
    python scan_rediskey.py -T zombiekey -H 127.0.0.1 -P 6379 -D 30
```
##### 扫描large key(大于512KB):
```
    python scan_rediskey.py -T largekey -H 127.0.0.1 -P 6379 -S 512 [-M ModeType]
```
##### 扫描没有设置过期时间的key:
```
    python scan_rediskey.py -T nottl -H 127.0.0.1 -P 6379
```
<br/> 

## 建议
如果需要扫描多种key，建议首先扫描zombie key。因为当扫描nottl key相当于对redis中所有key进行了一次命令操作，会导致扫描zombie key的结果为空。
<br/> 
<br/> 
<br/> 

## 结果
脚本执行后，会在脚本目录生成格式以操作类型开头的txt文件。如果扫描largekey会在脚本目录生成RDB开头的txt临时文件，如果选择remote的方式扫描，则会在脚本目录多生成一个.rdb文件。

    例如：
    zombiekey_127.0.0.1_6379.txt
    largekey_127.0.0.1_6379.txt
    nottl_127.0.0.1_6379.txt
<br/> 

## 参考：
  https://github.com/sripathikrishnan/redis-rdb-tools
