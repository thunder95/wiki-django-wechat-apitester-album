# coding=utf-8  

import requests
import json
import os
import sys
import ssl
import re
import time

reload(sys)
sys.setdefaultencoding("utf-8")

class apidoc:
    def __init__(self):
        if hasattr(ssl, '_create_unverified_context'):
            ssl._create_default_https_context = ssl._create_unverified_context
        self.base_url = ''
        self.global_data = {}
        self.myRequests = requests.Session()

    def api(self, content):
        self.content = content
        self.parse_headers()
        basics = self.parse_basic()
        params = self.parse_params()

        start = time.clock()
        rs = self.req(basics[0], params, basics[1])
        consume_time = "%f s" % (time.clock() - start)
        self.parse_return(rs['data'])

        try:
            return {
                'title':re.findall(u"####接口名称(.*?)####",self.content,re.S)[0].replace('\n', '').strip(),
                #'title':'unkonwn',
                'consume_time': consume_time,
                'url': basics[0],
                'result': self.check_result(rs),
                'params': json.dumps(params),
                'response': json.dumps(rs)
            }
        except Exception,e:
            print(e)
            return {}

    #发起请求
    def req(self, url, params, mtype):
        try:
            if mtype == 1:
                #GET
                r = self.myRequests.get(url=url, params=params, timeout=2)
            elif mtype == 2:
                #POST
                r = self.myRequests.post(url, data=json.dumps(params, ensure_ascii=False).encode('utf8'),timeout=2)
            elif mtype == 3:
                r = self.myRequests.put(url, data=json.dumps(params, ensure_ascii=False).encode('utf8'), timeout=2)
            else:
                return False
            return json.loads(r.text)

        except Exception,e:
            print(e)
            return False

    #解析基础信息
    def parse_basic(self):
        #base url
        try:
            self.base_url = re.findall(r"BASE_URL = (.+?)\s+",self.content)[0]
        except Exception,e:
            print(e)
            pass


        #api url
        try:
            url = self.base_url + re.findall(r"RURL = (.+?)\s+",self.content)[0]
            print(url)
        except Exception,e:
            print(e)
            return False   

        #type
        try:
            methode = re.findall(r"METHODE = ([a-zA-z]+?)\s+",self.content)[0].strip()
            
            if methode.lower() == 'post' :
                mtype = 2
            elif methode.lower() == 'get' :
                mtype = 1
            elif methode.lower() == 'put' :
                mtype = 3
            else:
                print(methode)
                return False
        except Exception,e:
            print(e)
            return False

        return (url, mtype)

    #解析并更新头信息
    def parse_headers(self):
     
        #取片段
        try:
            content = re.findall(u"####头信息(.*?)####",self.content,re.S)[0]
        except Exception,e:
            #print(e)
            return False

        _dict = {}
        flag = False
        for item in content.splitlines():
            if item.count('|')> 3 and flag:
                tmp = item.split('|')
                _dict[tmp[1].strip()] = tmp[2].strip()
            if '----' in item:
                flag = True

        print(_dict)
        if len(_dict)>0:    
            self.myRequests.headers.update(_dict)

    #解析传参
    def parse_params(self):
        #取片段
        try:
            content = re.findall(u"####参数说明(.*?)####",self.content,re.S)[0]
        except:
            return False

        _dict = {}
        flag = False
        for item in content.splitlines():
            try:
                if item.count('|')> 3 and flag:
                    tmp = item.split('|')
                    key = tmp[1].strip()

                    #修正val的值
                    if '~GLOBAL~' in tmp[2]:
                        tmp_val = self.global_data[tmp[2].split('~')[-1].strip()]
                    else:
                        tmp_val = tmp[2].strip()

                    #val可能是数组
                    if tmp_val[0] == '[' and tmp_val[-1] == ']':
                        tmp_val = tmp_val[1:-1].split(',')

                    #修正key的值
                    alist = key.split('/')
                    first = alist.pop().strip()
                    if first == '[' and first == ']':
                        tmp = [{first[1:-1]:tmp_val}]
                    else :
                        tmp = {first:tmp_val}

                    alist.reverse()
                    for item in alist:
                        tmp = {item:tmp}

                    #合并字典，尚未测试字典中多个字段
                    self.deepSearch(_dict, tmp)


                if '----' in item:
                    flag = True
            except Exception,e:
                print(e)
                continue

        print(_dict)
        return _dict


    #解析参数返回
    def parse_return(self, rs):
        tmp_headers = {}
        #print(re.findall(u"####返回说明(.*?)####",self.content,re.S)[0])

        #取片段
        try:
            content = re.findall(u"####返回说明(.*?)####",self.content,re.S)[0]
        except Exception,e:
            print(e)
            return False
        
        for item in content.splitlines():
            try:
                second = item.split('|')[1]
                key = second.split('~')[-1].strip()
                #递归取出key的值
                key_seq = key.split('/')
                tmp = rs
                for ks in key_seq:
                    tmp = tmp[ks].strip()

                #存入全局变量
                if '~HEADER~' in second:
                    #tmp_headers.append(second.split('~')[-1].strip())
                    tmp_headers[key] = tmp
                if '~GLOBAL~' in second:
                    #self.global_data.append(second.split('~')[-1].strip())
                    self.global_data[key] = tmp

            except Exception,e:
                #print(e)
                continue

        #更新headers
        self.myRequests.headers.update(tmp_headers)

    #检验返回结果
    def check_result(self, rs):
        try:
            content = re.findall(u"####返回校验(.*?)####",self.content,re.S)[0]
        except Exception,e:
            print(e)
            return False

        string = ''
        flag = False
        for item in content.splitlines():
            tmp_rs = ''
            if item.count('|')> 3 and flag:
                tmp = item.split('|')

                #参考值 可以是全局变量, 字符串
                if '~GLOBAL~' in tmp[3]:
                    target_val = self.global_data[tmp[3].split('~')[-1].strip()]
                else:
                    target_val = tmp[3].strip()

                #取值, 只支持最后一级是列表
                karr = tmp[1].strip().split('/')
                last = karr.pop().strip()

                #结果集
                rs_data = rs
                for ki in karr:
                    if not rs_data.has_key(ki):
                        rs_data = {}
                        string += tmp[1].strip() + ":测试未通过, 原因:字段未匹配到"+ki+"<br>"
                        break
                    else:
                        print("==="+ki)
                        rs_data = rs_data[ki]

                if not rs_data:
                    continue

                if last[0] == '[' and last[-1] == ']':
                    #循环判断
                    last = last[1:-1]
                    for item in rs_data:
                        calc_rs = self.calc_result(item, last, tmp[2].strip(), target_val)
                        if len(calc_rs)>0 :
                            tmp_rs = tmp[1].strip() + ":测试未通过, 原因: " + calc_rs
                            break

                else:
                    #单词判断
                    calc_rs = self.calc_result(rs_data, last, tmp[2].strip(), target_val)
                    if len(calc_rs)>0 :
                        tmp_rs = tmp[1].strip() + ":测试未通过, 原因: " + calc_rs

                #收集所有结果
                if len(tmp_rs)<1 :
                    string +=  tmp[1].strip() + ":测试通过<br>"
                else:
                    string += tmp_rs + "<br>"

     

            if '----' in item:
                flag = True

        return string

    #单个判断结果, 根据需要累加
    def calc_result(self, result, field, opt, val):
        string = ''
        print(len(result))
        if not isinstance(result,dict):
            string = "选取的字段不存在字典中，请参考data/data/[cust_type]"

        elif not result.has_key(field):
            string = "不存在此字段"+field

        elif opt == '=' and str(result[field]) != str(val):
            string = "返回的"+ str(result[field]) +'不等于预设的'+ str(val)

        return string



    #深度合并， 后期需要加入字典中带列表的情形
    def deepSearch(self,_dict, tmp):  
        for key in tmp.keys():  
            if key not in _dict.keys():  
                _dict[key] = tmp[key]  
            else:  
                self.deepSearch(_dict[key], tmp[key])


