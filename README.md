# kbjson-tool 用户手册 #

## 部署说明 ##

解压代码，找到名为kbt的python模块包，复制到用户代码所在文件夹中即可使用。

目录结构举例：  
/WORK_DIR/kbt  
/WORK_DIR/try.py

```python
# File: try.py
import kbt
o = kbt.Entity()
...
```

## 使用介绍 ##

_注：详细接口可参考[KB-JSON 2.0 开发工具库接口规范][接口规范]_

[接口规范]: http://db-wdm-site-off10.db01.baidu.com/kongliang/kgc/blob/master/python/kbt/Design.md

kbt模块包中定义了Entity、Spo等类，对应实体、三元组等概念。

可从KB-JSON文本反序列化得到实体对象（用静态方法Entity.fromKbjson），或者直接实例化一个空实体。

在实体对象上，可创建、获取和修改其中的三元组（用createSpo创建，get或triples获取，add或remove增删），也可直接获取特定属性的值（用getv）。

在三元组对象上，可对属性值和元数据进行快捷读写（用v、r、m、values等），也可针对复杂的值进行更多操作（用items等获取KValue对象，用append、remove增删三元组中的值）。

KValue类是对三元组中的值的抽象，是可嵌套键值对存储（get、set、remove）。

**实体概念模型**  
（4层）Entity => ATTR DICT(+META) => SPO SET => KVALUE LIST(+META)

**API使用模型**  
（3层）Entity => SPO SET => KVALUE LIST

## 场景示例 ##

### 1.从KB-JSON文本解析实体，对实体ID和实体名进行操作后，再序列化为KB-JSON
```python
import kbt
# KB-JSON样例
s = """{
    "@id": "http://userbase/k/liudehua",
    "@type": [          
        "Person"
    ], 
    "name": [
        {
            "objects": [
                {
                    "@type": "bkgss:Text",      
                    "value": "刘德华"
                }
            ]
        }
    ]
}"""
o = kbt.Entity.fromKbjson(s)                # 解析实体
print o.id()                                # => http://userbase/k/liudehua
print o.getv("name")[0]                     # => 刘德华

spo = o.get("name")[0]                      # 获取要修改的三元组
spo.v(u"华仔")
print spo.v()                               # => 华仔

o.toString(indent=4)                        # 序列化，indent缺省时输出为一行
```
序列化结果
```json
{
    "@id": "http://userbase/k/liudehua", 
    "name": [
        {
            "objects": [
                {
                    "@type": "bkgss:Text", 
                    "value": "华仔"
                }
            ]
        }
    ], 
    "@type": [
        "Person"
    ]
}
```

### 2.向实体中添加新的三元组
```python
import kbt
o = kbt.Entity()
spo = o.createSpo("name", "baidu")          # 新建三元组
o.add(spo)                                  # 添加到实体
spo = o.createSpo("age", "15", kbt.Entity.META_STATUS_DEFAULT, kbt.Entity.META_FROM_TYPE_PUSH)
o.add(spo)
o.toString(indent=4)
```
输出结果
```json
{
    "age": [
        {
            "objects": [
                {
                    "@type": "bkgss:Text", 
                    "value": "15"
                }
            ], 
            "meta": [
                {
                    "fromType": "PUSH", 
                    "timeLastMod": "1431609314", 
                    "stat": "DEFAULT", 
                    "@type": "MetaSPO", 
                    "timeGenerate": "1431609314"
                }
            ]
        }
    ], 
    "@id": "42053711fa3b11e4a6cf1458d0b88725", 
    "name": [
        {
            "objects": [
                {
                    "@type": "bkgss:Text", 
                    "value": "baidu"
                }
            ], 
            "meta": [
                {
                    "timeLastMod": "1431609314", 
                    "@type": "MetaSPO", 
                    "timeGenerate": "1431609314"
                }
            ]
        }
    ]
}
```
从上面输出可以看到，createSpo时，系统自动加上了timeGenerate和timeLastMod两个元数据。

### 3.读写三元组上的meta信息 ###
```python
import kbt
s = """{
    "@context": "http://kg.baidu.com/sample_context.jsonld", 
    "@id": "http://userbase.kgs.baidu.com/somename/liudehua", 
    "@type": [          
        "Person", 
        "Singer"
    ], 
    "award": [
        {
            "objects": [
                {
                    "@type": "Song",      
                    "value": "冰雨"
                }
            ], 
            "meta": [
                {
                    "@type": "MetaSPO", 
                    "timeGenerate": "1428996364", 
                    "timeLastMod": "1428996364", 
                    "fromType": "PUSH", 
                    "fromUrl": "http://baike.baidu.com/view/1758.htm", 
                    "lang": "zh-cn", 
                    "viewId": "Singer.http://baike.baidu.com/liudehua"
                },
                {
                    "@type": "MetaCustom", 
                    "resolution": "0.1"
                }
            ], 
            "subjectType": ["Singer"]
        }
    ]
}"""
o = kbt.Entity.fromKbjson(s)                # 解析实体
spo = o.get("award")[0]                     # 获取三元组

# MetaSPO放置系统元数据，使用m方法快速访问
print spo.m("lang")                         # => zh-cn
print spo.m(kbt.Entity.META_FROM_TYPE)      # => PUSH

spo.m("lang", "en-us")                      # 修改meta值
print spo.m("lang")                         # => en-us

# 其他类型的meta，通过meta方法访问
meta = spo.meta("MetaCustom")[0]
print meta.get("resolution")                # => 0.1

newMeta = kbt.Meta("MetaCustom2")			# 新建meta，使用Entity.createMeta方法，需指定Meta类型
newMeta.set("meta_key", "xxx")
spo.appendMeta(newMeta)                     # 添加meta到三元组
print spo.meta("MetaCustom2")[0].items()    # => [('@type', 'MetaCustom2'), ('meta_key', 'xxx')]
```

### 4.解析KB-JSON 1.0
```python
import kbt
s = """{
        "ID": "66cfc7acc6a911e38974047d7b067fc6",
        "AVP_LIST": [
            {
                "ATTRIBUTE": "name",
                "VALUE": "刘德华",
                "VALUE_TYPE": "LITERAL",
                "FROM_TYPE": "PUSH",
                "VALUE_LANG": "zh-cn",
                "FROM_URL": "http://baike.baidu.com/view/1758.htm"
            },
            {
                "ATTRIBUTE": "type",
                "VALUE": "Person",
                "VALUE_TYPE": "LITERAL",
                "FROM_TYPE": "PUSH",
                "VALUE_LANG": "zh-cn",
                "FROM_URL": "http://baike.baidu.com/view/1758.htm"
            },
            {
                "ATTRIBUTE": "weight",
                "VALUE": {"value":"68", "unitCode":"KG"},
                "VALUE_TYPE": "SVALUE",
                "FROM_TYPE": "PUSH",
                "VALUE_LANG": "zh-cn",
                "FROM_URL": "http://baike.baidu.com/view/1758.htm"
            },
            {
                "ATTRIBUTE": "memberOf",
                "VALUE": "东亚唱片",
                "REFER": "c7ded732c6a811e38974047d7b067fc6",
                "VALUE_TYPE":"LITERAL",
                "FROM_TYPE": "PUSH",
                "VALUE_LANG": "zh-cn",
                "FROM_URL": "http://baike.baidu.com/view/1758.htm"
            }
        ]
    }"""
o = kbt.Entity.fromKbjson1(s)               # 解析KB-JSON 1.0
s2 = o.toString(indent=4)                   # 转为KB-JSON 2.0
```
输出结果
```json
{
    "memberOf": [
        {
            "objects": [
                {
                    "@type": "bkgss:Text", 
                    "value": "东亚唱片", 
                    "refer": "c7ded732c6a811e38974047d7b067fc6"
                }
            ], 
            "meta": [
                {
                    "fromType": "PUSH", 
                    "lang": "zh-cn", 
                    "fromUrl": "http://baike.baidu.com/view/1758.htm", 
                    "@type": "MetaSPO"
                }
            ]
        }
    ], 
    "@id": "66cfc7acc6a911e38974047d7b067fc6", 
    "name": [
        {
            "objects": [
                {
                    "@type": "bkgss:Text", 
                    "value": "刘德华"
                }
            ], 
            "meta": [
                {
                    "fromType": "PUSH", 
                    "lang": "zh-cn", 
                    "fromUrl": "http://baike.baidu.com/view/1758.htm", 
                    "@type": "MetaSPO"
                }
            ]
        }
    ], 
    "weight": [
        {
            "objects": [
                {
                    "unitCode": "KG", 
                    "@type": "StructuredValue", 
                    "value": "68"
                }
            ], 
            "meta": [
                {
                    "fromType": "PUSH", 
                    "lang": "zh-cn", 
                    "fromUrl": "http://baike.baidu.com/view/1758.htm", 
                    "@type": "MetaSPO"
                }
            ]
        }
    ], 
    "@type": [
        "Person"
    ]
}
```

### 5. 各种方式查找属性值，修改和删除属性值 ###

```python
import kbt
s = """{
        "@context": "http://kg.baidu.com/sample_context.jsonld", 
        "@id": "http://userbase.kgs.baidu.com/somename/liudehua", 
        "@type": [          
            "Person", 
            "Singer", 
            "Actor"
        ],         
        "name": [
            {
                "objects": [
                    {
                        "@type": "bkgss:Text",      
                        "value": "刘德华"
                    }
                ]
            }
        ], 
        "memberOf": [
            {
                "objects": [
                    {
                        "@type": "bkgss:Text", 
                        "value": "东亚唱片", 
                        "refer": "c7ded732c6a811e38974047d7b067fc6"
                    }
                ], 
                "meta": [
                    {
                        "fromType": "PUSH", 
                        "lang": "zh-cn", 
                        "fromUrl": "http://baike.baidu.com/view/1758.htm", 
                        "@type": "MetaSPO"
                    }
                ], 
                "subjectType": ["Singer"]
            }
        ], 
        "award": [
            {
                "objects": [
                    {
                        "@type": "Song",      
                        "value": "冰雨"
                    },
                    {
                        "@type": "Song",      
                        "value": "笨小孩"
                    }
                ], 
                "meta": [
                    {
                        "@type": "MetaSPO", 
                        "timeGenerate": "1428996364", 
                        "timeLastMod": "1428996364", 
                        "fromType": "PUSH", 
                        "fromUrl": "http://baike.baidu.com/view/1758.htm", 
                        "lang": "zh-cn", 
                        "viewId": "Singer.http://baike.baidu.com/liudehua"
                    }
                ], 
                "subjectType": ["Singer"]
            }
        ]
    }"""
o = kbt.Entity.fromKbjson(s)                # 解析实体

# 直接访问属性中的简单值
# Entity => value
print o.getv("award")                       # => [u"冰雨", u"笨小孩"]
print o.getv("memberOf")                    # => [u"东亚唱片"]

# 通过三元组对象访问简单值、REFER等
# Entity => Spo => value
spo = o.get("memberOf")[0]
print spo.v(), spo.r()                      # => 东亚唱片 c7ded732c6a811e38974047d7b067fc6
print spo.p()                               # => memberOf
print spo.values()[0]                       # => 东亚唱片

# 通过三元组获取KValue类型的值对象后访问
# Entity => Spo => KValue => value
spo = o.get("memberOf")[0]
kv = spo.o()                                # spo.o() == spo.items()[0]
print kv.get("value"), kv.get("refer")      # => 东亚唱片 c7ded732c6a811e38974047d7b067fc6
print kv.type()                             # => bkgss:Text

# 从实体获取KValue后访问
# Entity => KValue => value
kv = o.geto("memberOf")[0]
print kv.get("value")                       # => 东亚唱片


# 按属性名分组遍历三元组
for name, spos in o.items():
    print "%s spo count: %s" % (name, len(spos))            # => memberOf spo count: 1
                                                            # => name spo count: 1
                                                            # => award spo count: 1
# 打印所有属性名
print " ".join(o.keys())                                    # => memberOf name award

# 遍历所有属性上的所有值
for spo in o.triples():
    for kv in spo.items():
        print "%s = %s" % (spo.p(), kv.get("value"))        # => memberOf = 东亚唱片
                                                            # => name = 刘德华
                                                            # => award = 冰雨
                                                            # => award = 笨小孩
# 修改属性值，通过Spo和KValue对象进行
spo = o.get("name")[0]
spo.v(u"华仔")
print o.getv("name")[0]                     # => 华仔

kv = o.get("award")[0].items()[1]
kv.set("value", u"天意")
print o.getv("award")                       # => [u"冰雨", u"天意"]

# 删除属性值，通过Spo对象进行
spo = o.get("award")[0]
kv = spo.items()[1]
print kv.get("value")                       # => 天意
spo.remove(kv)                              # 从三元组中删除一个值
print o.getv("award")                       # => [u"冰雨"]

spo = o.get("memberOf")[0]
o.remove(spo)                               # 从实体中删除一个三元组
print o.get("memberOf")                     # => []
```

_注：实体的get、geto、getv、triples、items方法中，都能使用可选的filter参数，对三元组进行过滤，详见[KB-JSON 2.0 开发工具库接口规范][接口规范]。_


## KB-JSON 1.0升级说明

工具库通过Entity.fromKbjson1方法，支持从KB-JSON 1.0（以下简称V1）升级。

### V1格式说明 ###
V1是简单的两层结构，顶层只有实体ID和AVP_LIST两个字段，每一个AVP对应一个三元组。

AVP中的ATTRIBUTE、VALUE和REFER字段定义了属性名和属性值，其他字段都是元数据。

VALUE_TYPE字段只能取值LITERAL和SVALUE，前者代表三元组值为文本类型，后者代表三元组值为StructuredValue类型。

```json
{
	(MUST) “ID”: ${ID},
	(MUST) “AVP_LIST”: [
		{
			(MUST) “ATTRIBUTE”: ${ATTRIBUTE},
			(SPECIAL) “VALUE”: ${VALUE},
			(SPECIAL) “REFER”: ${REFER},
			(MUST) “VALUE_TYPE”: ${VALUE_TYPE},
			(MUST) “FROM_TYPE”: ${FROM_TYPE},
			(MUST) “VALUE_LANG”: ${VALUE_LANG},
			(OPTIONAL) “CONFIDENCE”: ${CONFIDENCE},
			(OPTIONAL) “FROM_URL”: ${FROM_URL},
			(OPTIONAL) “TIME_GENERATE”: ${TIME_GENERATE},
			(OPTIONAL) “TIME_EXPIRE”: ${TIME_EXPIRE},
			(OPTIONAL) “INFO”: ${INFO}
			},
		……
	]
}
```


### 升级方式 ###

1. 实体ID直接映射

2. 每个AVP转换为一个Spo对象

3. ATTRIBUTE、VALUE_TYPE、VALUE、REFER转换为Spo的name、type、value、refer等字段

4. FROM_URL、CONFIDENCE、FROM_TYPE、VALUE_LANG、TIME_GENERATE、TIME_EXPIRE转换为Spo上Meta字段，类型为MetaSPO

5. INFO以及其他扩展字段，也转换为Spo上Meta，类型为MetaAVP

6. 所有SVALUE值和INFO字段值，转换后为StructuredValue类型

### 转换细节说明 ###

**AVP值类型约束**

AVP中除VALUE和INFO字段之外的系统字段，值都必须为字符串类型。

VALUE、INFO和其他扩展字段值，可以是SVALUE（Json Object）类型，但该值的内部字段值应为字符串类型。

**实体ID**

为保持refer字段的有效性，不对V1中的实体ID进行任何处理，即允许不是URL的实体ID。

**实体类型**

V1中的实体类型，是属性名为type的三元组。这些三元组中的类型值会被提取，其他元信息将丢弃。

**三元组中的类型信息**

由于V1中未定义SVALUE和元数据值的具体类型，因此：

- 在SVALUE转换后的StructuredValue类型值中，各字段并未在Schema上定义

- INFO和其他扩展的元数据，转换后统一放到了类型为MetaAVP的meta中，保持字段名不变

**FROM_TYPE值**

转换关系如下：
```python
# KB-JSON 1.0的FROM_TYPE中没有CLEANSE和FEED
PUSH                        =>      PUSH   
STRUCTURE_EXTRACT           =>      EXTRACT  
SEMISTRUCTURE_EXTRACT       =>      EXTRACT
UNSTRUCTURE_EXTRACT         =>      EXTRACT
INFERENCE                   =>      INFERENCE
MINING                      =>      MINING
MANUAL_INTERVENTION         =>      INTERVENE
```

**已知扩展字段**

- VIEW_ID转换为MetaSPO的viewId

### 错误处理 ###

当数据格式不符合KB-JSON 1.0规范时，通常会打印警告信息，然后跳过特定字段、三元组的转换。

## Parser插件开发 ##

开发仅需三步：

1. 新建文件xxx.py，用python实现一个从text到Entity对象的转换函数parse，测试效果

2. 在xxx.py中新建XxxParser类（派生自kbt.Parser，参考kbt/parsers/v1.py中的KbjsonV1Parser类），将1中的parse函数改写为parse方法

3. 为解析器命名，即重载XxxParser类的name方法，返回一个英文名（比如Kbjson1.0解析器的名称为V1）。上传xxx.py到kbt/parsers目录(或E-mail给kongliang@baidu.com)完成插件开发

使用：

```python
import kbt
o = kbt.Entity.fromParser(text, parserName)
```
