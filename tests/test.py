# coding=utf-8

import sys
import unittest
# always use absolute import in module '__main__'
sys.path.append("..")
import kbt
sys.path.remove("..")
from kbt import Entity, Spo, Config
from kbt.data import *
from kbt.testtools import *

class EntityOpTest(unittest.TestCase):

    #
    # 实体操作
    #
    def test_create(self):
        o = Entity()
        self.assertEqual(32, len(o.id()))       # 自动创建GUID
        o = Entity("")
        self.assertEqual("", o.id())            # 不创建
        self.assertEqual("{}", o.toString())    # 空ID序列化时删除字段
        o = Entity("123")
        self.assertEqual("123", o.id())
        self.assertEqual('{"@id": "123"}', o.toString())

    def test_fromKbjson(self):
        # 最基础case，解析实体，检查类型、大小、上下文和ID
        o = Entity.fromKbjson(EntityTest.Sample_Small)
        self.assertEqual("Person", o.type()[0])
        self.assertEqual(3, o.size())
        self.assertEqual("http://kg.baidu.com/sample_context.jsonld", o.context())
        self.assertEqual("http://userbase.kgs.baidu.com/somename/liudehua", o.id())

    def test_fromKbjsonObject(self):
        jsobj = json.loads(EntityTest.Sample_Small)
        o = Entity.fromKbjsonObject(jsobj)
        self.assertEqual("Person", o.type()[0])
        self.assertEqual(3, o.size())
        self.assertEqual("http://kg.baidu.com/sample_context.jsonld", o.context())
        self.assertEqual("http://userbase.kgs.baidu.com/somename/liudehua", o.id())

    def test_fromKbjson_array_hack(self):
        # 允许KB-JSON中，实体的type和属性的subjectType为字符串或数组，两者统一转换为数组
        o = Entity.fromKbjson(EntityTest.Sample_Subject_Type)
        attr = o.get("name")
        spo = attr[0]
        self.assertEqual("Person", spo.subjectType()[0])
        spo.addSubjectType("Actor")
        self.assertEqual(2, len(spo.subjectType()))
        spo = attr[1]
        self.assertEqual("Singer", spo.subjectType()[0])

        o = Entity.fromKbjson(EntityTest.Sample_Subject_Type)
        attr = o.get("name")
        spo = attr[0]
        spo.removeSubjectType("Person")
        self.assertEqual(0, len(spo.subjectType()))

    def test_fromKbjson_min(self):
        o = Entity.fromKbjson(EntityTest.Sample_Min)
        self.assertEqual("Person", o.type()[0])
        self.assertEqual(1, o.size())
        self.assertEqual("", o.context())
        self.assertEqual("", o.id())

    def test_fromKbjson_jsonld(self):
        # JSON-LD的兼容性，在单元素无序集合的表达上，兼容JSON-LD的两种写法
        o = Entity.fromKbjson(EntityTest.Sample_Jsonld_Array)
        self.assertRaises(Exception, lambda : o.toString())
        o = Entity.fromKbjson(EntityTest.Sample_Jsonld_Array, jsonldFormat=True)
        self.assertIsNotNone(o.toString())

        o = Entity.fromKbjson(EntityTest.Sample_KValue_Meta_Array)
        self.assertRaises(AssertionError, lambda : o.geto("friend")[0].m(Entity.META_LOCAL_REFER))
        o = Entity.fromKbjson(EntityTest.Sample_KValue_Meta_Array, jsonldFormat=True)
        self.assertIsNotNone(o.toString())
        
        o = Entity.fromKbjson(EntityTest.Sample_KValue_Meta_Nest_Array)
        self.assertRaises(AssertionError, lambda : o.geto("friend")[0].m(Entity.META_LOCAL_REFER))
        o = Entity.fromKbjson(EntityTest.Sample_KValue_Meta_Nest_Array, jsonldFormat=True)
        self.assertIsNotNone(o.toString())

    def test_fromKbjson_empty(self):
        o = Entity.fromKbjson(EntityTest.Sample_Empty)
        self.assertRaises(IndexError, lambda : o.type()[0])
        self.assertEqual(0, o.size())
        self.assertEqual("", o.context())
        self.assertEqual("", o.id())

    def test_toString(self):
        self.assertTrue(jsonEquals(EntityTest.Sample_Empty, Entity.fromKbjson(EntityTest.Sample_Empty).toString(dense=False)))
        self.assertTrue(jsonEquals(EntityTest.Sample_Min, Entity.fromKbjson(EntityTest.Sample_Min).toString(dense=False)))
        self.assertTrue(jsonEquals(EntityTest.Sample_Small, Entity.fromKbjson(EntityTest.Sample_Small).toString(dense=False)))
        self.assertTrue(jsonEquals(EntityTest.Sample_Normal, Entity.fromKbjson(EntityTest.Sample_Normal).toString(dense=False)))
        self.assertTrue(jsonEquals(EntityTest.Sample_Meta, Entity.fromKbjson(EntityTest.Sample_Meta).toString(dense=False)))
        self.assertTrue(jsonEquals(EntityTest.Sample_RawProperty, Entity.fromKbjson(EntityTest.Sample_RawProperty).toString(dense=False)))
        self.assertTrue(jsonEquals(EntityTest.Sample_Nest_KValue, Entity.fromKbjson(EntityTest.Sample_Nest_KValue).toString(dense=False)))

    def test_toKbjsonObject(self):
        self.assertTrue(jsonEquals(EntityTest.Sample_Empty, Entity.fromKbjson(EntityTest.Sample_Empty).toString(dense=False)))
        self.assertTrue(dictEquals(json.loads(EntityTest.Sample_Normal), Entity.fromKbjson(EntityTest.Sample_Normal).toKbjsonObject(dense=False)))

    def test_toKbjson_sort(self):
        o = Entity.fromKbjson(EntityTest.Sample_Small)
        text = o.toString(indent=4, sort=True, encoding="utf-8")
        self.assertEqual(text, EntityTest.Sample_Small_Sort)

    #def test(self):
    #    #path = ur"D:\Down\CRT\3"
    #    #s = open(path).read().decode("utf-8")
    #    #o = Entity.fromKbjson(s, jsonldFormat=True)
    #    o = Entity()
    #    spo = o.createSpo("name", "xx")
    #    o.add(spo)
    #    print o.toString()

    def test_toKbjson_remove_empty(self):
        # subjectType
        o = Entity()
        spo = o.createSpo("name", "")
        o.add(spo)
        spo.addSubjectType("Person")
        spo.removeSubjectType("Person")
        self.assertFalse(jsonEquals(o.toString(dense=False), o.toString(dense=True)))

        o = Entity.fromKbjson(EntityTest.Sample_Empty_Subject_Type1)
        self.assertTrue(jsonEquals(EntityTest.Sample_Empty_Subject_Type1, o.toString(dense=False)))
        self.assertFalse(jsonEquals(EntityTest.Sample_Empty_Subject_Type1, o.toString(dense=True)))

        o = Entity.fromKbjson(EntityTest.Sample_Empty_Subject_Type2)
        self.assertTrue(jsonEquals(EntityTest.Sample_Empty_Subject_Type2, o.toString(dense=False)))
        self.assertFalse(jsonEquals(EntityTest.Sample_Empty_Subject_Type2, o.toString(dense=True)))

        # empty property
        o = Entity.fromKbjson(EntityTest.Sample_Empty_Property)
        self.assertTrue(jsonEquals(EntityTest.Sample_Empty_Property, o.toString(dense=False)))
        self.assertFalse(jsonEquals(EntityTest.Sample_Empty_Property, o.toString(dense=True)))

        # empty SPO meta
        o = Entity.fromKbjson(EntityTest.Sample_Empty_SPO_META)
        self.assertTrue(jsonEquals(EntityTest.Sample_Empty_SPO_META, o.toString(dense=False)))
        self.assertFalse(jsonEquals(EntityTest.Sample_Empty_SPO_META, o.toString(dense=True)))
        
        # empty SPO objects
        o = Entity.fromKbjson(EntityTest.Sample_Empty_SPO_OBJ)
        self.assertTrue(jsonEquals(EntityTest.Sample_Empty_SPO_OBJ, o.toString(dense=False)))
        self.assertFalse(jsonEquals(EntityTest.Sample_Empty_SPO_OBJ, o.toString(dense=True)))

    def test_hasType(self):
        o = Entity.fromKbjson(EntityTest.Sample_Small)
        self.assertTrue(o.hasType("Person"))
        self.assertTrue(o.hasType("Actor"))
        self.assertFalse(o.hasType("Movie"))

    def test_type_array_hack(self):
        o = Entity.fromKbjson(EntityTest.Sample_Single_Type)
        self.assertTrue(o.hasType("Person"))
        self.assertFalse(o.hasType("Actor"))
        o.addType("Actor")
        self.assertTrue(o.hasType("Actor"))

        o = Entity.fromKbjson(EntityTest.Sample_Single_Type)
        o.removeType("Actor")
        o.removeType("Person")
        self.assertFalse(o.hasType("Person"))

    def test_addType(self):
        o = Entity.fromKbjson(EntityTest.Sample_Small)
        self.assertFalse(o.hasType("Movie"))
        o.addType("Movie")
        self.assertTrue(o.hasType("Movie"))

    def test_setType(self):
        o = Entity.fromKbjson(EntityTest.Sample_Small)
        self.assertTrue(o.hasType("Person"))
        o.setType(["Movie", "Thing"])
        self.assertFalse(o.hasType("Person"))
        self.assertTrue(o.hasType("Movie"))
        

    def test_removeType(self):
        o = Entity.fromKbjson(EntityTest.Sample_Small)
        self.assertTrue(o.hasType("Actor"))
        o.removeType("actor")
        self.assertTrue(o.hasType("Actor"))
        o.removeType("Actor")
        self.assertFalse(o.hasType("Actor"))

        o = Entity.fromKbjson(EntityTest.Sample_Normal)
        #self.assertRaises(Exception, lambda : o.removeType("Singer"))
        o.removeType("Singer")
        self.assertFalse(o.hasType("Singer"))
        o.removeType("xxx")

    def test_type(self):
        o = Entity.fromKbjson(EntityTest.Sample_Small)
        self.assertEqual(("Person", "Singer", "Actor"), tuple(o.type()))

    def test_name(self):
        o = Entity.fromKbjson(EntityTest.Sample_Small)
        self.assertEqual(u"刘德华", o.name())
        self.assertEqual(u"刘德华", o.getv("name")[0])
        #o.name("")
        #self.assertEqual(u"", o.name())
        #o.name(u"Andy")
        #self.assertEqual(u"Andy", o.name())
        #self.assertEqual(u"Andy", o.getv("name")[0])

        o = Entity()
        self.assertEqual(u"", o.name())
        #o.name(u"Andy")
        #self.assertEqual(u"Andy", o.name())
        #self.assertEqual(u"Andy", o.getv("name")[0])

    def test_toTriple(self):
        s = Entity.fromKbjson(EntityTest.Sample_Normal).toTriple()
        self.assertEqual(EntityTest.Sample_Normal_Size, len(s.split("\n")))

    def test_fromKbjson1(self):
        o = Entity.fromKbjson1(EntityTest.Sample_Kbjson1_Small)
        #dump(o)
        self.assertEqual("68", o.getv("weight")[0])
        self.assertEqual(u"刘德华", o.getv("name")[0])
        spo = o.get("name")[0]
        self.assertEqual(S_CLASS_TEXT, spo.o().type())
        self.assertEqual(Entity.META_FROM_TYPE_PUSH, spo.m(Entity.META_FROM_TYPE))


class PropertyOpTest(unittest.TestCase):
    #
    # 属性创建
    #
    #def test_createSpo(self):
    #    # 已废弃接口
    #    o = Entity()
    #    t = now()
    #    spo = o.createSpo("name", u"刘德华", Entity.META_STATUS_RAW, Entity.META_FROM_TYPE_INTERVENE)
    #    self.assertEqual("name", spo.p())
    #    self.assertEqual(u"刘德华", spo.v())
    #    self.assertEqual("", spo.r())
    #    self.assertEqual(Entity.META_STATUS_RAW, spo.m(Entity.META_STATUS))
    #    self.assertEqual(Entity.META_FROM_TYPE_INTERVENE, spo.m(Entity.META_FROM_TYPE))

    #    # auto set create time
    #    self.assertTrue(sameTime(t, spo.m(Entity.META_CREATE_TIME)))

    #    # multi-value create
    #    spo = o.createSpo("name", [u"刘德华", u"华仔"], Entity.META_STATUS_RAW, Entity.META_FROM_TYPE_INTERVENE)
    #    self.assertEqual("name", spo.p())
    #    self.assertEqual(u"刘德华", spo.v())
    #    self.assertEqual(u"华仔", spo.values()[1])
    #    self.assertEqual(Entity.META_STATUS_RAW, spo.m(Entity.META_STATUS))
    #    spo2 = o.createSpo("name", [KValue(u"刘德华"), u"华仔"], Entity.META_STATUS_RAW, Entity.META_FROM_TYPE_INTERVENE)
    #    self.assertTrue(spo.equals(spo2))

    def test_addSpo(self):
        o = Entity()
        t = now()
        spo = o.addSpo("name", u"刘德华", Entity.META_STATUS_RAW, Entity.META_FROM_TYPE_INTERVENE)
        spo2 = o.get("name")[0]
        self.assertEqual(spo.v(), spo2.v())
        self.assertEqual("name", spo.p())
        self.assertEqual(u"刘德华", spo.v())
        self.assertEqual("", spo.r())
        self.assertEqual(Entity.META_STATUS_RAW, spo.m(Entity.META_STATUS))
        self.assertEqual(Entity.META_FROM_TYPE_INTERVENE, spo.m(Entity.META_FROM_TYPE))

        # auto set create time
        self.assertTrue(sameTime(t, spo.m(Entity.META_CREATE_TIME)))

        # multi-value create
        spo = o.addSpo("name", [u"刘德华", u"华仔"], Entity.META_STATUS_RAW, Entity.META_FROM_TYPE_INTERVENE)
        self.assertEqual("name", spo.p())
        self.assertEqual(u"刘德华", spo.v())
        self.assertEqual(u"华仔", spo.values()[1])
        self.assertEqual(Entity.META_STATUS_RAW, spo.m(Entity.META_STATUS))
        spo2 = o.addSpo("name", [KValue(u"刘德华"), u"华仔"], Entity.META_STATUS_RAW, Entity.META_FROM_TYPE_INTERVENE)
        self.assertTrue(spo.equals(spo2))

    def test_add(self):
        o = Entity()
        spo = o.createSpo("name", u"刘德华", Entity.META_STATUS_RAW, Entity.META_FROM_TYPE_INTERVENE)
        o.add(spo)
        self.assertEqual(1, o.size())
        #dump(o)

    #
    # 属性获取
    #
    def test_get(self):
        o = Entity.fromKbjson(EntityTest.Sample_Normal)
        #print o.toTriple()
        spos = o.get("weight")
        self.assertEqual(1, len(spos))
        spo = spos[0]
        self.assertEqual("weight", spo.p())
        self.assertEqual("68", spo.v())

    def test_getx_with_subjectType(self):
        o = Entity.fromKbjson(EntityTest.Sample_Normal)
        # get
        self.assertEqual(2, len(o.get("award")))
        self.assertEqual(1, len(o.get("award", {"subjectType" : "Singer"})))
        self.assertEqual("Singer", o.get("award", {"subjectType" : "Singer"})[0].subjectType()[0])

        # geto
        self.assertEqual(2, len(o.geto("award")))
        self.assertEqual(1, len(o.geto("award", {"subjectType" : "Singer"})))
        self.assertTrue(isinstance(o.geto("award", {"subjectType" : "Singer"})[0], KValue))

        # getv
        self.assertEqual(2, len(o.getv("award")))
        self.assertEqual(1, len(o.getv("award", {"subjectType" : "Singer"})))
        self.assertTrue(isinstance(o.getv("award", {"subjectType" : "Singer"})[0], basestring))

        # tripes
        count = 0
        for spo in o.triples():
            if "Person" in spo.subjectType():
                count += 1
        self.assertEqual(count, len(o.triples({"subjectType" : "Person"})))
        self.assertEqual("Person", o.triples({"subjectType" : "Person"})[0].subjectType()[0])

        # items
        self.assertEqual(1, len(o.items({"subjectType" : "Singer"})))

    def test_getx_with_filter(self):
        o = Entity.fromKbjson(EntityTest.Sample_Normal)
        # get
        self.assertEqual(2, len(o.get("name")))
        self.assertEqual(1, len(o.get("name", Entity.F_NODEL)))

        # geto
        self.assertEqual(2, len(o.geto("name")))
        self.assertEqual(1, len(o.geto("name", Entity.F_IDENTIFIED)))

        # getv
        self.assertEqual(2, len(o.geto("name")))
        self.assertEqual(1, len(o.geto("name", Entity.F_PUSH)))

        # triples
        a = o.triples(Entity.F_NODEL)
        self.assertEqual(o.size() - 1, len(a))

        # items
        count = 0
        for name, spos in o.items(Entity.F_NODEL):
            count += len(spos)
        self.assertEqual(o.size() - 1, count)

        # multi
        a = o.triples({S_SP_SUBTYPE : "Singer", Entity.META_FROM_TYPE : Entity.META_FROM_TYPE_PUSH})
        self.assertEqual(1, len(a))
        a = o.triples({Entity.META_STATUS : "!" + Entity.META_STATUS_MARKDEL, Entity.META_FROM_TYPE : "!" + Entity.META_FROM_TYPE_MINING})
        self.assertEqual(5, len(a))

    def test_combine_filter(self):
        f = dict(Entity.F_NODEL)
        f.update(Entity.F_PUSH)
        o = Entity()
        self.assertTrue(dictEquals(f, o.combineFilter(Entity.F_NODEL, Entity.F_PUSH)))

        
        self.assertTrue(dictEquals({ "subjectType" : "Singer", 
                                     Entity.META_STATUS : "!" + Entity.META_STATUS_MARKDEL }
                                , o.combineFilter(Entity.F_NODEL, {"subjectType" : "Singer"})))

    def test_invert_filter(self):
        o = Entity()
        self.assertTrue(dictEquals(Entity.F_DEL, o.invertFilter(Entity.F_NODEL)))
        self.assertTrue(dictEquals(Entity.F_NODEL, o.invertFilter(Entity.F_DEL)))

    def test_geto(self):
        o = Entity.fromKbjson(EntityTest.Sample_Normal)
        kvs = o.geto("award")
        self.assertEqual(2, len(kvs))

        kv = None
        for item in kvs:
            self.assertIsInstance(item, KValue)
            if item.get(S_SPO_VALUE) == u"无间道":
                kv = item
        self.assertNotEqual(None, kv)
        self.assertEqual("userbase:k/wujiandao", kv.get(S_SPO_REFER))
        self.assertEqual("Movie", kv.get(S_SPO_TYPE))

    def test_getv(self):
        o = Entity.fromKbjson(EntityTest.Sample_Normal)
        vl = o.getv("name")
        self.assertEqual(2, len(vl))
        self.assertTrue(u"刘德华" in vl)
        self.assertTrue(u"刘福荣" in vl)

        age = o.getv("weight")[0]
        self.assertEqual("68", age)
        self.assertNotEqual(68, age)

        xxx = o.getv("notexist")
        self.assertEqual(0, len(xxx))
        self.assertRaises(IndexError, lambda : o.getv("notexist")[0])

    def test_items(self):
        o = Entity.fromKbjson(EntityTest.Sample_Normal)
        attrs = o.items()
        self.assertEqual(EntityTest.Sample_Normal_Attr_Size, len(attrs))
        for name, spos in attrs:
            self.assertIsInstance(spos[0], Spo)

        attrs = o.items({"subjectType" : "Singer"})
        self.assertEqual(1, len(attrs))
        self.assertIsInstance(attrs[0][0], basestring)
        self.assertIsInstance(attrs[0][1][0], Spo)      # Entity => [(name, [Spo])] => [Spo] => Spo

    def test_triples(self):
        o = Entity.fromKbjson(EntityTest.Sample_Normal)
        self.assertEqual(EntityTest.Sample_Normal_Size, len(o.triples()))
        for spo in o.triples():
            self.assertIsInstance(spo, Spo)

        self.assertEqual(1, len(o.triples({"subjectType" : "Singer"})))
        self.assertIsInstance(o.triples({"subjectType" : "Singer"})[0], Spo)

    def test_keys(self):
        o = Entity.fromKbjson(EntityTest.Sample_Normal)
        self.assertTrue("name" in o.keys())
        self.assertEqual(EntityTest.Sample_Normal_Attr_Size, len(o.keys()))

        a1 = []
        for key in o:
            a1.append(key)
        a2 = o.keys()
        a1.sort()
        a2.sort()
        self.assertEqual(json.dumps(a1), json.dumps(a2))

    def test_hasKey(self):
        o = Entity.fromKbjson(EntityTest.Sample_Normal)
        self.assertTrue(o.hasKey("name"))
        self.assertTrue(o.hasKey("weight"))
        self.assertFalse(o.hasKey("name2"))
        self.assertFalse(o.hasKey(""))

    #
    # 属性修改
    #
    def test_remove(self):
        o = Entity()
        #dump(o)
        first = toJson(o)
        spo = o.createSpo("name", u"刘德华", Entity.META_STATUS_RAW, Entity.META_FROM_TYPE_INTERVENE)
        o.add(spo)
        self.assertEqual(1, o.size())
        o.remove(spo)
        self.assertEqual(0, o.size())
        second = toJson(o)
        #dump(o)
        self.assertTrue(dictEquals(first, second))
        
    #
    # raw属性
    #
    def test_getRaw(self):
        o = Entity.fromKbjson(EntityTest.Sample_RawProperty)
        self.assertEqual("RAW_VALUE", o.getRaw("RAW_NAME")[0])
        self.assertEqual(0, len(o.getRaw("notexist")))

    def test_addRaw(self):
        o = Entity()
        o.addRaw("age", "24")
        self.assertEqual("24", o.getRaw("age")[0])

        o = Entity.fromKbjson(EntityTest.Sample_RawProperty)
        self.assertEqual(0, len(o.getRaw("xxx")))
        o.addRaw("xxx", "{some value}")
        self.assertEqual(1, len(o.getRaw("xxx")))
        o.addRaw("xxx", "{some value2}")
        self.assertEqual(2, len(o.getRaw("xxx")))
        self.assertEqual("{some value2}", o.getRaw("xxx")[1])

    def test_removeRaw(self):
        o = Entity.fromKbjson(EntityTest.Sample_RawProperty)
        o.addRaw("xxx", "{some value}")
        o.addRaw("xxx", "{some value}")
        self.assertEqual(2, len(o.getRaw("xxx")))
        o.removeRaw("xxx")
        self.assertEqual(0, len(o.getRaw("xxx")))

        o = Entity.fromKbjson(EntityTest.Sample_RawProperty)
        o.addRaw("xxx", "value1")
        o.addRaw("xxx", "value2")
        self.assertEqual(2, len(o.getRaw("xxx")))
        o.removeRaw("xxx", "value2")
        self.assertEqual(1, len(o.getRaw("xxx")))
        self.assertEqual("value1", o.getRaw("xxx")[0])

    def test_rawItems(self):
        o = Entity.fromKbjson(EntityTest.Sample_RawProperty)
        self.assertEqual(2, len(o.rawItems()))

        o = Entity()
        o.addRaw("name", "xxx")
        o.addRaw("age", "24")
        self.assertEqual(2, len(o.rawItems()))
        self.assertTrue(o.rawItems()[0] in [("name", "xxx"), ("age", "24")])


class MetaOpTest(unittest.TestCase):

    def test_appendMeta(self):
        o = Entity.fromKbjson(EntityTest.Sample_Small)
        meta = Meta("CustomMeta")
        meta.set("version", "1.0")
        self.assertEqual(0, len(o.meta()))
        o.appendMeta(meta)
        self.assertEqual(1, len(o.meta()))
        o.appendMeta(meta)
        self.assertEqual(2, len(o.meta()))

    def test_meta(self):
        o = Entity.fromKbjson(EntityTest.Sample_Meta)
        self.assertEqual(1, len(o.meta()))
        meta = o.meta("CustomMeta")[0]
        self.assertEqual("1.0", meta.get("version"))
        self.assertEqual("CustomMeta", meta.type())

    def test_removeMeta(self):
        o = Entity.fromKbjson(EntityTest.Sample_Meta)
        self.assertEqual(1, len(o.meta()))
        meta = o.meta("CustomMeta")[0]
        o.removeMeta(meta)
        self.assertEqual(0, len(o.meta()))

    def test_m(self):
        o = Entity()
        self.assertEqual("", o.m(Entity.META_FROM_URL))
        o.m(Entity.META_FROM_URL, "http://xxx")
        self.assertEqual("http://xxx", o.m(Entity.META_FROM_URL))


class KValueTest(unittest.TestCase):
    #
    # 创建和读写
    #
    def test_create(self):
        v = KValue()
        self.assertEqual("", v.type())
        
        self.assertRaises(Exception, lambda : KValue(1))
        self.assertRaises(Exception, lambda : KValue(1.2))
        KValue(None)
        KValue("")
        KValue("vvv")
        KValue({"value" : "ddd"})

    def test_get(self):
        v = KValue()
        self.assertEqual("", v.get(S_SPO_OBJECT))
        v.set(S_SPO_OBJECT, "28")
        self.assertEqual("28", v.get(S_SPO_OBJECT))

    def test_has_key(self):
        v = KValue()
        self.assertFalse(v.hasKey("name"))
        v.set("name", "kk")
        self.assertTrue(v.hasKey("name"))

    def test_items(self):
        v = KValue()
        v.set("name", "kk")
        v.set("age", "22")
        self.assertEqual(2, len(v.items()))
        self.assertTrue(v.items()[1][0] in ("name", "age"))
        
        a = []
        for child in v:
            a.append(child)
        self.assertEqual(2, len(a))
        self.assertEqual(2, v.size())
        self.assertEqual(a[0], v.items()[0])
        self.assertEqual(a[1], v.items()[1])

        v = KValue()
        v.set("weight", KValue({"a" : "b"}))
        self.assertIsInstance(v.items()[0][1], KValue)


    def test_set(self):
        v = KValue()
        self.assertRaises(AssertionError, lambda : v.set(S_SPO_OBJECT, 28))      # value should be string
        v2 = KValue()
        v.set(S_SPO_OBJECT, v2)
        self.assertTrue(lambda : v.get(S_SPO_OBJECT) is v2)                      # KValue is a ref object
        v2.set("name", "kk")
        self.assertEqual("kk", v.get(S_SPO_OBJECT).get("name"))

    def test_remove(self):
        v = KValue()
        v.set("name", "kk")
        self.assertEqual("kk", v.get("name"))
        v.remove("name")
        self.assertEqual("", v.get("name"))
        v.set(S_SPO_OBJECT, KValue())
        self.assertNotEqual("", v.get(S_SPO_OBJECT))
        v.remove(S_SPO_OBJECT)
        self.assertEqual("", v.get(S_SPO_OBJECT))

    def test_type(self):
        v = KValue()
        self.assertEqual("", v.type())
        v.type("Person")
        self.assertEqual("Person", v.type())
        self.assertRaises(AssertionError, lambda : v.type(["Person"]))

        o = Entity.fromKbjson(EntityTest.Sample_OType)
        v = o.geto("friend")[0]
        self.assertEqual("EntertainmentPerson", v.type())
        self.assertTrue(jsonEquals(EntityTest.Sample_OType, o.toString()))
        v.type("Person")
        self.assertEqual("Person", v.type())

        # auto rewrite
        v = KValue()
        v.type("Text")
        self.assertEqual(S_CLASS_TEXT, v.type())

    def test_types(self):
        v = KValue()
        self.assertEqual([], v.types())
        v.type("Person")
        self.assertEqual(1, len(v.types()))
        self.assertEqual("Person", v.types()[0])
        v.types(["Person"])
        self.assertEqual(1, len(v.types()))
        self.assertEqual("Person", v.types()[0])

        o = Entity.fromKbjson(EntityTest.Sample_OType)
        v = o.geto("friend")[0]
        self.assertEqual("Person", v.types()[1])
        self.assertTrue(jsonEquals(EntityTest.Sample_OType, o.toString()))
        v.type("Person")
        self.assertEqual(1, len(v.types()))
        self.assertEqual("Person", v.types()[0])
        v.types(["EntertainmentPerson", "Person"])
        self.assertTrue(jsonEquals(EntityTest.Sample_OType, o.toString()))
        
        # auto rewrite
        v = KValue()
        v.types(["Person", "Text"])
        self.assertEqual(S_CLASS_TEXT, v.types()[1])


    def test_nest(self):
        o = Entity.fromKbjson(EntityTest.Sample_Nest_KValue)
        spo = o.get("award")[0]
        kv = spo.o()
        self.assertIsInstance(kv.get("other"), KValue)
        self.assertEqual("2015", kv.get("other").get("year"))
        kv.get("other").set("year", "2000")
        self.assertEqual("2000", kv.get("other").get("year"))

        o = Entity.fromKbjson(o.toString())
        kv = o.get("award")[0].o()
        self.assertEqual("2000", kv.get("other").get("year"))

    def test_equals(self):
        # empty
        l, r = KValue(), KValue()
        self.assertTrue(l.equals(r))

        l, r = KValue("Value"), KValue("Value")
        self.assertTrue(l.equals(r))
        r.set("value", "value")
        self.assertFalse(l.equals(r))

        # type field
        l, r = KValue("123"), KValue()
        r.set("value", "123")
        self.assertFalse(l.equals(r))
        r.type("text")
        self.assertTrue(l.equals(r))
        self.assertEqual(S_CLASS_TEXT, r.type())
        r.type("Text")
        self.assertEqual(S_CLASS_TEXT, r.type())
        r.type(S_CLASS_TEXT)
        self.assertEqual(S_CLASS_TEXT, r.type())

        l, r = KValue(), KValue()
        l.type("text")
        r.type("TEXT")
        self.assertTrue(l.equals(r))
        r.set("value", "")                                  # set to empty string is allowed, but we shall not do this
        self.assertFalse(l.equals(r))

        l, r = KValue(), KValue()
        l.set("child", KValue("123"))
        r.set("child", KValue(""))
        self.assertFalse(l.equals(r))
        r.get("child").set("value", "123")
        self.assertTrue(l.equals(r))
        l.get("child").set("value", KValue("abc"))
        r.get("child").set("value", KValue("abcd"))
        self.assertFalse(l.equals(r))
        r.get("child").set("value", KValue("abc"))
        self.assertTrue(l.equals(r))

    def test_fromJsonObject(self):
        kv = KValue({"@type" : "Person", "value" : u"刘德华"})
        self.assertEqual(u"刘德华", kv.get("value"))
        self.assertRaises(Exception, lambda : KValue({"@type" : "Text", "value" : u"刘德华"}))
        KValue({"@type" : S_CLASS_TEXT, "value" : u"刘德华"})

        meta = Meta({"@type" : "Person", "value" : u"刘德华"})
        self.assertEqual(u"刘德华", meta.get("value"))
        self.assertRaises(Exception, lambda : Meta({"@type" : "Text", "value" : u"刘德华"}))
        KValue({"@type" : S_CLASS_TEXT, "value" : u"刘德华"})

        # 反序列化数组
        kv = KValue({"@type" : "Person", "value" : [u"刘德华", u"朱丽倩"]})
        o = kv.get("value")
        self.assertTrue(o.isArray())
        self.assertEqual(u"朱丽倩", o[1])
        o[1] = u"小倩"
        self.assertEqual(u"小倩", o[1])
        o[1] = { "value" : u"小倩", "@type" : "Person" }
        self.assertTrue(o[1].isObject())
        json.dumps(kv._toJson())

    #
    # meta相关测试
    #
    def test_m(self):
        kv = KValue()
        self.assertEqual("", kv.m(Entity.META_LOCAL_REFER))
        kv.m(Entity.META_LOCAL_REFER, "http://xxx")
        self.assertEqual("http://xxx", kv.m(Entity.META_LOCAL_REFER))

        kv.set("child", KValue().set("value", "123").m(Entity.META_LOCAL_REFER, "xxx"))
        self.assertEqual("xxx", kv.get("child").m(Entity.META_LOCAL_REFER))

    #
    # 数组相关测试
    #
    def test_array(self):
        self.assertRaises(Exception, lambda : KValue(["1", "2"]))

        # 构造
        names = KValue.create(["A", "B"])
        self.assertTrue(names.isArray())
        kv = KValue({"@type" : "Person"})
        self.assertFalse(kv.isArray())

        # 设置
        kv.set("value", names)
        a = ["B", "C"]
        kv.set("value", a)
        self.assertTrue(kv.get("value").isArray())
        self.assertEqual("B", a[0])
        o = kv.get("value")
        self.assertNotEqual(a, o)
        o.append("D")
        self.assertEqual(3, len(a))         # 原数组会被修改
        self.assertEqual(3, o.size())
        o.remove("B")
        self.assertEqual(2, len(a))
        self.assertEqual(2, o.size())
        self.assertEqual(1, o.index("D"))
        self.assertEqual(-1, o.index("E"))

        # 值语义的append、remove、index
        a = [{"@type" : "Person", "value" : "A"}, {"@type" : "Person", "value" : "B"}]
        kv.set("value", a)
        self.assertTrue(kv.get("value").isArray())
        o = kv.get("value")
        self.assertTrue(o.isArray())
        json.dumps(kv._toJson(), indent=4)
        o.append({"@type" : "Person", "value" : "C"})
        self.assertEqual(3, o.size())
        json.dumps(kv._toJson(), indent=4)
        o.remove(dict({"@type" : "Person", "value" : "C"}))
        self.assertEqual(2, o.size())
        o.append(KValue({"@type" : "Person", "value" : "C"}))
        self.assertEqual(3, o.size())
        o.remove(KValue({"@type" : "Person", "value" : "C"}))
        self.assertEqual(2, o.size())
        o.append({"@type" : "Person", "value" : "C"})
        self.assertEqual(2, o.index(KValue({"@type" : "Person", "value" : "C"})))
        self.assertEqual(-1, o.index(KValue({"@type" : "Person", "value" : "C2"})))

        # 值语义的equals
        self.assertTrue(KValue({"@type" : "Person", "value" : "A"}).equals(o[0]))
        o[0] = {"@type" : "Person", "value" : "AAA"}
        self.assertEqual("AAA", o[0].get("value"))

        # 遍历
        a = [{"@type" : "Person", "value" : "A"}, {"@type" : "Person", "value" : "B"}]
        kv.set("value", a)
        o = kv.get("value")
        self.assertEqual(2, len(o.items()))
        self.assertEqual(2, o.size())
        self.assertTrue(o.items()[0].isObject())
        ret = []
        for v in o:
            ret.append(v)
        self.assertEqual(2, len(ret))
        self.assertTrue(ret[0].equals(o.items()[0]))
        self.assertTrue(ret[1].equals(o.items()[1]))


        #print json.dumps(kv._toJson(), indent=4)


class MetaTest(unittest.TestCase):

    def test_create(self):
        self.assertRaises(Exception, lambda : Meta())       # missing type argument

        meta = Meta(S_SPO_METASPO)
        self.assertEqual(S_SPO_METASPO, meta.type())

    # get, set, type, remove is same as KValueTest


class SpoTest(unittest.TestCase):

    def setUp(self):
        o = Entity.fromKbjson(EntityTest.Sample_Normal)
        self.o = o
        self.spo = o.get("weight")[0]
        self.spoName = o.get("name")[0]

    def tearDown(self):
        self.spo = None

    #
    # 序列化
    #
    def test_toString(self):
        o = Entity()
        o.addSpo("name", u"刘德华")
        spo = o.triples()[0]
        s = spo.toString()

        jsobj = json.loads(s)

        self.assertEqual(u"刘德华", jsobj["objects"][0]["value"])

    def test_fromString(self):
        o = Entity()
        o.addSpo("name", u"刘德华")
        spo = o.triples()[0]
        s = spo.toString()

        # 带属性反序列化
        o2 = Entity(o.id())
        spo = Spo.fromString(s, "name")
        o2.add(spo)

        s1 = o.toString()
        s2 = o2.toString()
        self.assertEqual(s1, s2)

        # 不带属性
        spo = Spo.fromString(s)
        self.assertEqual("", spo.p())
        o = Entity()
        self.assertRaises(Exception, lambda : o.add(spo))

    #
    # 属性获取
    #
    def test_propName(self):
        self.assertEqual("weight", self.spo.p())

    def test_refer(self):
        self.assertEqual("", self.spo.r())

    def test_value(self):
        self.assertEqual("68", self.spo.v())

    def test_object(self):
        o = self.spo.o()
        self.assertEqual("68", o.get(S_SPO_VALUE))
        self.assertEqual("KG", o.get("unitCode"))
        self.assertEqual("QuantitativeValue", o.type())

    def test_empty_objects(self):
        spo = self.spo
        for kv in spo.items():
            spo.remove(kv)
        self.assertEqual(0, len(spo.items()))

        self.assertEqual("weight", spo.p())
        self.assertEqual("", spo.r())
        self.assertEqual("", spo.v())
        self.assertEqual(None, spo.o())
        self.assertEqual("Person", spo.subjectType()[0])
        self.assertEqual(0, len(spo.values()))

    def test_subjectType(self):
        self.assertEqual("Person", self.spo.subjectType()[0])
        self.assertEqual(0, len(self.spoName.subjectType()))

    def test_items(self):
        self.assertEqual(1, len(self.spo.items()))
        self.assertEqual(1, len(self.spoName.items()))

        kv = self.spo.items()[0]
        self.assertTrue(kv.equals(self.o.geto("weight")[0]))

    def test_size(self):
        self.assertEqual(len(self.spo.items()), self.spo.size())

    def test_values(self):
        self.assertEqual(1, len(self.spo.values()))

        v = self.spo.values()[0]
        self.assertEqual(v, self.o.getv("weight")[0])
        self.assertEqual("68", v)

    def test_match(self):
        o = Entity.fromKbjson(EntityTest.Sample_Normal)
        """                {
                    "objects": [
                        {
                            "@type": "bkgss:Text",
                            "value": "刘德华"
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
                            "viewId": "Singer.http://baike.baidu.com/liudehua",
                            "stat" : "IDENTIFIED"
                        }
                    ]
                }, 
                {
                    "objects": [
                        {
                            "@type": "bkgss:Text", 
                            "value": "刘福荣"
                        }
                    ], 
                    "meta": [
                        {
                            "@type": "MetaSPO", 
                            "timeGenerate": "1428996364", 
                            "timeLastMod": "1428996364", 
                            "fromType": "MINING", 
                            "fromUrl": "http://baike.baidu.com/view/1758.htm", 
                            "lang": "zh-cn", 
                            "viewId": "Singer.http://baike.baidu.com/liudehua",
                            "stat" : "MARKDEL"
                        }
                    ],
                    "endDate": "1999-01-01"
                }"""
        spo = o.get("name")[0]
        self.assertTrue(spo.match(Entity.F_PUSH))
        self.assertTrue(spo.match(Entity.F_IDENTIFIED))
        self.assertTrue(spo.match(Entity.F_NODEL))
        self.assertFalse(spo.match(Entity.F_INFERENCE))
        self.assertFalse(spo.match(Entity.F_RAW))
        self.assertFalse(spo.match(Entity.F_DEL))
        spo = o.get("name")[1]
        self.assertTrue(spo.match(Entity.F_MINING))
        self.assertTrue(spo.match(Entity.F_CN))
        self.assertTrue(spo.match(Entity.F_DEL))
        self.assertFalse(spo.match(Entity.F_INFERENCE))
        self.assertFalse(spo.match(Entity.F_EN))
        self.assertFalse(spo.match(Entity.F_NODEL))

    #
    # 相等性比较
    #
    def test_equals(self):
        o = Entity()
        spo1 = o.createSpo("name", "value")
        spo2 = o.createSpo("name", "value")
        self.assertTrue(spo1.equals(spo2))
        self.assertTrue(spo2.equals(spo1))
        spo2.v("xxx")
        self.assertFalse(spo1.equals(spo2))
        
        # meta不参与spo比较
        spo1 = o.createSpo("name", "value", Entity.META_STATUS_CLEAN)
        spo2 = o.createSpo("name", "value", Entity.META_STATUS_DEFAULT)
        self.assertTrue(spo1.equals(spo2))
        spo1 = o.createSpo("name", "value", Entity.META_FROM_TYPE_CLEANSE)
        spo2 = o.createSpo("name", "value")
        self.assertTrue(spo1.equals(spo2))

        # spo相等要求属性名和objects相等
        spo1 = o.createSpo("name", "value")
        spo2 = o.createSpo("name2", "value")
        self.assertFalse(spo1.equals(spo2))
        spo2.p("name")
        self.assertTrue(spo1.equals(spo2))
        
        # KValue顺序
        kv1, kv2 = KValue("v1"), KValue("v2")
        spo1 = o.createSpo("award", kv1)
        spo2 = o.createSpo("award", kv1)
        spo3 = o.createSpo("award", kv2)
        spo1.append(kv1)
        spo1.append(kv2)
        spo2.append(kv1)
        spo2.append(kv2)
        spo3.append(kv2)
        spo3.append(kv1)
        self.assertTrue(spo1.equals(spo2))
        self.assertFalse(spo2.equals(spo3))

        # 空spo
        spo1 = o.createSpo("award", "")
        spo2 = o.createSpo("award", "")
        self.assertTrue(spo1.equals(spo2))
        spo1 = o.createSpo("award", "")
        spo2 = o.createSpo("award", "xxx")
        self.assertFalse(spo1.equals(spo2))
        spo2.remove(spo2.items()[0])
        self.assertFalse(spo1.equals(spo2))
        spo1.remove(spo1.items()[0])
        self.assertTrue(spo1.equals(spo2))

    def test_hash(self):
        o = Entity.fromKbjson(EntityTest.Sample_Small)
        jsobj = json.loads(EntityTest.Sample_Spo_Award_Objects)

        # 默认只对objects做哈希
        spo = o.get("award")[0]
        key1 = spo.hash()
        key2 = hash(json.dumps(jsobj, ensure_ascii=False, sort_keys=True))
        self.assertEquals(key1, key2)

        # withMeta2会考虑fromType和fromUrl
        key3 = o.get("award")[0].hash(withMeta2=True)
        jsobj["fromType"] = spo.m(Entity.META_FROM_TYPE)
        jsobj["fromUrl"] = spo.m(Entity.META_FROM_URL)
        key4 = hash(json.dumps(jsobj, ensure_ascii=False, sort_keys=True))
        self.assertNotEqual(key2, key3)
        self.assertEquals(key3, key4)

    #
    # 属性修改
    #
    def test_set_propName(self):
        spo = self.spo
        self.assertEqual("weight", spo.p())
        spo.p("new_weight")
        self.assertEqual("new_weight", spo.p())
        self.assertEqual(0, len(self.o.get("new_weight")))
        self.o.remove(spo)
        self.o.add(spo)
        self.assertEqual(1, len(self.o.get("new_weight")))
        # TODO：对自动移除添加的测试

    def test_set_refer(self):
        self.assertEqual("", self.spo.r())
        self.spo.r("xxx")
        self.assertEqual("xxx", self.spo.r())

    def test_set_value(self):
        self.assertEqual("68", self.spo.v())
        self.spo.v("100")
        self.assertEqual("100", self.spo.v())
        self.assertRaises(AssertionError, lambda : self.spo.v(100))

    def test_set_object(self):
        self.assertEqual("68", self.spo.v())
        self.spo.o("100")
        self.assertEqual("100", self.spo.v())

        kv = KValue()
        kv.type("text")
        kv.set("value", "120")
        self.spo.o(kv)
        self.assertEqual("120", self.spo.v())

    def test_set_with_empty_objects(self):
        spo = self.spo
        #dumpSpo(spo)

        # set value
        for kv in spo.items():
            spo.remove(kv)
        self.assertEqual(0, len(spo.items()))
        spo.v("100")
        self.assertEqual("100", spo.v())
        self.assertNotEqual(None, spo.o())
        self.assertEqual(1, len(spo.values()))
        #dumpSpo(spo)

        # set refer
        for kv in spo.items():
            spo.remove(kv)
        self.assertEqual(0, len(spo.items()))
        spo.r("xxx")
        self.assertEqual("xxx", spo.r())
        #dumpSpo(spo)
        
        # set object with string
        for kv in spo.items():
            spo.remove(kv)
        self.assertEqual(0, len(spo.items()))
        spo.o("123")
        self.assertEqual("123", spo.v())

        # set object with KValue
        for kv in spo.items():
            spo.remove(kv)
        self.assertEqual(0, len(spo.items()))
        kv = KValue()
        kv.type("QuantitativeValue")
        kv.set("value", "68000")
        kv.set("unitCode", "G")
        spo.o(kv)
        self.assertEqual("68000", spo.v())
        kv2 = spo.o()
        self.assertEqual("QuantitativeValue", kv2.type())
        self.assertEqual("G", kv2.get("unitCode"))
        #dumpSpo(spo)

    def test_set_subjectType(self):
        self.assertEqual("Person", self.spo.subjectType()[0])
        self.spo.addSubjectType("Singer")
        self.assertEqual("Singer", self.spo.subjectType()[1])
        self.spo.removeSubjectType("Person")
        self.assertEqual("Singer", self.spo.subjectType()[0])
        self.spo.removeSubjectType("xxx")
        self.assertRaises(AssertionError, lambda : self.spo.addSubjectType(""))

    def test_append(self):
        kv = KValue()
        kv.type("QuantitativeValue")
        kv.set("value", "68000")
        kv.set("unitCode", "G")
        self.assertEqual(1, len(self.spo.items()))
        self.spo.append(kv)
        self.assertEqual(2, len(self.spo.items()))
        
        spo = self.o.get("name")[0]
        #dumpSpo(spo)
        self.assertEqual(1, len(spo.items()))
        spo.append(u"华仔")
        self.assertEqual(2, len(spo.items()))
        #dumpSpo(spo)

    def test_index(self):
        kv0 = self.spo.o()
        self.assertEqual(0, self.spo.index(kv0))

        kv = KValue("100KG")
        self.spo.append(kv)
        self.assertEqual(0, self.spo.index(kv0))
        self.assertEqual(1, self.spo.index(kv))

        self.assertEqual(-1, self.spo.index(KValue()))
        
        self.assertEqual(-1, self.spo.index(kv0.get(S_SPO_VALUE)))

        spo = self.o.get("name")[0]
        self.assertEqual(0, spo.index(u"刘德华"))


    def test_remove(self):
        # remove by value
        spo = self.o.get("name")[0]
        self.assertEqual(1, len(spo.items()))
        spo.remove(u"刘德华")
        self.assertEqual(0, len(spo.items()))

        # remove by exist KValue
        spo = self.o.get("name")[1]
        self.assertEqual(1, len(spo.items()))
        spo.remove(spo.o())
        self.assertEqual(0, len(spo.items()))

        # remove by a new KValue
        spo = self.spo
        self.assertEqual(1, len(spo.items()))
        kv = KValue()
        kv.type("QuantitativeValue")
        kv.set(S_SPO_VALUE, "69")
        kv.set("unitCode", "KG")
        spo.remove(kv)
        self.assertEqual(1, len(spo.items()))
        kv.set(S_SPO_VALUE, "68")
        spo.remove(kv)
        self.assertEqual(0, len(spo.items()))
        #dumpSpo(spo)

        # remove non-exist value
        spo = self.o.get("award")[0]
        self.assertEqual(1, len(spo.items()))
        self.assertRaises(AssertionError, lambda : spo.remove(None))
        spo.remove("")
        spo.remove("xxx")
        spo.remove(KValue())
        self.assertEqual(1, len(spo.items()))

    #
    # meta操作
    #
    def test_MetaSPO(self):
        # 快捷meta操作
        spo = self.spo
        self.assertEqual("1428996364", spo.m("timeLastMod"))
        self.assertEqual("", spo.m("xxx"))
        self.assertEqual(Entity.META_FROM_TYPE_PUSH, spo.m(Entity.META_FROM_TYPE))
        spo.m(Entity.META_FROM_TYPE, Entity.META_FROM_TYPE_FEED)
        self.assertEqual(Entity.META_FROM_TYPE_FEED, spo.m(Entity.META_FROM_TYPE))

        spo = self.o.get("coOccur")[1]
        self.assertEqual("", spo.m(Entity.META_FROM_TYPE))
        spo.m(Entity.META_FROM_TYPE, Entity.META_FROM_TYPE_PUSH)
        self.assertEqual(Entity.META_FROM_TYPE_PUSH, spo.m(Entity.META_FROM_TYPE))
        #dumpSpo(spo)

    def test_meta(self):
        spo = self.spo
        self.assertEqual(2, len(spo.meta()))
        meta = spo.meta(S_SPO_METASPO)[0]
        self.assertEqual(Entity.META_FROM_TYPE_PUSH, meta.get(Entity.META_FROM_TYPE))

        meta = spo.meta("MetaCustom")[0]
        self.assertEqual("0.1", meta.get("resolution"))
        self.assertRaises(AssertionError, lambda : meta.set("confidence", 0.9))
        meta.set("confidence", "0.9")
        self.assertEqual("0.9", meta.get("confidence"))
        #dumpSpo(spo)

    def test_appendMeta(self):
        spo = self.spo
        meta = spo.meta("MetaCustom")[0]
        self.assertEqual(2, len(spo.meta()))
        spo.appendMeta(meta)
        self.assertEqual(3, len(spo.meta()))
        self.assertEqual(2, len(spo.meta("MetaCustom")))

        spo.removeMeta(meta)
        self.assertEqual(1, len(spo.meta()))            # remove two at once
        #dumpSpo(spo)

    def test_removeMeta(self):
        spo = self.spo
        meta = spo.meta("MetaCustom")[0]
        self.assertEqual(2, len(spo.meta()))
        spo.removeMeta(meta)
        self.assertEqual(1, len(spo.meta()))

    #
    # 属性上的属性
    #
    def test_attr(self):
        spo = self.o.get("name")[1]
        self.assertEqual("1999-01-01", spo.attr("endDate"))
        self.assertEqual("", spo.attr("notexist"))
        spo.attr("endDate", "2010-10-10")
        self.assertEqual("2010-10-10", spo.attr("endDate"))

        spo = self.o.get("weight")[0]
        self.assertEqual("", spo.attr("xxx"))
        self.assertRaises(AssertionError, lambda : spo.attr("xxx", 60))
        spo.attr("xxx", "60")
        spo = self.o.get("weight")[0]
        self.assertEqual("60", spo.attr("xxx"))

    def test_attrs(self):
        spo = self.o.get("name")[1]
        self.assertEqual(1, len(spo.attrs()))
        self.assertEqual(("endDate", "1999-01-01"), spo.attrs()[0])
        spo.attr("xxx", "60")
        self.assertEqual(2, len(spo.attrs()))

    def test_removeAttr(self):
        spo = self.o.get("name")[1]
        self.assertEqual(1, len(spo.attrs()))
        spo.removeAttr("endDate")
        self.assertEqual(0, len(spo.attrs()))


class EntityTest(object):
    #
    # 测试用数据
    #
    Sample_Small = """{
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

    Sample_Spo_Award = """{
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
    }"""
    
    Sample_Spo_Award_Objects = """{
        "objects": [

            {
                "@type": "Song",      
                "value": "冰雨"
            },
            
            {
                "@type": "Song",      
                "value": "笨小孩"
            }
        ]
    }"""

    Sample_Small_Sort = """{
    "@context": "http://kg.baidu.com/sample_context.jsonld", 
    "@id": "http://userbase.kgs.baidu.com/somename/liudehua", 
    "@type": [
        "Person", 
        "Singer", 
        "Actor"
    ], 
    "award": [
        {
            "meta": [
                {
                    "@type": "MetaSPO", 
                    "fromType": "PUSH", 
                    "fromUrl": "http://baike.baidu.com/view/1758.htm", 
                    "lang": "zh-cn", 
                    "timeGenerate": "1428996364", 
                    "timeLastMod": "1428996364", 
                    "viewId": "Singer.http://baike.baidu.com/liudehua"
                }
            ], 
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
            "subjectType": [
                "Singer"
            ]
        }
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

    Sample_Min = """{
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
    
    Sample_OType = """{
        "@type": [          
            "Person"
        ], 
        "friend": [
            {
                "objects": [
                    {
                        "@type": ["EntertainmentPerson", "Person"],      
                        "value": "刘德华"
                    }
                ]
            }
        ]
    }"""
    
    Sample_KValue_Meta_Array = """{
        "@type": [          
            "Person"
        ], 
        "friend": [
            {
                "objects": [
                    {
                        "@type": "Person",      
                        "value": "刘德华",
                        "meta" : {
                            "@type" : "MetaS",
                            "localRefer" : "http://xxx.com/1234"
                        }
                    },
                    {
                        "@type": "Person",      
                        "value": "华仔",
                        "meta" : [{
                            "@type" : "MetaS",
                            "localRefer" : "http://xxx.com/1111"
                        }]
                    }
                ]
            }
        ]
    }"""
        
    Sample_KValue_Meta_Nest_Array = """{
        "@type": [          
            "Person"
        ], 
        "friend": [
            {
                "objects": [
                    {
                        "@type": "Person",      
                        "value": "刘德华",
                        "meta" : {
                            "@type" : "MetaS",
                            "localRefer" : "http://xxx.com/1234"
                        },
                        "other" : {
                            "value" : "xxx",
                            "meta" : {
                                "@type" : "MetaS",
                                "localRefer" : "inner refer"
                            }
                        }
                    },
                    {
                        "@type": "Person",      
                        "value": "华仔",
                        "meta" : [{
                            "@type" : "MetaS",
                            "localRefer" : "http://xxx.com/1111"
                        }]
                    }
                ]
            }
        ]
    }"""

    Sample_Nest_KValue = """{
        "@type": [          
            "Person"
        ], 
        "award": [
            {
                "objects": [
                    {
                        "@type": "SomeStructuredValue",      
                        "value": "奖项A",
                        "other": {
                            "@type": "StructuredValue", 
                            "location" : "北京",
                            "year" : "2015"
                        }
                    }
                ]
            }
        ]
    }"""
    
    Sample_Single_Type = """{
        "@type": "Person",
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
    
    Sample_Empty_Property = """{
        "@type": [          
            "Person"
        ], 
        "name": [

        ]
    }"""
        
    Sample_Empty_SPO_META = """{
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
                ],

                "meta" : []
            }
        ]
    }"""
            
    Sample_Empty_SPO_OBJ = """{
        "@type": [          
            "Person"
        ], 
        "name": [
            {
                "objects": [

                ]
            }
        ]
    }"""
    
    Sample_Empty_Subject_Type1 = """{
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
                ],
                "subjectType" : ""
            }
        ]
    }"""
        
    Sample_Empty_Subject_Type2 = """{
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
                ],
                "subjectType" : []
            }
        ]
    }"""
    
    Sample_Subject_Type = """{
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
                ],
                "subjectType" : "Person"
            },
            {
                "objects": [
                    {
                        "@type": "bkgss:Text",      
                        "value": "华仔"
                    }
                ],
                "subjectType" : ["Singer"]
            }
        ]
    }"""
    
    Sample_Meta = """{
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
        ],
        "meta" : [
            {
                "@type" : "CustomMeta",
                "version" : "1.0"
            }
        ]
    }"""
    
    Sample_RawProperty = """{
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
        ],
        "property" : [
            {
                "objects" : [
                    {
                        "@type": "bkgss:Text", 
                        "value" : "RAW_VALUE"
                    }
                ],
                "name" : "RAW_NAME"
            },
            {
                "objects" : [
                    {
                        "@type": "bkgss:Text", 
                        "value" : "RAW_VALUE2"
                    }
                ],
                "name" : "RAW_NAME2"
            }
        ],
        "meta" : [
            {
                "@type" : "CustomMeta",
                "version" : "1.0"
            }
        ]
    }"""

    Sample_Empty = """{}"""

    Sample_Normal_Size = 7
    Sample_Normal_Attr_Size = 4
    Sample_Normal = """{
            "@context": "http://kg.baidu.com/sample_context.jsonld", 
            "@id": "http://userbase/k/liudehua", 
            "@type": [
                "Person", 
                "Singer", 
                "Actor"
            ], 
            "meta" : [
                {
                    "@type" : "SomeMetaType",
                    "value" : "123"
                }
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
                        }
                    ], 
                    "subjectType": ["Singer"]
                }, 
                {
                    "objects": [
                        {
                            "@type": "Movie", 
                            "value": "无间道", 
                            "refer": "userbase:k/wujiandao"
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
                            "viewId": "Actor.http://baike.baidu.com/liudehua"
                        }
                    ], 
                    "subjectType": ["Actor"]
                }
            ], 
            "coOccur": [
                {
                    "objects": [
                        {
                            "@type": "Person", 
                            "value": "张学友", 
                            "refer": "userbase:k/zhangxueyou"
                        }
                    ], 
                    "meta": [
                        {
                            "@type": "MetaSPO", 
                            "timeGenerate": "1428996364", 
                            "timeLastMod": "1428996364", 
                            "fromType": "MINING", 
                            "fromUrl": "http://baike.baidu.com/view/1758.htm", 
                            "lang": "zh-cn", 
                            "viewId": "Relation.http://baike.baidu.com/liudehua"
                        }
                    ]
                }, 
                {
                    "objects": [
                        {
                            "@type": "coOccur", 
                            "meta": [], 
                            "value": "共现关系", 
                            "refer": "userbase:r/coocur/liudehua/zhangxueyou"
                        }
                    ], 
                    "subjectType": []
                }
            ], 
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
                            "@type": "MetaSPO", 
                            "timeGenerate": "1428996364", 
                            "timeLastMod": "1428996364", 
                            "fromType": "PUSH", 
                            "fromUrl": "http://baike.baidu.com/view/1758.htm", 
                            "lang": "zh-cn", 
                            "viewId": "Singer.http://baike.baidu.com/liudehua",
                            "stat" : "IDENTIFIED"
                        }
                    ]
                }, 
                {
                    "objects": [
                        {
                            "@type": "bkgss:Text", 
                            "value": "刘福荣"
                        }
                    ], 
                    "meta": [
                        {
                            "@type": "MetaSPO", 
                            "timeGenerate": "1428996364", 
                            "timeLastMod": "1428996364", 
                            "fromType": "MINING", 
                            "fromUrl": "http://baike.baidu.com/view/1758.htm", 
                            "lang": "zh-cn", 
                            "viewId": "Singer.http://baike.baidu.com/liudehua",
                            "stat" : "MARKDEL"
                        }
                    ],
                    "endDate": "1999-01-01"
                }
            ], 
            "weight":[
                {
                    "objects": [
                        {
                            "@type": "QuantitativeValue", 
                            "unitCode":"KG", 
                            "value":"68"
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
                            "viewId": "person.http://baike.baidu.com/liudehua"
                        }, 
                        {
                            "@type": "MetaCustom", 
                            "resolution": "0.1"
                        }
                    ], 
                    "subjectType": ["Person"]
                }
            ]
        }"""

    Sample_Kbjson1_Small = """{
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

    Sample_Jsonld_Array = """{
        "@context": "http://st01-wdm-site-off1.st01.baidu.com:8080/context/kbjson_context.jsonld", 
        "@id": "http://st01-wdm-site-off1.st01.baidu.com:8080/KGCoreData/tier1/e13236bb77607942ba8f4c0b14a2180d", 
        "@type": "Blog", 
        "_bdbkLemmaDesc": {
            "@type": "_bdbkLemmaDesc", 
            "meta": {
                "@type": "MetaSPO", 
                "ctime": "1430220991", 
                "fromUrl": "http://baike.baidu.com/view/4884834.htm", 
                "intime": "1431498102", 
                "spoSign": "ea0a409297624f58f86d5f2697fbe48b", 
                "stat": "DEFAULT", 
                "timeGenerate": "1428419381", 
                "timeLastMod": "1428419381", 
                "viewId": "http://st01-wdm-site-off1.st01.baidu.com:8080/KGCoreData/bdbk/10722146"
            }, 
            "name": "_bdbkLemmaDesc", 
            "objects": [
                {
                    "@type": "bkgss:Text", 
                    "value": "24小时制"
                }
            ], 
            "subjectType": "Thing"
        },
        "meta" : {
            "@type": "CustomMeta", 
            "ctime": "1430220991"
        }
    }
    """


class ParserTest(unittest.TestCase):
    
    def test_parser_load(self):
        self.assertIsInstance(Parser.items()[0][1], Parser)

    def test_fromParser(self):
        Parser.add("jsobj", ParserTest.JsonObjectParser())
        o = Entity.fromParser(ParserTest.Json_PO, "jsobj")
        self.assertEqual("15", o.getv("age")[0])

    def test_add(self):
        Parser.add("simple", ParserTest.SimpleParser())
        o = Entity.fromParser("", "simple")
        self.assertIsInstance(o, Entity)

    def test_get(self):
        self.assertEqual("KbjsonV1Parser", Parser.get("v1").__class__.__name__)
        self.assertIsNone(Parser.get("notexist"))

    def test_items(self):
        count = len(Parser.items())
        Parser.add("empty", Parser())
        self.assertEqual(count + 1, len(Parser.items()))

    #
    # 测试用数据
    #
    class JsonObjectParser(Parser):
        def parse(self, text):
            import json
            pbag = json.loads(text)
            o = Entity()
            for key, value in pbag.items():
                spo = o.createSpo(key, value)
                o.add(spo)
            return o

    class SimpleParser(Parser):
        def parse(self, text):
            o = Entity()
            o.id = "http://empty"
            return o

    Json_PO = """{
        "name" : "baidu",
        "age" : "15"
    }"""


class UpgradeTest(unittest.TestCase):
    
    def test_normal(self):
        o = Entity.fromKbjson1(UpgradeTest.Sample_Kbjson1_Normal)

        # type
        self.assertEqual("Person", o.type()[0])
        self.assertEqual(0, len(o.get("type")))

        # refer、MetaSPO
        self.assertEqual("e6f3a388c6ac11e38974047d7b067fc6", o.get("spouse")[0].r())
        self.assertEqual("1.0", o.get("spouse")[0].m("confidence"))

        # INFO in MetaAVP
        meta = None
        for spo in o.get("memberOf"):
            a = spo.meta(S_SPO_METAAVP)
            if a:
                meta = a[0]
                break
        self.assertIsInstance(meta, Meta)
        self.assertIsInstance(meta.get("INFO"), KValue)
        self.assertNotEqual("", meta.get("INFO").get("REMARK"))
        self.assertEqual("", meta.get("INFO").get("notexist"))

        # other fields in MetaAVP
        self.assertEqual("0.745036", o.get("SIM")[0].meta("MetaAVP")[0].get("SIM_VAL"))
        self.assertEqual("114923", o.get("name")[0].m("viewId"))
        #dump(o)

    #
    # 测试用数据
    #
    Sample_Kbjson1_Normal = """{
        "ID": "66cfc7acc6a911e38974047d7b067fc6",
        "AVP_LIST": [
            {
                "ATTRIBUTE": "type",
                "VALUE": "Person",
                "VALUE_TYPE": "LITERAL",
                "FROM_TYPE": "PUSH",
                "VALUE_LANG": "zh-cn",
                "FROM_URL": "http://baike.baidu.com/view/1758.htm"
            },
            {
                "ATTRIBUTE": "name",
                "VALUE": "刘德华",
                "VALUE_TYPE": "LITERAL",
                "FROM_TYPE": "PUSH",
                "VALUE_LANG": "zh-cn",
                "FROM_URL": "http://baike.baidu.com/view/1758.htm",
                "VIEW_ID": "114923"
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
            },
            {
                "ATTRIBUTE": "memberOf",
                "VALUE": "映艺娱乐",
                "VALUE_TYPE":"LITERAL",
                "FROM_TYPE": "PUSH",
                "VALUE_LANG": "zh-cn",
                "FROM_URL": "http://baike.baidu.com/view/1758.htm",
                "TIME_GENERATE": "1009814400",
                "INFO" : {"REMARK" : "2014Q1人物定向挖掘"}
            },
            {
                "ATTRIBUTE": "spouse",
                "VALUE": "朱丽倩",
                "REFER": "e6f3a388c6ac11e38974047d7b067fc6",
                "VALUE_TYPE":"LITERAL",
                "CONFIDENCE":"1.0",
                "FROM_TYPE": "PUSH",
                "VALUE_LANG": "zh-cn",
                "FROM_URL": "http://baike.baidu.com/view/1758.htm",
                "TIME_GENERATE": "1214150400"
            },
            {
                "ATTRIBUTE": "SIM",
                "SIM_VAL": "0.745036",
                "VALUE": "柯受良",
                "VALUE_TYPE": "LITERAL",
                "FROM_TYPE": "MINING",
                "VALUE_LANG": "zh-cn",
                "REFER": "ee62b65659ba4ced8ba0423588318e07"
            }
        ]
    }"""

    Sample_Kbjson1_Person = """"""


if __name__ == "__main__":
    suite1 = unittest.TestLoader().loadTestsFromTestCase(EntityOpTest)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(PropertyOpTest)
    suite3 = unittest.TestLoader().loadTestsFromTestCase(KValueTest)
    suite4 = unittest.TestLoader().loadTestsFromTestCase(SpoTest)
    suite5 = unittest.TestLoader().loadTestsFromTestCase(MetaTest)
    suite6 = unittest.TestLoader().loadTestsFromTestCase(MetaOpTest)
    suite7 = unittest.TestLoader().loadTestsFromTestCase(ParserTest)
    suite8 = unittest.TestLoader().loadTestsFromTestCase(UpgradeTest)
    
    suite = unittest.TestSuite([
        suite1, 
        suite2,
        suite3,
        suite4,
        suite5,
        suite6,
        suite7,
        suite8,
    ])
    unittest.TextTestRunner(verbosity=2).run(suite)
