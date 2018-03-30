# coding=utf-8  

#将json格式的数据格式化到api文档中


import requests
import json
import os
import sys
import ssl
import re
import time
reload(sys)
sys.setdefaultencoding("utf-8")

#将json格式转为传入参数或返回
def parse(jObj, prefix=None):
    global string
    for item in jObj:
        #print(item)
        #print(jObj[item])
        key = item
        if prefix:
            key = prefix+'/'+item
        if isinstance(jObj[item], list):
            if isinstance(jObj[item][0], dict):
                parse(jObj[item][0], key)
        elif isinstance(jObj[item], dict):
            parse(jObj[item], key)
        else:
            string += '|'+key+ '|'+ str(jObj[item]) +"||\n"

def deepSearch(dict1, dict2):  
    for key in dict2.keys():  
        if key not in dict1.keys():  
            dict1[key] = dict2[key]  
        else:  
            deepSearch(dict1[key], dict2[key])  

if __name__ == '__main__':
    jstr = '{"user_id":"","user_id_desc":"","cust_status":1,"cust_name":"丫丫策马","cust_concat_name":"向大侠","cust_concat_phone":"13454547878","selectedRegion":["130000","130300","130306"],"cust_addr":"不晓得哪根道99好","notes":"费瓦访玩","cust_type":6,"org_code":"qslb00830001","create_user_id":"USER0000000045","type":"add","region_code1":"130000","region_code2":"130300","region_code3":"130306","checkedcate":["qslb008300010002"]}'

    obj = json.loads(jstr)
    global string
    string = ''
    parse(obj)
    print(string)

   
