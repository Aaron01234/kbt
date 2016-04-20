#coding=utf8

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

class NtupleParser(kbt.Parser):
    def name(self):
        return "NtupleParser"

    def parse(self, text):
        if isinstance(text,basestring):
            ntuples = json.loads(text)
        else:
            ntuples = text
        o = kbt.Entity()
        id = ""
        type = ""
        for ntuple in ntuples:
            items = ntuple.split("\t")
            if id == "":
                id = items[0]
            if type == "":
                type = items[1]
            name = items[2]
            value = items[3]
            vtype = items[7]
            ftype = items[5]
            if vtype == S_LITERAL:
                kv = value
            elif vtype == S_SVALUE:
                kv = kbt.KValue()
                kv.type(S_SVALUE_META_TYPE)
                for k,v in json.loads(value).items():
                    if isinstance(v,basestring):
                        kv.set(k,v)
                    else:
                        kv.set(k,json.dumps(v,False,False))
            else:
                print >> sys.stderr, "Warn: unknown VALUE_TYPE '%s'" % vtype
                continue
            spo = o.createSpo(name, kv)
            #meta
            if _mapper.has_key(ftype):
                action = _mapper[key]
                if action is None: continue
                field,mapper = action
                if mapper is None:
                    spo.m(field, ftype)
                else:
                    spo.m(field,mapper[ftype])

            o.add(spo)
        o.id(id)
        o.setType([type])

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
