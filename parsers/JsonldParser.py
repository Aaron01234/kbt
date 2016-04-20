# coding=utf-8

u"""
    JSON-LD 解析器

    可参考本文件，从kbt.Parser基类派生实现任意的解析器插件，放置到parsers目录中生效。

    用户使用解析器插件的方式：
    Entity.fromParser(text, parserName)
    其中parserName是解析器的name方法返回值。

    注：Entity.fromKbjson1(text) <=> Entity.fromParser(text, "JsonldParser")
"""

import sys
import json
import kbt

S_ID = "@id"
S_TYPE = "@type"
S_VALUE = "@value"
S_SVALUE_META_TYPE = "StructuredValue"
S_TEXT = "bkgss:Text"
S_THING = "Thing"
META_STATUS = "stat"
META_STATUS_DEFAULT = "DEFAULT"

def only_trans_num_to_str(value):
    if type(value) == list:
        result = []
        for i in xrange(len(value)):
            result.append(only_trans_num_to_str(value[i]))
        del value
        return result
    elif type(value) == dict:
        result = {}
        for k,v in value.items():
            result[only_trans_num_to_str(k)] = only_trans_num_to_str(v)
        del value
        return result
    elif type(value) == float:
        return str(value)
    elif type(value) == int:
        return str(value)
    else:
        return value

def get_type(value):
    if value is None:
        return "NONE"
    elif isinstance(value, basestring):
        return "STR"
    elif type(value) == list:
        return "LIST"
    elif type(value) == dict:
        s_id = value.get(S_ID)
        if s_id is not None:
            return "OBJECT_NODE"
        s_value= value.get(S_VALUE)
        if s_value is not None:
            return "VALUE_NODE"
        return "SVALUE_NODE"
    else:
        return "NONE"
        
def get_kv(vtype, value):
    if vtype == "STR":
        kv = value
    elif vtype == "VALUE_NODE":
        kv = kbt.KValue()
        kv.type(S_TEXT)
        for k, v in value.items():
            v = only_trans_num_to_str(v)
            if _mapper.has_key(k):
                kv.set(_mapper[k], v)
            else:
                kv.set(k, v)
    elif vtype == "SVALUE_NODE":
        kv = kbt.KValue()
        kv.type(S_SVALUE_META_TYPE)
        for k, v in value.items():
            v = only_trans_num_to_str(v)
            kv.set(k, v)
    elif vtype == "OBJECT_NODE":
        kv = kbt.KValue()
        kv.type(S_THING)
        for k, v in value.items():
            if k != S_ID:
                v = only_trans_num_to_str(v)
                if _mapper.has_key(k):
                    kv.set(_mapper[k], v)
                else:
                    kv.set(k, v)
    else:
        kv = None
    return kv

class JsonldParser(kbt.Parser):
    
    def name(self):
        return "JsonldParser"

    def parse(self, text):
        jsobj = json.loads(text)
        o = kbt.Entity()
        
        # id
        id = jsobj.get(S_ID)
        if id is not None: o.id(id)

        # spo
        for property in jsobj:
            # filter @id
            if property == S_ID:
                continue

            # @type
            if property == S_TYPE:
                s_type = jsobj.get(S_TYPE)
                if get_type(s_type) == "STR":
                    o.addType(s_type)
                elif get_type(s_type) == "LIST":
                    for i in xrange(len(s_type)):
                        o.addType(s_type[i])
                else:
                    continue
            
            # property
            value = jsobj.get(property)
            value = only_trans_num_to_str(value)
            vtype = get_type(value) 
            if value is None or vtype == "NONE":
                continue
            if vtype == "LIST":
                for i in xrange(len(value)):
                    vtype_tmp = get_type(value[i])
                    kv = get_kv(vtype_tmp, value[i])
                    if kv is None: continue
                    spo = o.createSpo(property, kv)
                    o.add(spo)
                    # refer
                    if vtype_tmp == "OBJECT_NODE":
                        refer = value[i][S_ID]
                        if refer is not None:
                            spo.r(refer)
                    #meta
                    spo.m(META_STATUS, META_STATUS_DEFAULT)

            else:
                kv = get_kv(vtype,value)
                if kv is None: continue
                spo = o.createSpo(property, kv)
                o.add(spo)
                # refer
                if vtype == "OBJECT_NODE":
                    refer = value[S_ID]
                    if refer is not None:
                        spo.r(refer)
                #meta
                spo.m(META_STATUS, META_STATUS_DEFAULT)

        return o
                    
_mapper = {
    S_VALUE : "value",
}
