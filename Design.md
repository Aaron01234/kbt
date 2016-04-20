# KB-JSON 2.0 开发工具库接口规范 #

## 背景 ##

知识建设和应用中：

- 实体三元组（SPO）及其元信息（META）的创建、读写操作很频繁

- 实体收录、清洗、融合等环节依赖和实体相关联的知识库Schema信息

- KB-JSON 2.0相比1.0灵活性和复杂度增加，更需要统一的开发工具库

注：阅读本文前，假定读者已熟悉[KB-JSON提交数据格式规范][KBJSON规范]

[KBJSON规范]: http://gitlab.baidu.com/kgschema/kgschema/blob/master/doc/kbjson_format_specification.md

## 名词解释 ##


**KB-JSON**  
百度公司使用的知识数据提交格式，本文档针对其2.0版本。

**Entity**  
实体对应实现类，可看作三元组的无序集合，并含有实体类型、上下文等信息。

**Spo**  
三元组对应实现类，可存取属性值和元数据等。

**Meta**  
元数据对应实现类，可以绑定到特定Entity或Spo的实例上。


## 基本概念 ##


![](http://10.205.63.30:8200/static/host/img/kbjson01.PNG)

_注：这里的Spo的O部分可为多值，且值间有序。_

Entity对象是四层结构：Entity是属性名到ATTR的映射词典，ATTR是SPO的无序集合，SPO可包含个KValue值，即：  
Entity => ATTR DICT(+META) => SPO SET => KVALUE LIST(+META)

举例：电影阿凡达的年份、演员和主演三个属性，用若干SPO表示：

- （阿凡达，演员，A）
- （阿凡达，演员，B）
- （阿凡达，演员，C）
- （阿凡达，主演，A B）

此例中有2个ATTR：演员和主演  
演员有3个（无序）SPO，值分别为A、B、C  
主演有1个SPO，这个SPO有2个（有序）KVALUE为"A B"

### KValue是什么 ###

首次接触KB-JSON格式时，往往对其复杂的层次，对哪些API返回数组，哪些返回字符串或对象容易混淆。

从基本概念图可以看到，一个实体由多个三元组(S, P, O)组成。其中S表示三元组所在实体，P代表属性名，O总是一个KValue对象的数组。而同一属性名P下，又可以有多个三元组。

比如有实体obj，则：
obj.get("age")返回match特定"S"（obj）上某个"P"（age）的三元组的数组a，a[0]是一个三元组对象spo，spo.items()返回其"O"，这个"O"是一个数组oa，oa[0]是"O"中的一个值（KValue）。

最终，所有的值都由KValue对象来表达，有以下几种情形：  
1. 值是简单字符串，则KValue.type()为bkgss:Text, KValue.get("value")为字符串值  
2. 值是结构化数据，则KValue.type()为StructuredValue或者其派生类，KValue.get("xxx")返回字段xxx的值，这个值本身又可以是字符串或者KValue对象  
3. 值是一个小实体（可看做情形2的泛化），则KValue.type()为Person等实体类型，KValue.get("value")一般为实体名称，KValue.get("refer")为实体ID，其他字段同情形2

综上可见，仅仅获取一个单值属性的字符串值，也是比较复杂的。因此，针对常用的场景，提供了一批快捷访问函数如下：
```python
Entity.getv("age")					= Entity.get("age")[0..n].items()[0..n].get("value") => List<string>
Entity.geto("age")					= Entity.get("age")[0..n].items() => List<KValue>
Entity.get("age")[0].v()        	= Entity.get("age")[0].items()[0].get("value") => string
Entity.get("age")[0].r()			= Entity.get("age")[0].items()[0].get("refer") => string
Entity.get("age")[1].o().get("max") = Entity.get("age")[1].items()[0].get("max") => string
```

### 多Type实体支持 ###

多Type特性在数据表达上体现在：

1. 实体类型可以是多值，比如某人同时是演员和歌手
2. 实体中的三元组可以指定一个或多个subjectType，比如award属性可以明确指定属于演员还是歌手

新增三元组时，可选指定subjectType。

* subjectType可缺省，此时逻辑上可以将“空值”看作这个三元组的subjectType。语义上，这代表并不关心此三元组的subjectType
* subjectType有值时，新增三元组（注意：并不会自动将这个类型值添加到实体类型中去）

获取三元组时：
  
* 参数给定非空subjectType，仅返回subjectType与给定值匹配的三元组  
* 参数未指定subjectType，则返回所有相关三元组，不管这些三元组的subjectType是否为空

获取一个三元组的subjectType时，如果该三元组未指定subjectType则返回空字符串。

修改实体类型时，内部判断并确保实体类型集合是实体所有三元组的subjectType集合的超集。若不符合此条件，拒绝修改。


### 三元组有序性支持 ###

每个三元组可以包含多个有序值。


## 接口设计 ##

TODO:接口稳定后补充类图

### 类说明 ###

* **Entity**：实体对象，包含三元组无序集合

* **Spo**：三元组对象，包含属性名、KValue值有序数组和关联Meta集合

* **KValue**：值对象，封装一个字符串值、数组或者字典，数组和字典值可嵌套KValue

* **Meta**：和实体或三元组关联的meta对象

* **MetaSPO**：系统定义的和三元组关联的标准meta对象类型，包含stat、fromType、timeGenerate、timeLastMod四个必选字段和若干可选字段

* **Config**：工具库配置类，存储全局配置

* **EntityExp**：实体对象，内部使用json-ld展开后的格式，派生自Entity


### 实体操作 ###

```c++
//
// 实体创建和序列化
//
Entity(id : string)										//（构造函数）创建新实体，id为None时新产生GUID
Entity.fromKbjson(text : string, jsonldFormat : bool) : Entity				//（静态成员）从KB-JSON 2.0文本解析实体对象
Entity.fromKbjsonObject(jsobj : JsonObject, jsonldFormat : bool) : Entity	//（静态成员）从KB-JSON 2.0格式的JSON对象解析实体对象
Entity.toString(indent : int, sort : bool) : string		// 序列化实体为KB-JSON 2.0文本，sort指定JSON对象key是否排序，默认为False
Entity.toKbjsonObject() : JsonObject					// 序列化实体为KB-JSON 2.0格式的JSON对象
Entity.fromKbjson1(text : string) : Entity				// 从KB-JSON 1.0文本解析实体对象

Entity.fromParser(text : string, parserName : string)	// 使用解析器插件从特定格式的文本中解析实体对象

//
// 实体信息读写
//
Entity.name() : string						// 获取实体名（标记为DEFAULT的SPO优先）
Entity.size() : int							// 获取实体中的三元组个数
Entity.type() : List<string>				// 获取实体类型
Entity.addType(type : string)				// 添加类型
Entity.removeType(type : string)			// 删除类型
Entity.hasType(type : string) : bool		// 判断类型
Entity.setType(types : List<string>)		// 重置类型
Entity.context() : string					// 获取context
Entity.context(ctx : string)				// 设置context
Entity.id() : string						// 获取实体ID
Entity.id(id : string)						// 设置实体ID
```

**JSON-LD格式兼容**

JSON-LD中的无序集合，若只有一个元素，表达为json时，单个对象或数组表示都是合法的。

默认情况下，Entity.fromKbjson等函数假定无序集合的json表达总是数组，Entity.toString等函数也总是输出数组（仅Spo的subjectType除外，若该值为从外部解析且并未修改过，输出时仍然可能是非数组）。

如果确实需要解析来自外部工具产出的JSON-LD标准的文本，则需要在Entity.fromKbjson中指定参数jsonldFormat为True。

### 属性操作 ###

```c++
//
// 属性创建
//
Entity.addSpo(name : string, value : KValue, stat : string, fromType : string) : Spo	// 新建Spo对象并添加到Entity中，value可为单值或数组
Entity.add(spo : Spo)								// 添加Spo对象到Entity中

//
// 属性值创建和读写
//
KValue(value : string)								// (构造函数)value可缺省，也可为string或Json对象
KValue.create(value : jsonValue)					// (静态成员)value可缺省，也可为string、数组或Json对象（从数组创建KValue时必须使用此方法）
KValue.get(name : string) : KValue					// 获取字段值
KValue.set(name : string, value : KValue) : KValue	// 设置字段值
KValue.hasKey(name : string) : bool                 // 查询字段是否存在
KValue.remove(name : string)						// 删除字段值
KValue.size() : int                                 // 返回字段个数
KValue.type() : string								// 获取objectType单值，多type时返回第一个
KValue.type(type : string) : KValue					// 设置objectType单值
KValue.types() : List<string>						// 获取objectType多值
KValue.types(type : List<string>) : KValue			// 设置objectType多值
KValue.items() : List<Tuple<string, KValue>>		// 返回所有字段和值，其中值可能为KValue或string
KValue.equals(right : KValue)						// 比较两个KValue对象
KValue.isArray() : bool								// 判断是否支持数组操作
KValue.isObject() : bool							// 判断是否支持词典操作
KValue[i] = KValue									// 数组元素索引
KValue.append(value : KValue)						// 数组元素添加
KValue.index(value : KValue)						// 数组元素位置查询
KValue.remove(value : KValue)						// 数组元素移除
KValue.nodes() : List<string, KValue>               // 遍历KValue中所有节点
KValue.flat() : List<string, string>                // 打平KValue中的所有叶子节点值为KV数组，key为叶子节点路径

Entity.flat() : List<string, string>                // 打平实体中的所有值为KV数组，key包含了属性名
Entity.flat(name : string) : List<string, string>   // 打平特定属性中的所有值为KV数组，key为叶子节点路径

KValue.flat(type=True) : List<string, string, string)               // 功能同上，打平结果中增加一列节点类型，其值为string或List<string>
Entity.flat(type=True) : List<string, string, string>
Entity.flat(name : string, type=True) : List<string, string, string>
Entity.nodes() : List<string, KValue>
Entity.nodes(name : string) : List<string, KValue>

//
// 属性获取
//
Entity.get(name : string, filter : JsonObject) : List<Spo>				// Entity => Spo
Entity.geto(name : string, filter : JsonObject) : List<KValue>			// Entity => Spo中的值对象
Entity.getv(name : string, filter : JsonObject) : List<string>			// Entity => Spo中值的value字段
Entity.triples(filter : JsonObject) : List<Spo)							// Entity => Spo
Entity.hasKey(key : string) : bool
Entity.keys() : List<string>
Entity.items(filter : JsonObject) : List<Tuple<string, List<Spo>>>		// 按属性名分组遍历Spo
Entity.combineFilter(filter1 : JsonObject, filter2 : JsonObject, ...)	// 合并多个属性过滤器
Entity.invertFilter(filter : JsonObject)								// 反转得到新的过滤器
                                    
Spo.p() : string						// 获取属性名
Spo.r() : string						// 获取首个refer字段
Spo.v() : string						// 获取首个value字段
Spo.o() : KValue						// 获取首个属性值，结果为包括value、refer、type等字段的词典
Spo.subjectType() : List<string>		// 获取subjectType值
Spo.items() : List<KValue>				// 获取属性值数组
Spo.values() : List<string>				// 获取属性值的value字段组成的数组
Spo.equals(right : Spo)					// 返回两个Spo的属性名和items是否都相等
Spo.hash()								// 返回三元组值的签名
Spo.size() : int						// 返回属性值个数
             
Spo.toString(indent: int) : string                  // 返回KB-JSON 2.0表示的spo中的o
Spo.fromString(data : string, name : string)        // 从KB-JSON 2.0解析spo，name为属性名（可选）

//
// 属性修改
//
Entity.remove(spo : Spo)				// 从Entity中删除Spo
Spo.p(value : string)					// 设置属性名
Spo.r(value : string)					// 设置首个refer字段
Spo.v(value : string)					// 设置首个value字段
Spo.o(value : KValue)					// 设置首个属性值
Spo.addSubjectType(type : string)		// 添加subjectType值
Spo.removeSubjectType(type : string)	// 移除subjectType值
Spo.append(value : KValue)				// 添加属性值
Spo.remove(value : KValue)				// 删除属性值
Spo.index(value : KValue)
```
_注：在接收KValue类型参数的地方，支持直接使用string，此时会自动将string封装为类型为文本的KValue对象。_

**属性获取中的filter参数**

在get、geto、getv、triples、items中，可以指定一个由string类型的Key-Value对组成的过滤对象，用以对subjectType和MetaSPO中的字段进行过滤。

列如：
```python
# 过滤器举例
o = Entity()
o.getv(name, {"subjectType" : "Singer"})								// subjectType过滤
o.getv(name, {Entity.META_FROM_TYPE : Entity.META_FROM_TYPE_PUSH})		// meta字段过滤
o.getv(name, Entity.F_PUSH)												// 效果同上
o.getv(name, o.combineFilter(Entity.F_PUSH, Entity.F_NODEL))			// 使用多个过滤器
o.getv(name, o.invertFilter(Entity.F_PUSH))								// 使用反向过滤器
```

系统预置过滤器：

```
F_NODEL  				// 未标记为删除
F_DEL  					// 标记为删除
F_RAW  					// {META_STATUS : META_STATUS_RAW}
F_CLEAN  
F_IDENTIFIED  
F_DEFAULT  
F_PUSH  				// {META_FROM_TYPE : META_FROM_TYPE_PUSH}
F_EXTRACT  
F_INFERENCE  
F_MINING  
F_INTERVENE  
F_FEED  
F_CLEANSE  
F_CN  					// {META_LANG : META_LANG_CN}
F_EN  
```

**objectType的确定**

objectType存储于KValue中的"@type"字段。其值的确定分以下情况：

1. 若KValue从string自动转换而来，则默认为bkgss:Text
2. 若用户使用KValue.type函数设置了@type，则使用该值
3. 若用户未指定，则在将KValue添加到实体的某个属性上时，根据待设置属性在Schema上的range来推断。推断失败时拒绝该KValue的添加


**高级遍历接口**

Entity和KValue提供了高级遍历接口nodes和flat，其中Entity.nodes还可以指定属性名，实现ATTR粒度遍历。

这些遍历接口的功能，是把树状的结构打平为数组。nodes的返回结果为两列：

1. 属性名，其值可能包含"."号表示嵌套节点
2. 节点，其类型可能是KValue和string（不含KValueArray）

nodes调用，会遍历所有的节点，包括@type等系统节点。

flat调用，仅返回叶子节点，且不包括@开头的叶子节点。另外，flat调用支持一个布尔参数type，设置为True时，将返回三列结果，第三列是第二列中的叶子节点所在的上层节点的类型，注意其值为string或数组。

### meta操作 ###

```c++
//
// meta创建
//
Meta(type : string)									// (构造函数)type可为string（Meta类型）或原始Json对象
Entity.appendMeta(meta : Meta)						// 关联Meta对象到实体中
Spo.appendMeta(meta : Meta)							// 关联Meta对象到三元组中

//
// meta获取 
//
Entity.m(name : string) : string                    // 获取S上MetaS字段值
Spo.m(name : string) : string						// 获取MetaSPO字段值
KValue.m(name : string) : string					// 获取O上MetaS字段值

Entity.meta(type : string) : List<Meta>				// Entity => Meta
Spo.meta(type : string) : List<Meta>				// Spo => Meta
Meta.get(name : string) : string					// 获取meta中字段值

//
// meta修改
//
Entity.m(name : string, value : string)             // 设置S上MetaS字段值
Spo.m(name : string, value : string)				// 设置MetaSPO字段值
KValue.m(name : string, value : string) : KValue	// 设置O上MetaS字段值

Entity.removeMeta(meta : Meta)						// 从实体中删除关联的Meta对象
Spo.removeMeta(meta : Meta)							// 从三元组中删除关联的Meta对象
Meta.set(name : string, value : string)				// 设置meta中该字段值
Meta.remove(name : string)							// 删除meta中的字段
```

### 关联Schema信息 ###

TODO：第二版纳入Schema相关API

### json-ld格式兼容 ###

**名称展开**

实现上，Entity类内部并未根据context展开短名称，为使名称不出现歧义，要加上两个假定：

1. 假定json-ld中，当短名称的命名空间和base指向相同时，总是省略命名空间前缀，比如：bkgs:Person和Person统一使用后者
2. 假定前缀bkgss总是指向http://kgs.baidu.com/schema#

若用户场景突破了这两个假定，或者确实需要使用展开后的长名称，应使用从Entity派生的EntityExp类：

```c++
//
// EntityExp相关操作
//
Entity.expand() : EntityExp							// Entity => EntityExp
EntityExp.flatten() : Entity						// EntityExp => Entity
EntityExp.toString() : string						// 序列化为展开后的格式
EntityExp.fromKbjson(text : string) : EntityExp		// 从展开后的格式反序列化
```

_注：EntityExp继承了Entity的所有方法，并允许在方法参数中任意使用bkgs:Person和Person等形式，它们在内部都会被展开成唯一的长名称后再使用。_


## 其他特性 ##

### 属性的属性（attribute of property） ###

属性上的属性在Schema的Property类及其派生类上定义，其值类似于三元组中的值。

```c++
//
// 属性的属性操作
//
Spo.attr(name : string) : KValue					// 获取
Spo.attr(name : string, value : KValue)				// 修改
Spo.attrs() : List<Tuple<string, string>>			// 遍历
Spo.removeAttr(name : string)						// 删除
```

### raw属性 ###

raw属性指未映射到Schema上的属性，可看作均为string类型的name-value对。

raw属性统一设置到实体中名为property的属性中，raw属性的name放到属性的属性中，value放到KValue的value字段。

手工存储raw属性的例子：
```python
# 给定实体o，手工存储raw属性RAW_NAME=RAW_VALUE
raw = KValue("RAW_VALUE")
spo = o.createSpo("property", raw)
spo.attr("name", "RAW_NAME")
o.add(spo)
```

上述例子是演示raw属性的实现，用户应使用专门的API来操作raw属性：
```c++
//
// raw属性操作
//
Entity.getRaw(name : string) : List<string>				// 获取
Entity.addRaw(name : string, value : string)			// 添加
Entity.removeRaw(name : string, value : string)			// 删除（value缺省时，删除所有名称为name的raw属性）
Entity.rawItems() : List<Tuple<string, string>>			// 返回所有raw属性和值
```

前面例子改用raw属性操作API实现：
```python
# 给定实体o，手工存储raw属性RAW_NAME=RAW_VALUE
o.addRaw("RAW_NAME", "RAW_VALUE")
```

### MetaSPO类 ###

MetaSPO是系统预置的meta类型，在每个SPO上只能关联一个MetaSPO实例。

MetaSPO一般由系统生成和维护，用户应通过前述Spo.m等快捷函数操作MetaSPO。


## FAQ ##

* **实体操作，是否考虑其他格式的序列化和反序列化？ kbjson1.0、jsonld、普通json**

	根据需求会逐步支持，原则上避免发明新的复杂格式约定，所以序列化到其他格式是有损的，而从其他格式反序列化后，需要配合一些API来补全KB-JSON 2.0特有的内容（比如批量设置某个属性的subjectType等）。
	<br/>

* **实体的type，和实体各三元组的subjectType之间是什么关系？二者会同步吗？**

	若有实体type集合A，实体各三元组的subjectType组成的集合B，则A应该是B的超集。API不会自动对二者进行同步，暂由用户保证一致性。
	<br/>

* **编辑实体时，会检查修改是否符合schema上定义的要求吗？**

	不会。schema相关的正确性验证，不在每次修改实体时进行。需要时，可以由系统或用户通过API验证实体有效性。
	<br/>