# coding=utf-8

import sys
import json
import time
import md5
from data import *
import entity

class Spo(object):

    u"""
        spo对象封装了属性名和属性值。
        其中属性名可以为空串（比如在反序列化时），此时Spo不能被添加到Entity。
    """
    
    def __init__(self, name, rawdata):
        u"value类型总是KValue"
        # 仅内部调用
        assert name is not None         # name可以为空串，代表还未绑定属性
        assert rawdata

        # 2个状态
        self._name = name
        self._jsobj = rawdata

        # objects
        try: self._objs = rawdata[S_SPO_OBJECT]
        except: 
            print >> sys.stderr, (u"bad SPO in property '%s'" % name).encode("utf-8")
            raise
        
        # meta和MetaSPO延迟加载
        self._meta = None
        self._metaSPO = None                # 加载后，值为封装好的Meta对象

    @staticmethod
    def _createRaw(kvs=None):
        # kvs总是为KValue对象列表
        assert(kvs is None or isinstance(kvs, list))
        a = []
        jsobj = {S_SPO_OBJECT : a}
        if kvs is not None:
            for kvalue in kvs:
                a.append(kvalue._toJson())
        return jsobj

    #
    # 序列化
    #
    def toString(self, indent=None):
        u"返回Unicode表示"
        s = json.dumps(self._jsobj, indent=indent, ensure_ascii=False)
        return s

    @staticmethod
    def fromString(data, name=None):
        jsobj = json.loads(data)
        if name:
            return Spo(name, jsobj)
        else:
            return Spo("", jsobj)

    #
    # 属性操作
    #
    def p(self, value=None):
        if value is None:
            return self._name
        else:
            # TODO：设置p时，将Spo从Entity移除后重新添加？？
            assert isinstance(value, basestring)
            self._name = value

    def r(self, value=None):
        if value is None:
            if len(self._objs) > 0:
                return self._objs[0].get(S_SPO_REFER, u"")
            else:
                return u""
        else:
            assert isinstance(value, basestring)
            self._ensureOneKV()
            self._objs[0][S_SPO_REFER] = value

    def v(self, value=None):
        if value is None:
            if len(self._objs) > 0:
                return self._objs[0].get(S_SPO_VALUE, u"")
            else:
                return u""
        else:
            assert isinstance(value, basestring)
            self._ensureOneKV()
            self._objs[0][S_SPO_VALUE] = value

    def o(self, value=None):
        u"设置为字符串时，自动封装为KValue"
        if value is None:
            if len(self._objs) > 0:
                return KValue(self._objs[0])
            else:
                return None
        else:
            if isinstance(value, basestring):
                value = KValue._fromText(value)         # wrap text in KValue

            assert isinstance(value, KValue)
            if len(self._objs) == 0:
                self._objs.append(value._toJson())
            else:
                self._objs[0] = value._toJson()

    def subjectType(self):
        ret = self._jsobj.get(S_SP_SUBTYPE, [])
        # hack subjectType 1/4: convert string to list
        if isinstance(ret, basestring): ret = [ret]
        assert isinstance(ret, list)
        return ret

    def addSubjectType(self, type):
        assert type
        if S_SP_SUBTYPE in self._jsobj:
            a = self._jsobj[S_SP_SUBTYPE]
            # hack subjectType 2/4: convert string to list
            if isinstance(a, basestring):
                a = [a]
                self._jsobj[S_SP_SUBTYPE] = a
        else:
            a = []
            self._jsobj[S_SP_SUBTYPE] = a
        if type not in a:
            a.append(type)

    def removeSubjectType(self, type):
        a = self._jsobj.get(S_SP_SUBTYPE)
        if a is not None:
            # hack subjectType 3/4: convert string to list
            if isinstance(a, basestring):
                a = [a]
                self._jsobj[S_SP_SUBTYPE] = a
            if type in a:
                a.remove(type)

    def size(self):
        return len(self._objs)

    def items(self):
        ret = []
        for jsKV in self._objs:
            ret.append(KValue(jsKV))
        return ret

    def values(self):
        ret = []
        for jsKV in self._objs:
            ret.append(jsKV.get(S_SPO_VALUE, u""))
        return ret

    def append(self, value):
        u"添加字符串时，自动封装为KValue"
        if isinstance(value, basestring):
            value = KValue._fromText(value)

        assert isinstance(value, KValue)
        self._objs.append(value._toJson())

    def index(self, value):
        u"查找第一个出现的位置，未找到时返回-1。查找字符串时，自动封装为KValue。"
        if isinstance(value, basestring):
            value = KValue._fromText(value)

        assert isinstance(value, KValue)
        index = 0
        for kv in self.items():
            if value.equals(kv):
                return index
            index += 1
        return -1

    def remove(self, value):
        u"移除字符串时，自动封装为KValue"
        if isinstance(value, basestring):
            value = KValue._fromText(value)

        assert isinstance(value, KValue)
        for kv in self.items():
            if value.equals(kv):
                self._objs.remove(kv._toJson())

    def equals(self, right):
        u"要求属性名和items相等"
        if not isinstance(right, Spo): return False
        if self.p() != right.p(): return False
        a1 = self.items()
        a2 = right.items()
        if len(a1) != len(a2): return False
        for i in xrange(len(a1)):
            if not a1[i].equals(a2[i]): return False
        return True

    def hash(self, withMeta2=False):
        # TODO: 改为跨语言一致性序列化
        obj = { S_SPO_OBJECT : self._jsobj.get(S_SPO_OBJECT, []) }
        if withMeta2 is True:
            obj[S_SPO_FROM_URL] = self.m(S_SPO_FROM_URL)
            obj[S_SPO_FROM_TYPE] = self.m(S_SPO_FROM_TYPE)
        s = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return self._hash(s)

    def match(self, filter):
        # filter是json风格的MetaSPO过滤器
        Entity = entity.Entity
        assert isinstance(filter, dict)

        self._ensureMetaSPO()
        meta = self._metaSPO._toJson()

        # subjectType处理
        subtype = filter.get(S_SP_SUBTYPE)
        if subtype is not None: 
            filter = dict(filter)               # 保护传入的参数
            del filter[S_SP_SUBTYPE]            # for MetaSPO process
            if subtype and subtype[0] == "!":
                if subtype[1:] in self.subjectType():
                    return False
            else:
                if subtype not in self.subjectType():
                    return False

        # MetaSPO处理
        for key in filter:
            value = filter[key]
            if value and value[0] == "!":
                if meta.get(key) == value[1:]:
                    return False
            else:
                if meta.get(key) != value:
                    return False

        return True
        
    #
    # meta操作
    #
    def m(self, name, value=None):
        u"快速读写系统预置的单例MetaSPO上的字段"
        self._ensureMetaSPO()
        if value is None:
            return self._metaSPO.get(name)
        else:
            self._metaSPO.set(name, value)

    def appendMeta(self, meta):
        assert isinstance(meta, Meta)
        self._ensureMeta()
        self._meta.append(meta._toJson())

    def removeMeta(self, meta):
        assert isinstance(meta, Meta)
        for item in self.meta():
            if meta.equals(item):
                self._meta.remove(item._toJson())

    def meta(self, type=None):
        self._ensureMeta()
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

    #
    # 属性上的属性
    #
    def attr(self, name, value=None):
        u"值类型约束为文本"
        # 系统保留字段不允许访问
        if name in DICT_SP_SYSTEM_FIELD:
            raise Exception("Error: '%s' is a system field" % name)

        if value is None:
            return self._jsobj.get(name, u"")
        else:
            assert isinstance(value, basestring)
            self._jsobj[name] = value

    def attrs(self):
        u"返回元组(string, string)的数组"
        a = []
        jsobj = self._jsobj
        for key in jsobj:
            if key in DICT_SP_SYSTEM_FIELD: continue
            a.append((key, jsobj[key]))
        return a

    def removeAttr(self, name):
        # 系统保留字段不允许访问
        if name in DICT_SP_SYSTEM_FIELD:
            raise Exception("Error: '%s' is a system field" % name)
        
        if name in self._jsobj:
            del self._jsobj[name]

    #
    # 内部实现
    #
    def _toJson(self):
        return self._jsobj

    def _ensureOneKV(self):
        if len(self._objs) == 0:
            # create TEXT object
            kv = KValue("")
            self._objs.append(kv._toJson())

    def _ensureMeta(self):
        if self._meta is not None: return

        if S_SPO_META not in self._jsobj:
            meta = []
            self._jsobj[S_SPO_META] = meta
        else:
            meta = self._jsobj[S_SPO_META]
        self._meta = meta                    # meta包含了所有元数据

    def _ensureMetaSPO(self):
        if self._metaSPO is not None: return

        self._ensureMeta()
        target = None
        for jsMeta in self._meta:
            if jsMeta.get(S_SPO_TYPE) == S_SPO_METASPO:
                target = Meta(jsMeta)
                break

        if target is None:
            target = Meta(S_SPO_METASPO)
            self.appendMeta(target)
        self._metaSPO = target
            
    def _time(self):
        return str(int(time.time()))

    def _hash(self, s):            
        u"获取一个str类型字符串的md5摘要，长度32的hex格式"
        if type(s) == unicode:
            s = s.encode("utf-8")
        return md5.new(s).hexdigest()
