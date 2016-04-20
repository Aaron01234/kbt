# coding=utf-8

u"""
    KB-JSON 1.0解析器

    可参考本文件，从kbt.Parser基类派生实现任意的解析器插件，放置到parsers目录中生效。

    用户使用解析器插件的方式：
    Entity.fromParser(text, parserName)
    其中parserName是解析器的name方法返回值。

    注：Entity.fromKbjson1(text) <=> Entity.fromParser(text, "V1")
"""

import sys
import json
import kbt

S_ID = "ID"
S_AVP = "AVP_LIST"
S_ATTR = "ATTRIBUTE"
S_VALUE = "VALUE"
S_REFER = "REFER"
S_LITERAL = "LITERAL"
S_SVALUE = "SVALUE"
S_VALUE_TYPE = "VALUE_TYPE"
S_SVALUE_META_TYPE = "StructuredValue"
S_META_AVP = "MetaAVP"
S_ATTR_TYPE = "type"


class KbjsonV1Parser(kbt.Parser):
    
    def name(self):
        return "v1"

    def parse(self, text):
        jsobj = json.loads(text)
        o = kbt.Entity()
        
        # id
        id = jsobj.get(S_ID)
        if id is not None: o.id(id)

        # spo
        avps = jsobj.get(S_AVP)
        if avps:
            for avp in avps:
                # name
                name = avp.get(S_ATTR)
                if not name: continue

                # type
                if name == S_ATTR_TYPE:
                    o.addType(avp.get(S_VALUE))
                    continue

                # value and @type
                value = avp.get(S_VALUE, "")
                vtype = avp.get(S_VALUE_TYPE)
                if vtype is None: continue
                if vtype == S_LITERAL:
                    kv = value
                elif vtype == S_SVALUE:
                    kv = kbt.KValue()
                    kv.type(S_SVALUE_META_TYPE)
                    for k, v in value.items():
                        kv.set(k, v)
                else:
                    print >> sys.stderr, "Warn: unknown VALUE_TYPE '%s'" % vtype
                    continue
                spo = o.createSpo(name, kv)
                o.add(spo)

                # refer
                refer = avp.get(S_REFER)
                if refer is not None:
                    spo.r(refer)

                # meta
                metaAVP = None
                for key in avp:
                    if _mapper.has_key(key):
                        # ignore or map to MetaSPO
                        action = _mapper[key]
                        if action is None: continue
                        field, mapper = action
                        if mapper is None:
                            spo.m(field, avp[key])
                        else:
                            spo.m(field, mapper(avp[key]))
                    else:
                        # map to MetaAVP
                        if metaAVP is None:
                            metaAVP = kbt.Meta(S_META_AVP)
                            spo.appendMeta(metaAVP)
                        value = avp[key]
                        kv = None
                        if isinstance(value, dict):
                            kv = kbt.KValue()
                            kv.type(S_SVALUE_META_TYPE)
                            for k, v in value.items():
                                kv.set(k, v)
                        elif isinstance(value, basestring):
                            kv = value
                        else:
                            print >> sys.stderr, "Warn: bad value in AVP: '%s = %s'" % (key, value)
                            continue
                        metaAVP.set(key, kv)

        return o
                    

#
# 映射函数所用词典（源中缺少CLEANSE和FEED）
#
_d_fromType = {
    "PUSH" : kbt.Entity.META_FROM_TYPE_PUSH,   
    "STRUCTURE_EXTRACT" : kbt.Entity.META_FROM_TYPE_EXTRACT,  
    "SEMISTRUCTURE_EXTRACT" : kbt.Entity.META_FROM_TYPE_EXTRACT,  
    "UNSTRUCTURE_EXTRACT" : kbt.Entity.META_FROM_TYPE_EXTRACT,  
    "INFERENCE" : kbt.Entity.META_FROM_TYPE_INFERENCE,  
    "MINING" : kbt.Entity.META_FROM_TYPE_MINING,  
    "MANUAL_INTERVENTION" : kbt.Entity.META_FROM_TYPE_INTERVENE,   
}


#
# 自定义映射函数
#
def mapFromType(v):
    ret = _d_fromType.get(v)
    if ret is None:
        print >> sys.stderr, "Warn: unknow from type: '%s'" % v
        return ""
    return ret



# AVP中的字段映射词典，key为原字段名，value为新字段名+转换映射函数
# 默认映射到MetaSPO中的特定字段，若提供了自定义映射函数则以待映射值为参数调用
# 未覆盖字段，统一放置到新建的MetaAVP中
# value=None的字段将被忽略

_mapper = {
    S_ATTR : None,
    S_VALUE : None,
    S_REFER : None,
    S_VALUE_TYPE : None,
    "CONFIDENCE" : ("confidence", None),
    "FROM_TYPE" : ("fromType", mapFromType),
    "FROM_URL" : ("fromUrl", None),
    "VALUE_LANG" : ("lang", None),
    "TIME_GENERATE" : ("timeGenerate", None),
    "TIME_EXPIRE" : ("timeExpire", None),

    # 已知扩展字段
    "VIEW_ID" : ("viewId", None),
}
