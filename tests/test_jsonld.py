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
reload(sys)
sys.setdefaultencoding("utf-8")

class JsonldTest(unittest.TestCase):
    
    def test_normal(self):
        o = Entity.fromJsonld(JsonldTest.Sample_Jsonld_Normal1)
        print o.toString()

        # id
        self.assertEqual(u"http://movie.douban.com/subject/5349275/", o.id())
        
        # name
        self.assertEqual(u"魔法少女小圆", o.name())
        self.assertEqual(u"魔法少女小圆", o.getv("name")[0])
        self.assertEqual(u"魔法少女まどか★マギカ", o.getv("name")[1])

        # type
        self.assertEqual(u"动画", o.type()[0])
        self.assertEqual(u"TVSeries", o.type()[1])

        # director
        attr = o.get("director")
        spo = attr[0]
        self.assertEqual(u"新房昭之", spo.o().get("value"))
        self.assertEqual(u"新房昭之", o.getv("director")[0])
        self.assertEqual(u"3", spo.o().get(u"出演场次1")[2])
        self.assertEqual(u"3", spo.o().get(u"出演场次2").get("c"))
        self.assertEqual(u"3", spo.o().get(u"出演场次3").get("c"))
        self.assertEqual(u"3", spo.o().get(u"出演场次4")[2])
        
        # 编剧
        attr = o.get(u"编剧")
        spo = attr[0]
        self.assertEqual(u"虚渊玄", spo.o().get("text"))
        self.assertEqual(u"http://movie.douban.com/search/%E8%99%9A%E6%B8%8A%E7%8E%84", spo.o().get("tourl"))


        # 主演
        attr = o.get(u"主演")
        self.assertEqual(u"http://movie.douban.com/celebrity/1001776/", attr[0].r())
        self.assertEqual(u"http://movie.douban.com/celebrity/1004083/", attr[6].r())
        self.assertEqual(u"6.789", attr[2].o().get(u"score"))
        self.assertEqual(u"5", (attr[2].o().get(u"出演场次1"))[1])
        self.assertEqual(u"6", (attr[2].o().get(u"出演场次2"))[2])
        self.assertEqual(u"6", (attr[2].o().get(u"出演场次3")).get(u"f"))
        self.assertEqual(u"8", (attr[2].o().get(u"出演场次4")).get(u"g")[1])

    #
    # 测试用数据
    #
    Sample_Jsonld_Normal1 = """{
        "@id": "http://movie.douban.com/subject/5349275/",
        "@type": [
            "动画",
            "TVSeries"
        ],
        "douban_score":8.1,
        "alias":"魔法少女まどか★マギカ",
        "name": [
            "魔法少女小圆",
            "魔法少女まどか★マギカ"
        ],
        "director": {
            "@value":"新房昭之",
            "score": 1.2345,
            "出演场次1": ["1", "2", "3"],
            "出演场次2": {"a":"1", "b":"2", "c":"3"},
            "出演场次3": {"a":1, "b":2, "c":3},
            "出演场次4": [1, 2, 3]
        },
        "编剧": {
            "text": "虚渊玄",
            "tourl": "http://movie.douban.com/search/%E8%99%9A%E6%B8%8A%E7%8E%84",
            "1":{
                    "@id":"111",
                    "xxx":"222",
                    "@idSourceType":"NED"
            }   
        },
        "主演": [
            {
                "@id": "http://movie.douban.com/celebrity/1001776/",
                "@idSourceType":"NED"
            },
            {
                "@id": "http://movie.douban.com/celebrity/1033828/"
            },
            {
                "@id": "http://movie.douban.com/celebrity/1051936/",
                "score": 6.789,
                "score_int": 6,
                "出演场次1": ["4", "5", "6"],
                "出演场次2": [4, 5, 6],
                "出演场次3": {"d":"4", "e":"5", "f":"6"},
                "出演场次4": {"d":4, "e":5, "f":6, "g":[7,8,9]}
            },
            {
                "@id": "http://movie.douban.com/celebrity/1276137/",
                "@idSourceType":"NED"
            },
            {
                "@id": "http://movie.douban.com/celebrity/1258374/"
            },
            {
                "@id": "http://movie.douban.com/celebrity/1020062/"
            },
            {
                "@id": "http://movie.douban.com/celebrity/1004083/"
            },
            {
                "@id": "http://movie.douban.com/celebrity/1004093/",
                "1":{
                    "@id":"111",
                    "xxx":"222",
                    "@idSourceType":"NED"
                }   
            }
        ]
}"""


if __name__ == "__main__":
    suite1 = unittest.TestLoader().loadTestsFromTestCase(JsonldTest)
    
    suite = unittest.TestSuite([
        suite1
    ])
    unittest.TextTestRunner(verbosity=2).run(suite)
