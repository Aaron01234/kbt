# coding=utf-8


import sys
import json
import time
from spo import *
from data import *
from config import *

class Entity(object):
    #
    # 常量定义
    #
    META_STATUS = "stat"
    META_STATUS_RAW = "RAW"
    META_STATUS_CLEAN = "CLEAN"
    META_STATUS_MARKDEL = "MARKDEL"
    META_STATUS_IDENTIFIED = "IDENTIFIED"
    META_STATUS_DEFAULT = "DEFAULT"
    META_STATUS_MISS = "MISS"

    META_FROM_TYPE = "fromType"
    META_FROM_TYPE_PUSH = "PUSH"
    META_FROM_TYPE_EXTRACT = "EXTRACT"
    META_FROM_TYPE_INFERENCE = "INFERENCE"
    META_FROM_TYPE_MINING = "MINING"
    META_FROM_TYPE_INTERVENE = "INTERVENE"
    META_FROM_TYPE_FEED = "FEED"
    META_FROM_TYPE_CLEANSE = "CLEANSE"
    META_FROM_TYPE_MANUAL = "MANUAL"

    META_APPROVAL_STAT = "approvalStat"
    META_APPROVAL_STAT_PENDING = "PENDING"
    META_APPROVAL_STAT_REVISING = "REVISING"
    META_APPROVAL_STAT_APPROVED = "APPROVED"
    META_APPROVAL_STAT_REJECTED = "REJECTED"

    META_LANG = "lang"
    META_LANG_CN = "zh-cn"
    META_LANG_EN = "en-us"

    META_VIEW_ID = "viewId"
    META_CONFIDENCE = "confidence"
    META_FROM_URL = "fromUrl"
    META_CREATE_TIME = "timeGenerate"
    META_MODIFY_TIME = "timeLastMod"
    META_EXPIRE_TIME = "timeExpire"

    META_LOCAL_REFER = "localRefer"

    # 过滤操作和过滤器
    F_NODEL = {META_STATUS : "!" + META_STATUS_MARKDEL}
    F_DEL = {META_STATUS : META_STATUS_MARKDEL}
    F_RAW = {META_STATUS : META_STATUS_RAW}
    F_CLEAN = {META_STATUS : META_STATUS_CLEAN}
    F_IDENTIFIED = {META_STATUS : META_STATUS_IDENTIFIED}
    F_DEFAULT = {META_STATUS : META_STATUS_DEFAULT}
    F_MISS = {META_STATUS : META_STATUS_MISS}

    F_PUSH = {META_FROM_TYPE : META_FROM_TYPE_PUSH}
    F_EXTRACT = {META_FROM_TYPE : META_FROM_TYPE_EXTRACT}
    F_INFERENCE = {META_FROM_TYPE : META_FROM_TYPE_INFERENCE}
    F_MINING = {META_FROM_TYPE : META_FROM_TYPE_MINING}
    F_INTERVENE = {META_FROM_TYPE : META_FROM_TYPE_INTERVENE}
    F_FEED = {META_FROM_TYPE : META_FROM_TYPE_FEED}
    F_CLEANSE = {META_FROM_TYPE : META_FROM_TYPE_CLEANSE}
    F_MANUAL = {META_FROM_TYPE : META_FROM_TYPE_MANUAL}

    F_PENDING = {META_APPROVAL_STAT : META_APPROVAL_STAT_PENDING}
    F_REVISING = {META_APPROVAL_STAT : META_APPROVAL_STAT_REVISING}
    F_APPROVED = {META_APPROVAL_STAT : META_APPROVAL_STAT_APPROVED}
    F_REJECTED = {META_APPROVAL_STAT : META_APPROVAL_STAT_REJECTED}

    F_CN = {META_LANG : META_LANG_CN}
    F_EN = {META_LANG : META_LANG_EN}

    #
    # 实体创建和序列化
    #
    def __init__(self, id=None):
        u"id为空（含空串）时随机生成。id为None时自动生成GUID"

        # id、context、type、属性集合和meta数组
        self._id = u""
        self._context = u""
        self._type = []
        self._attrs = {}
        self._meta = []
        self._metaS = None

        # id初始化
        if id is None: id = self._guid()
        self.id(id)

        # 缓存字段
        self._leafcache = None              # 叶子节点路径=>值的缓存

    @staticmethod
    def fromKbjson(text, jsonldFormat=False):
        return Entity.fromKbjsonObject(json.loads(text), jsonldFormat=jsonldFormat)

    @staticmethod
    def fromKbjsonObject(jsobj, jsonldFormat=False):
        return Entity("")._parseFromKbjson(jsobj, jsonldFormat=jsonldFormat)

    @staticmethod
    def fromKbjson1(text):
        return Entity.fromParser(text, "v1")

    @staticmethod
    def fromJsonld(text):
        return Entity.fromParser(text, "JsonldParser")

    @staticmethod
    def fromParser(text, parserName=None):
        u"从解析器插件解析出实体对象，parserName为空时尝试自动判断"
        import parsers
        if parserName is None:
            raise NotImplementedError()
        p = parsers.Parser.get(parserName)
        if p is None: raise Exception("parser not found: '%s'" % parserName)
        o = p.parse(text)
        assert isinstance(o, Entity)
        return o

    def _toKbjson(self, indent=None, sort=False, dense=True, encoding="utf-8"):
        u"返回utf-8字节流，若要返回unicode，设置encoding为None"
        jsobj = self.toKbjsonObject(dense=dense)
        text = json.dumps(jsobj, ensure_ascii=False, indent = indent, sort_keys=sort)
        if encoding is not None:
            text = text.encode(encoding)
        return text

    def toKbjson(self, *args, **kwargs):
        u"此接口已废弃"
        print >> sys.stderr, "WARN: Entity.toKbjson is deprecated, use 'Entity.toString' instead"
        return self._toKbjson(*args, **kwargs)

    def toString(self, indent=None, sort=False, dense=True, encoding=None):
        return self._toKbjson(indent, sort, dense, encoding)

    def toJson(self, indent=None, sort=False, default=False):
        jsobj = {"id" : self.id(), "type" : self.type()}
        filter = self.F_DEFAULT if default is True else None
        for attr in self:
            a = self.getv(attr, filter=filter)
            if a: jsobj[attr] = a
        text = json.dumps(jsobj, ensure_ascii=False, indent = indent, sort_keys=sort)
        text = text.encode("utf-8")
        return text
    
    def _objectChange(self, objs, mdict):
        assert isinstance(objs, dict) or isinstance(objs, KValue) and objs.isObject()\
                , 'unexpected type: %s' % type(objs)
        new_obj = {}
        if objs.get('value'): 
            new_obj['@value'] = objs.get('value')
        if objs.get('refer'): 
            new_obj['@id'] = objs.get('refer')
        for k, v in objs: 
            if k != 'value' and k != 'refer' and k != '@type' and k != 'meta' \
                    and k != 'localRefer':
                if isinstance(v, (list, KValueArray)):
                    new_obj[k] = [self._objectChange(item, {}) if isinstance(item, (dict, KValue))\
                            else item for item in v]
                elif isinstance(v, (dict, KValue)): 
                    new_obj[k] = self._objectChange(v, {})
                else: 
                    new_obj[k] = v
        if mdict != {}:
            for k in mdict: 
                if mdict[k]: 
                    new_obj[k] = mdict[k]
        return new_obj
            

    
    def toKBLite(self, default=False, context=None, idBase=None, internal=False, raw=True):
        u"""
        default: 是否只取stat为DEFAULT的spo
        idBase: 指定id前缀
        context: 指定数据context
        internal: 是否获取内部属性
        raw: 是否获取raw属性
        """
        idBase = idBase or ''
        if idBase and not isinstance(idBase, basestring):
            raise Exception('Id base must be string or unicode.')
        jsobj = {S_S_ID: '%s%s' % (idBase, self.id()), S_SPO_TYPE: self.type()}
        if context: 
            jsobj[S_S_CONTEXT] = context
        elif self.context(): 
            jsobj[S_S_CONTEXT] = self.context()
        filter = self.F_DEFAULT if default is True else self.F_NODEL
        #if self.m('timeGenerate'): 
        #    jsobj['@cts'] = self.m('timeGenerate')
        #if self.m('timeLastMod'): 
        #    jsobj['@dts'] = self.m('timeLastMod')
        for attr in self:
            if not internal and attr.startswith('_'):
                continue
            if attr==S_S_RAW_PROPERTY_NAME: 
                if not raw: 
                    continue
                else: 
                    for k, v in self.rawItems(filter): 
                        v_json = json.loads(v)
                        if k.startswith('@'):       # 保留字，不做格式处理
                            if k not in jsobj:
                                jsobj[k] = v_json
                            else:
                                if not isinstance(jsobj[k], list):
                                    jsobj[k] = [jsobj[k]]
                                jsobj[k].append(v_json)
                        else:
                            if isinstance(v_json, dict):
                                if 'value' in v_json and '@value' not in v_json: 
                                    v_json['@value'] = v_json['value']
                                    v_json.pop('value')
                            elif isinstance(v_json, basestring):
                                v_json = {'@value': v_json}
                            elif isinstance(v_json, list):
                                for i in xrange(len(v_json)):
                                    item = v_json[i]
                                    if isinstance(item, dict):
                                        if 'value' in item and '@value' not in item:
                                            item['@value'] = item['value']
                                            item.pop('value')
                                    elif isinstance(item, basestring):
                                        v_json[i] = {'@value': item}
                            jsobj.setdefault(k, [])
                            if isinstance(v_json, list):
                                jsobj[k].extend(v_json)
                            else:
                                jsobj[k].append(v_json)
                continue
            value = []
            for spo in self.get(attr, filter): 
                mdict = {}
                m_attr = {'fromUrl':'@fromurl','fromType':'@fromtype','lang':'@lang'}
                for item in m_attr:
                    if spo.m(item):
                        new_item =m_attr[item]
                        mdict[new_item] = spo.m(item)
                objs = spo.o()
                try:
                    if objs.isObject():
                        final_value = self._objectChange(objs, mdict)
                        value.append(final_value)
                    else:
                        for obj in objs: 
                            final_value = self._objectChange(obj, mdict)
                            value.append(final_value)
                except:
                    print >> sys.stderr, (u"process propery '%s' failed" % spo.p()).encode("utf-8")
                    raise
            jsobj[attr] = value
        return jsobj
            

    def toJsonLD(self, default=False, context=None, idBase=None, internal=False, raw=False):
        u"""
        default: 是否只取stat为DEFAULT的spo
        context: 指定数据context
        idBase: 指定id前缀
        internal: 是否获取内部属性
        raw: 是否获取raw属性
        """
        idBase = idBase or ''
        if idBase and not isinstance(idBase, basestring):
            raise Exception('Id base must be string or unicode.')
        jsobj = {S_S_ID: '%s%s' % (idBase, self.id()), S_SPO_TYPE: self.type()}
        jsobj[S_S_CONTEXT] = context or self.context()
        filter = self.F_DEFAULT if default is True else self.F_NODEL
        for attr in self:
            if not internal and attr.startswith('_'):
                continue
            if not raw and attr==S_S_RAW_PROPERTY_NAME:
                continue
            value = []
            for objs in self.geto(attr, filter=filter):
                if objs.isObject():
                    queue = [(value, objs)]
                elif objs.isArray():
                    queue = [(value, obj) for obj in objs]
                else:
                    assert 0
                while(queue):
                    cur, o = queue.pop(0)
                    assert isinstance(cur, list)
                    if isinstance(o, basestring):
                        cur.append(o)
                        continue
                    assert isinstance(o, KValue)
                    refer = o.get(S_SPO_REFER)
                    local_refer = o.get('localRefer')
                    val = o.get(S_SPO_VALUE)
                    if refer and refer!=u'010':     # @TODO: 常量定义: 010为建边nil实体
                        cur.append({S_S_ID: '%s%s' % (idBase, refer)})
                        continue
                    elif val and (o.size()<=2 or o.size()<=3 and (refer==u'010'\
                            or local_refer) or o.size()<=4 and refer==u'010' and local_refer):
                            # 粗陋的svalue判断，@TODO: 引入schema
                        cur.append(val)
                        continue
                    else:
                        data = {}
                        for k, v in o.items():
                            data[k] = []
                            if isinstance(v, (list, KValueArray)):
                                for item in v:
                                    queue.append((data[k], item))
                            else:
                                queue.append((data[k], v))
                        cur.append(data)
            if value:
                jsobj[attr] = value
        # 去单值括号
        queue = [jsobj]
        while(queue):
            cur = queue.pop(0)
            assert isinstance(cur, dict)
            for k, vs in cur.iteritems():
                if k.startswith('@'): continue
                assert isinstance(vs, list)
                for v in vs:
                    if isinstance(v, dict):
                        queue.append(v)
                if len(vs)==1:
                    cur[k] = vs[0]
        return jsobj

    def combineFilter(self, *args):
        ret = {}
        for f in args:
            assert isinstance(f, dict)
            ret.update(f)
        return ret

    def invertFilter(self, filter):
        u"过过滤器中的每一个过滤条件取反"
        ret = {}
        for key, value in filter.items():
            if value and value[0] == "!": newv = value[1:]
            else: newv = "!" + value
            ret[key] = newv
        return ret

    def toKbjsonObject(self, dense=True):
        u"转化后，原来JSON根部带有的双下划线字段会丢失"
        # 空串值处理
        if dense is True:
            self._removeEmptyFields()

        # 设置attributes
        jsobj = dict(self._attrs)

        # 设置id、context、type
        id = self.id()
        context = self.context()
        tlist = self.type()

        if id: jsobj[S_S_ID] = id
        if context: jsobj[S_S_CONTEXT] = context
        if tlist: jsobj[S_SPO_TYPE] = tlist

        # 设置meta
        if len(self._meta) > 0:
            jsobj[S_S_META] = self._meta

        return jsobj

    def toTriple(self):
        u"转化为易读的三元组列表，用于直接打印"
        ret = []
        try:
            name = self.getv("name")[0]
        except:
            name = self.id()

        for spo in self.triples():
            try:
                ret.append(u"%s\t%s\t%s" % (name, spo.p(), spo.v()))
            except:
                print >> sys.stderr, "bad property: %s" % (spo.p())
        return "\n".join(ret)

    #
    # 实体信息读写
    #
    def size(self):
        u""
        # 每次重新计算
        count = 0
        for attr in self._attrs.values():
            for spl in attr:
                count += len(spl[S_SPO_OBJECT])
        return count

    def type(self):
        return self._type

    def name(self):
        u"返回实体名，标记为DEFAULT的SPO优先"
        # 要考虑identified和default的情况，所以即使是单值也不能直接读写
        ##if name is None:
        ##    a = self.getv("name")
        ##    if a: return a[0]
        ##    else: return u""
        ##else:
        ##    spos = self.get("name")
        ##    if len(spos) == 0:
        ##        spo = self.createSpo("name", name)
        ##        self.add(spo)
        ##    else:
        ##        spo = spos[0]
        ##        spo.v(name)
        a = self.getv("name", Entity.F_DEFAULT)
        if len(a) == 0: a = self.getv("name")
        return a[0] if a else u""

    def addType(self, type):
        if type not in self._type:
            self._type.append(type)

    def setType(self, type):
        self._type = list(type)

    def removeType(self, type):
        if type in self._type:
            # 因无schema信息，无法做到派生类之间的兼容性检查，所以暂时去掉了
            ## 验证是否可以删除（检查subjectType）
            #for spo in self.triples():
            #    if type in spo.subjectType():
            #        raise Exception("Error: can't remove type '%s', property '%s' has a subjectType with it." % (type, spo.p()))
            self._type.remove(type)
        
        # 删除不存在的type，无需处理

    def hasType(self, type):
        return type in self._type

    def context(self, ctx=None):
        if ctx is None:
            return self._context
        else:
            self._context = ctx

    def id(self, id=None):
        u"设置和获取实体ID"
        # 允许使用空串参数表达不希望生成ID
        if id is None:
            return self._id
        else:
            assert isinstance(id, basestring)
            self._id = id

    #
    # 属性创建
    #
    def addSpo(self, name, value, stat=None, fromType=None):
        u"value可以是string或KValue对象，或者它们构成的数组，返回添加到实体中的Spo对象"
        spo = self.createSpo(name, value, stat, fromType)
        self.add(spo)
        return spo

    def createSpo(self, name, value, stat=None, fromType=None):
        # 此接口已经废弃
        return self._createSpo(name, value, stat, fromType)

    def _createSpo(self, name, value, stat=None, fromType=None):
        u"value可以是string或KValue对象，或者它们构成的数组"
        # Spo对象糅合了属性名、属性值（包括值和类型）和元信息
        assert name and value is not None

        if not isinstance(value , list):
            value = [value]

        # create spo
        kvs = []
        for v in value:
            if isinstance(v, basestring):
                kv = KValue(v)
            elif isinstance(v, KValue):
                kv = v
            else:
                #print >> sys.stderr, v
                raise Exception("value should be Text or KValue")
            # objectType检测
            # TODO：必要时根据实体类型和name从schema推断类型
            if not kv.type():
                raise Exception("objectType not set")
            kvs.append(kv)
        spo = Spo(name, Spo._createRaw(kvs))

        # stat、fromType
        if stat: spo.m(Entity.META_STATUS, stat)
        if fromType: spo.m(Entity.META_FROM_TYPE, fromType)

        # create time
        t = spo._time()
        spo.m(Entity.META_CREATE_TIME, t)
        spo.m(Entity.META_MODIFY_TIME, t)

        return spo

    def add(self, spo):
        attrs = self._attrs
        name = spo.p()
        assert name, "Spo: property name is not set"
        if name not in attrs:
            attr = []
            attrs[name] = attr
        else:
            attr = attrs[name]
        attr.append(spo._toJson())

    def remove(self, spo):
        name = spo.p()
        attr = self._attrs.get(name)
        if attr is not None:
            jsobj = spo._toJson()
            attr.remove(jsobj)
            if len(attr) == 0:
                del self._attrs[name]

    #
    # 属性获取
    #
    def get(self, name, filter=None):
        u"获取特定属性名下的Spo列表"
        ret = []
        attr = self._attrs.get(name)
        if attr is not None:
            for jsSpo in attr:
                spo = Spo(name, jsSpo)
                if filter is None or spo.match(filter):
                    ret.append(spo)
        return ret

    def nodes(self, name=None, filter=None, parseRaw=False):
        return self._flat(name=name, filter=filter, parseRaw=parseRaw, leaf=False, withType=False)

    def flat(self, name=None, filter=None, parseRaw=False, type=False):
        return self._flat(name=name, filter=filter, parseRaw=parseRaw, leaf=True, withType=type)

    def _flat(self, name=None, filter=None, parseRaw=False, withType=False, leaf=True):
        u"打平整个实体，或特定属性，只给出叶子节点。withType为True时，额外给出所有节点的类型。"
        # parseRaw为True时，自动解析raw属性
        if parseRaw: assert name is None
        a = []
        if name is None:
            for name, spl in self.items(filter=filter):
                flag = parseRaw and name == "property" 
                for spo in spl:
                    # 特殊处理：将raw属性的value反序列化为Json值
                    if flag:
                        jsobj = json.loads(json.dumps(spo._toJson(), ensure_ascii=False))
                        spo = Spo(spo.p(), jsobj)
                        po = jsobj["objects"][0]
                        s = po.get("value")
                        if isinstance(s, basestring):
                            obj = json.loads(s)
                            if type(obj) in (list, dict):
                                del po["@type"]         # 直接抛弃了Text类型，使结构化值能正常展开
                            else:
                                obj = unicode(obj)
                            po["value"] = obj


                    for kv in spo.items():
                        kv.flat(a, name, leaf=leaf, type=withType)
        else:
            spl = self.get(name, filter)
            for spo in spl:
                for kv in spo.items():
                    kv.flat(a, leaf=leaf, type=type)
        return a
    
    def dump(self, parseRaw=False):
        a = self.flat(parseRaw=parseRaw)
        a.sort()
        lastProp = None
        name = self.name()
        type = " ".join(self.type())
        print (u"%s[%s](%s)" % (name, type, self.id())).encode("utf-8")

        format = "%-30s %-50s %s"
        print format % ("Property", "Leaf", "Value")
        print "-" * 100
        for key, value in a:
            prop = key.split('.')[0]
            name = prop if prop != lastProp else ""
            lastProp = prop
            s = format % (name, key, value)
            s = s.encode("utf-8")
            print s

    def geto(self, name, filter=None):
        u"获取特定属性名下的值对象（KValue）列表"
        ret = []
        if filter is None:
            attr = self._attrs.get(name)
            if attr is not None:
                for jsSpo in attr:
                    kvs = jsSpo.get(S_SPO_OBJECT)
                    if kvs is not None:
                        for jsKV in kvs:
                            ret.append(KValue(jsKV))
        else:
            for spo in self.get(name):
                if spo.match(filter):
                    for kv in spo.items():
                        ret.append(kv)
        return ret

    def getv(self, name, filter=None):
        u"获取特定属性名下的值列表，相同值不去重"
        # Entity => ATTR DICT(+META) => SPO SET => KVALUE LIST(+META)
        ret = []
        if filter is None:
            attr = self._attrs.get(name)
            if attr is not None:
                for jsSpo in attr:
                    kvs = jsSpo.get(S_SPO_OBJECT)
                    if kvs is not None:
                        for o in kvs:
                            ret.append(o.get(S_SPO_VALUE, u""))
        else:
            for spo in self.get(name):
                if spo.match(filter):
                    for v in spo.values():
                        ret.append(v)
        return ret

    def getv2(self, path, filter=None):
        u"获取指定路径下的叶子节点的值列表"
        # 注意：这里的cache并没有失效机制，即假设getv2仅用于实体只读的场景
        if self._leafcache is None:
            a = self.flat(filter=filter)
            post = ".value"
            offset = -len(post)
            kv = {}
            for key, value in a:
                if key.endswith(post):
                    key = key[0:offset]
                if key in kv:
                    kv[key].append(value)
                else:
                    kv[key] = [value]
            self._leafcache = kv
        return self._leafcache.get(path, [])

    def hasKey(self, key):
        return self._attrs.has_key(key)

    def keys(self):
        return self._attrs.keys()

    def __iter__(self):
        for key in self._attrs:
            yield key

    def items(self, filter=None):
        ret = []
        for name, attr in self._attrs.items():
            spos = []
            for jsSpo in attr:
                spo = Spo(name, jsSpo)
                if filter is None or spo.match(filter):
                    spos.append(spo)
            if len(spos) > 0:
                ret.append((name, spos))
        return ret

    def triples(self, filter=None):
        ret = []
        for name, attr in self._attrs.items():
            for jsSpo in attr:
                spo = Spo(name, jsSpo)
                if filter is None or spo.match(filter):
                    ret.append(spo)
        return ret

    #
    # meta操作
    #
    def appendMeta(self, meta):
        assert isinstance(meta, Meta)
        self._meta.append(meta._toJson())

    def removeMeta(self, meta):
        assert isinstance(meta, Meta)
        for item in self.meta():
            if meta.equals(item):
                self._meta.remove(item._toJson())

    def meta(self, type=None):
        if type is None:
            ret = []
            for jsMeta in self._meta:
                ret.append(Meta(jsMeta))
            return ret
        else:
            ret = []
            for jsMeta in self._meta:
                if type == jsMeta.get(S_SPO_TYPE):
                    ret.append(Meta(jsMeta))
            return ret

    def m(self, name, value=None):
        u"快速读写系统预置的单例MetaS上的字段"
        self._ensureMetaS()
        if value is None:
            return self._metaS.get(name)
        else:
            self._metaS.set(name, value)

    #
    # raw属性
    #
    def getRaw(self, name):
        # 系统保留字段不允许访问
        ret = []
        for spo in self.get(S_S_RAW_PROPERTY_NAME):
            if spo.attr("name") == name:
                ret.append(spo.v())

        return ret

    def addRaw(self, name, value):
        assert isinstance(value, basestring)
        raw = KValue(value)
        spo = self.createSpo(S_S_RAW_PROPERTY_NAME, raw)
        spo.attr("name", name)
        self.add(spo)

    def removeRaw(self, name, value=None):
        for spo in self.get(S_S_RAW_PROPERTY_NAME):
            if spo.attr("name") == name:
                if value is None or value == spo.v():
                    self.remove(spo)

    def rawItems(self, filter=None):
        ret = []
        for spo in self.get(S_S_RAW_PROPERTY_NAME, filter):
            ret.append((spo.attr("name"), spo.v()))

        return ret

    #
    # 内部实现
    #
    def _parseFromKbjson(self, jsobj, jsonldFormat=False):
        assert len(self.type()) == 0        # 内部使用方式假设

        if jsonldFormat is True:
            jsobj = self._processJsonldArray(jsobj)

        # 设置id、context、type
        id = jsobj.get(S_S_ID, u"")
        context = jsobj.get(S_S_CONTEXT, u"")
        tlist = jsobj.get(S_SPO_TYPE, [])

        # hack type 1/1: convert string to list
        if isinstance(tlist, basestring): tlist = [tlist]
        assert type(tlist) == list          # 输入数据假设

        if id: self.id(id)
        if context: self.context(context)
        self._type = tlist

        # 设置attributes
        for item in jsobj.items():
            k, v = item
            if k and k[0] != "@" and k != S_S_META:
                if k[0:2] == "__": continue            # 忽略双下划线开头的系统特殊属性
                self._attrs[k] = v

        # 设置meta
        if S_S_META in jsobj:
            for jsMeta in jsobj[S_S_META]:
                self._meta.append(jsMeta)

        return self

    def _processJsonldArray(self, jsobj):
        # TODO: process Entity type and attr subjectType
        for k, v in jsobj.items():
            if k and k[0] != "@":
                if k[0:2] == "__": continue            # 忽略双下划线开头的系统特殊属性
                # meta => [meta], spo => [spo]
                if isinstance(v, dict):
                    v = [v]
                    jsobj[k] = v
        
                for jsspo in v:
                    # spo.meta => [spo.meta]
                    meta = jsspo.get(S_SPO_META)
                    if meta is not None and isinstance(meta, dict):
                        meta = [meta]
                        jsspo[S_SPO_META] = meta

                    # o.meta => [o.meta]
                    for jso in jsspo.get(S_SPO_OBJECT, []):
                        self._processJsonldKValue(jso)

        return jsobj

    def _processJsonldKValue(self, jso):
        for key, value in jso.items():
            if isinstance(value, dict):
                if key == S_S_META:
                    jso[key] = [value]
                else:
                    self._processJsonldKValue(value)

    def _guid(self):
        import uuid
        return str(uuid.uuid1()).replace("-", u"")

    def _removeEmptyFields(self):
        #
        # 要处理的属性
        # S => 空attr
        # SP => subjectType，空meta
        for name, attr in self._attrs.items():
            if len(attr) == 0:
                del self._attrs[name]

            # 跳过双下划线开头的特殊附加属性
            if name[0:2] == "__": continue
            for jspo in attr:
                try:
                    jsSubtype = jspo.get(S_SP_SUBTYPE)
                except:
                    if isinstance(attr, dict):
                        print >> sys.stderr, "Invalid kb-json: property '%s' is not a list. Try parse with 'jsonldFormat=True'." % name
                    raise
                if jsSubtype is not None:
                    # hack subjectType 4/4: convert string to list
                    if jsSubtype == u"": del jspo[S_SP_SUBTYPE]
                    elif len(jsSubtype) == 0:
                        del jspo[S_SP_SUBTYPE]

                jsMeta = jspo.get(S_SPO_META)
                if jsMeta is not None and len(jsMeta) == 0:
                    del jspo[S_SPO_META]

                jsObj = jspo.get(S_SPO_OBJECT)
                if jsObj is not None and len(jsObj) == 0:
                    del jspo[S_SPO_OBJECT]

    def _ensureMetaS(self):
        if self._metaS is not None: return

        target = None
        for jsMeta in self._meta:
            if jsMeta.get(S_SPO_TYPE) == S_S_METAS:
                target = Meta(jsMeta)
                break

        if target is None:
            target = Meta(S_S_METAS)
            self.appendMeta(target)
        self._metaS = target
            

