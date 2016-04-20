# coding=utf-8
import sys

# 字符串配置
S_SPO_OBJECT = "objects"
S_S_ID = "@id"
S_S_CONTEXT = "@context"
S_S_META = "meta"
S_S_RAW_PROPERTY_NAME = "property"
S_S_METAS = "MetaS"
S_SP_SUBTYPE = "subjectType"
S_SPO_TYPE = "@type"
S_SPO_VALUE = "value"
S_SPO_REFER = "refer"
S_SPO_META = "meta"
S_SPO_METASPO = "MetaSPO"
S_SPO_METAAVP = "MetaAVP"
S_SPO_FROM_URL = "fromUrl"
S_SPO_FROM_TYPE = "fromType"
S_CLASS_TEXT = "bkgss:Text"
S_FILTER_EXP = "exp"

DICT_SP_SYSTEM_FIELD = set([S_SPO_META, S_SP_SUBTYPE, S_SPO_OBJECT])


class KValue(object):

    u"""
        KValue代表Spo类中o的值封装
        封装前：string、dict、list
        封装后：string、KValue、KValueArray
    """

    def __init__(self, jsonValue=None):
        u"jsonValue可以是None、字符串或词典，数组请用KValue.create()创建"
        jsobj = KValue._createRaw(jsonValue)
        if isinstance(jsobj, list):
            raise Exception("can't construct KValue directly from array, try use factory 'KValue.create([...])'")
        self._jsobj = jsobj

    @staticmethod
    def create(value=None):
        u"value可以是None、字符串、数组或词典"
        jsobj = KValue._createRaw(value)
        if isinstance(jsobj, list):
            return KValueArray(jsobj)
        else:
            return KValue(jsobj)

    @staticmethod
    def _createRaw(jsobj=None):
        u"根据除数字以外的Json值创建KValue对象"
        if jsobj is None:
            return {}
        elif isinstance(jsobj, basestring):
            return {S_SPO_VALUE : jsobj, S_SPO_TYPE : S_CLASS_TEXT}
        elif isinstance(jsobj, dict):
            # 检查@type="Text"以避免常见错误
            if S_SPO_TYPE in jsobj:
                v = jsobj[S_SPO_TYPE]
                if isinstance(v, list): v = v[0]
                if not isinstance(v, basestring) or v.lower() == "text":
                    raise Exception("'@type' should be %s instead of %s" % (S_CLASS_TEXT, v))
            return jsobj
        elif isinstance(jsobj, list):
            return jsobj
        else:
            raise Exception("can't create KValue from '%s'" % jsobj)

    @staticmethod
    def _fromText(text):
        assert isinstance(text, basestring)
        kv = KValue(text)
        return kv

    #
    # 对象操作
    #
    def get(self, name):
        # convert Json to KValue automatically
        return self._wrap(self._jsobj.get(name, u""))

    def set(self, name, value):
        # convert KValue to Json automatically
        # 不会对value深拷贝
        self._jsobj[name] = self._unwrap(value)
        return self

    def hasKey(self, name):
        return name in self._jsobj

    def remove(self, name):
        if name in self._jsobj:
            del self._jsobj[name]

    def type(self, type=None):
        # 获取时返回单值（数组取第一个），设置时参数为单值（整个属性替换为单值）
        if type is None:
            t = self._jsobj.get(S_SPO_TYPE, u"")
            if isinstance(t, list): t = t[0]            # 兼容单值和数组
            return t
        else:
            # TODO: 检查是否有更多的类似处理
            # 把text处理为bkgss:Text等做处理
            assert isinstance(type, basestring)
            if type.lower() == "text": type = S_CLASS_TEXT
            self._jsobj[S_SPO_TYPE] = type
            return self

    def types(self, types=None):
        # 获取时返回数组，设置时参数为数组
        if types is None:
            t = self._jsobj.get(S_SPO_TYPE, u"")
            if not t: return []
            if isinstance(t, basestring): t = [t]
            return t
        else:
            # TODO: 检查是否有更多的类似处理
            # 把text处理为bkgss:Text等做处理
            assert isinstance(types, list)
            for i in xrange(len(types)):
                if types[i].lower() == "text": types[i] = S_CLASS_TEXT
            self._jsobj[S_SPO_TYPE] = types
            return self

    def items(self):
        # convert Json to KValue automatically
        a = []
        for key, value in self._jsobj.items():
            a.append((key, self._wrap(value)))
        return a

    def nodes(self):
        u"遍历所有节点，以数组返回"
        return self.flat(leaf=False, type=False)

    def flat(self, a=None, prefix="", leaf=True, type=False):
        u"遍历所有叶子节点，以数组返回"
        if a is None: a = []
        if leaf and self.isObject() and self._jsobj.get(S_SPO_TYPE) == S_CLASS_TEXT:
            # 此分支是一个优化，对于单层数据快速返回结果
            #a.extend(self._jsobj.items())
            if type is False:
                if prefix:
                    a.append((prefix + ".value", self._jsobj.get("value")))
                else:
                    a.append(("value", self._jsobj.get("value")))
            else:
                if prefix:
                    a.append((prefix + ".value", self._jsobj.get("value"), S_CLASS_TEXT))
                else:
                    a.append(("value", self._jsobj.get("value"), S_CLASS_TEXT))
        else:
            # 正常分支
            if type is False:
                self._flat(self, a, prefix, leaf)
            else:
                self._flatWithType(self, a, prefix, leaf)
        return a

    def _flat(self, kv, a, prefix, leaf):
        if type(kv) in (str, unicode):
            a.append((prefix, kv))
        elif kv.isObject():
            if not leaf: a.append((prefix, kv))
            for key, value in kv.items():
                if leaf and key[0] == "@": continue
                cp = "%s%s%s" % (prefix, "." if prefix else "", key)
                self._flat(value, a, cp, leaf)
        elif kv.isArray():
            for child in kv:
                self._flat(child, a, prefix, leaf)

    def _flatWithType(self, kv, a, prefix, leaf, ntype=""):
        if type(kv) in (str, unicode):
            a.append((prefix, kv, ntype))
        elif kv.isObject():
            if not leaf: a.append((prefix, kv, ntype))
            ntype = kv._jsobj.get(S_SPO_TYPE, "")
            for key, value in kv.items():
                if leaf and key[0] == "@": continue
                cp = "%s%s%s" % (prefix, "." if prefix else "", key)
                self._flatWithType(value, a, cp, leaf, ntype)
        elif kv.isArray():
            for child in kv:
                self._flatWithType(child, a, prefix, leaf, "")

    def __iter__(self):
        for key, value in self._jsobj.items():
            yield (key, self._wrap(value))

    def size(self):
        return len(self._jsobj)

    def equals(self, other):
        u"值语义比较"
        # KValue代表了值，因此不按照引用进行相等比较
        # 假定字段值中只能是字符串或嵌套KValue
        if not isinstance(other, KValue): return False
        o1, o2 = self._jsobj, other._jsobj
        if len(o1) != len(o2): return False
        return _jsonValueEquals(o1, o2)
        #for key in o1:
        #    value = o1[key]
        #    if isinstance(value, basestring):
        #        if value != o2.get(key): return False
        #    elif isinstance(value, dict):
        #        if not KValue(value).equals(KValue(o2.get(key))): return False
        #    elif isinstance(value, list):
        #        if not KValueArray(value).equals(KValueArray(o2.get(key))): return False
        #    else:
        #        raise Exception("KValue should only contains Text or KValue")

        #return True

    #
    # 类型信息
    #
    def isArray(self):
        return False

    def isObject(self):
        return True

    #
    # O上meta操作
    #
    def m(self, name, value=None):
        # 快捷读写KValue中类型为MetaS的meta上的字段
        a = self._jsobj.get(S_S_META)
        if a is None:
            a = []
            self._jsobj[S_S_META] = a
        assert isinstance(a, list)

        if value is None:
            for meta in a:
                if meta.get(S_SPO_TYPE) == S_S_METAS:
                    return meta.get(name, u"")
            return u""
        else:
            assert isinstance(value, basestring)
            target = None
            for meta in a:
                if meta.get(S_SPO_TYPE) == S_S_METAS:
                    target = meta
                    break
            if target is None:
                target = Meta(S_S_METAS)._toJson()
                a.append(target)
            target[name] = value
            return self

    #
    # 内部实现
    #
    def _toJson(self):
        return self._jsobj

    def _wrap(self, v):
        # json => KValue
        if isinstance(v, basestring):
            return v
        elif isinstance(v, dict):
            return KValue(v)
        elif isinstance(v, list):
            return KValueArray(v)
        else:
            assert False

    def _unwrap(self, v):
        # KValue => json
        if isinstance(v, KValue):       # KValue和KValueArray的处理方式相同
            return v._jsobj
        #assert not isinstance(v, float) and not isinstance(v, int)
        if isinstance(v, float) or isinstance(v, int):
            return str(v)
        return v


class KValueArray(KValue):
    
    u"封装string或KValue组成的数组，KValueArray本身也是一个KValue"

    def __init__(self, jsobj=[]):
        u"内部调用，仅接受数组参数"
        assert isinstance(jsobj, list)
        self._jsobj = jsobj

    def isArray(self):
        return True
    
    def isObject(self):
        return False

    #
    # 数组操作，借用部分基类方法
    #
    def __getitem__(self, i):
        return self._wrap(self._jsobj[i])

    def __setitem__(self, i, v):
        # 不会对v深拷贝
        v = self._unwrap(v)
        self._jsobj[i] = v
    
    def append(self, v):
        v = self._unwrap(v)
        self._jsobj.append(v)

    def index(self, v):
        # 使用python数组提供的值比较语义
        v = self._unwrap(v)
        try:
            return self._jsobj.index(v)
        except ValueError:
            return -1
    
    def remove(self, v):
        # 使用python词典提供的值比较语义
        v = self._unwrap(v)
        self._jsobj.remove(v)

    def __iter__(self):
        for jsobj in self._jsobj:
            yield self._wrap(jsobj)

    def size(self):
        return len(self._jsobj)

    def items(self):
        ret = []
        for jsobj in self._jsobj:
            ret.append(self._wrap(jsobj))
        return ret

    #
    # 未实现的对象操作
    #
    def get(self, name):
        raise NotImplementedError("invalid operation on array")

    def set(self, name, value):
        raise NotImplementedError("invalid operation on array")

    def type(self, type=None):
        raise NotImplementedError("invalid operation on array")

    def equals(self):
        raise NotImplementedError("invalid operation on array")

    def _toJson(self):
        raise NotImplementedError("invalid operation on array")

    def m(self, name, value):
        raise NotImplementedError("invalid operation on array")


class Meta(KValue):
    
    # 从KValue基础get、set、remove和type四个方法

    def __init__(self, typeOrJson):
        u"可以从type或者JsonObject构造出KValue"
        # 创建Meta时，应总是提供其类型，但这里并未检测json对象内部
        if isinstance(typeOrJson, dict):
            # 内部接口，用于从KB-JSON解析
            rawdata = typeOrJson
            super(Meta, self).__init__(rawdata)
        elif isinstance(typeOrJson, basestring):
            super(Meta, self).__init__()
            self.set(S_SPO_TYPE, typeOrJson)
        else:
            raise Exception("type must be a string")

    #@staticmethod
    #def fromJsonObject(jsobj):
    #    u"假定类型字段为@type"
    #    if not isinstance(jsobj, dict):
    #        raise Exception("fromJsonObject need a 'JsonObject' value")
    #    # Meta不用检查@type="Text"
    #    return Meta(jsobj)



class Parser(object):

    _dic_parser = {}
    
    def parse(self, text):
        u"从文本解析出Entity对象"
        raise NotImplementedError("please override this method in subclass")

    def name(self):
        u"设定parser的名称，若缺省使用文件名（不含扩展名）"
        pass

    @staticmethod
    def add(name, parser):
        assert isinstance(parser, Parser)
        if name in Parser._dic_parser:
            raise Exception("parser name already exist: %s" % name)
        Parser._dic_parser[name] = parser

    @staticmethod
    def get(name):
        return Parser._dic_parser.get(name)

    @staticmethod
    def items():
        return Parser._dic_parser.items()



#
# 共用内部函数
#
def _jsonValueEquals(left, right):
    if isinstance(left, basestring):
        return left == right
    elif isinstance(left, list):
        if len(left) != len(right): return False
        for i in xrange(len(left)):
            if not _jsonValueEquals(left[i], right[i]): return False
    elif isinstance(left, dict):
        if len(left) != len(right): return False
        for lkey, lvalue in left.items():
            rvalue = right.get(lkey)
            if rvalue is None: return False
            if not _jsonValueEquals(lvalue, rvalue): return False
    else:
        return left == right

    return True
