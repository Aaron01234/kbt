# coding=utf-8

import json
import time
import math
import md5

def dump(o):
    s = o.toKbjson(indent=4, dense=False)
    print s.decode("utf-8")

def dumpSpo(spo):
    dumpView(spo)
    
def dumpView(spo):
    rawdata = spo._toJson()
    s = json.dumps(rawdata, indent=4, ensure_ascii=False)
    print s

def copy(o):
    u"深拷贝实体o"
    return json.loads(json.dumps(o, ensure_ascii=False))

def toJson(o):
    return json.loads(o.toKbjson())

def dictEquals(left, right):
    ltype, rtype = type(left), type(right)
    if ltype != rtype: return False

    if ltype == unicode:
        return left == right
    elif isinstance(left, list):
        if len(left) != len(right): return False
        for i in xrange(len(left)):
            if not dictEquals(left[i], right[i]): return False
    elif isinstance(left, dict):
        if len(left) != len(right): return False
        for lkey, lvalue in left.items():
            rvalue = right.get(lkey)
            if rvalue is None: return False
            if not dictEquals(lvalue, rvalue): return False
    else:
        return left == right

    return True
    
def jsonEquals(left, right):
    u"比较JSON文本的相等性"
    oleft = json.loads(left)
    oright = json.loads(right)
    ret = dictEquals(oleft, oright)

    # for debug print right
    if ret == False:
        o = json.loads(right)
        text = json.dumps(o, ensure_ascii=False, indent=4)
        text = text.encode("utf-8")
        #print text

    return ret

def now():
    return str(int(time.time()))

def sameTime(t1, t2):
    return math.fabs(int(t1) - int(t2)) <= 1

def hash(s):            
    u"获取一个str类型字符串的md5摘要，长度32的hex格式"
    if type(s) == unicode:
        s = s.encode("utf-8")
    return md5.new(s).hexdigest()


if __name__ == "__main__":
    # dictEquals
    assert dictEquals({}, {})
    assert dictEquals({"name" : "123"}, {"name" : "123"})
    assert dictEquals("abc", "abc")
    assert dictEquals(1, 1)
    assert dictEquals([], [])
    assert dictEquals(["str"], ["str"])

    assert not dictEquals({"name" : "123"}, {"name" : "1234"})
    assert dictEquals({"name" : "123", "age" : 22}, {"age" : 22, "name" : "123"})
    
    assert dictEquals([1, 2], [1, 2])
    assert not dictEquals([1, 2], [2, 1])

    print "done"