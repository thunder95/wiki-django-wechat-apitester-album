# -*- coding: utf-8 -*-
#!/usr/bin/python
from __future__ import print_function

import os
import requests
import re
import time
import xml.dom.minidom
import json
import math
import subprocess
import ssl
import threading
import urllib
import urllib3
from PIL import Image
import io
import pdfkit
import sys
import hashlib
from collections import OrderedDict
import mimetypes, hashlib
#from .models import Wxgroups
from .wechat_db import handel_groups
#import panda as pd
#import matplotlib as mpl
#mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fontmanager
#分词统计
from wordcloud import WordCloud,STOPWORDS,ImageColorGenerator 
import jieba 
from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']            #SimHei是黑体的意思

reload(sys)
sys.setdefaultencoding("utf-8")



class Wechat:
    def __init__(self, request, uid=None):
        self.request = request
        if uid:
            self.uid = uid

        if hasattr(ssl, '_create_unverified_context'):
            ssl._create_default_https_context = ssl._create_unverified_context

        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36'
        headers = {'User-agent': self.user_agent}
        self.myRequests = requests.Session()
        self.myRequests.headers.update(headers)

        


    #获取uuid
    def getUuid(self):
        url = 'https://login.weixin.qq.com/jslogin'
        params = {
            'appid': 'wx782c26e4c19acffb',
            'fun': 'new',
            'lang': 'zh_CN',
            '_': int(time.time()),
        }

        r= self.myRequests.get(url=url, params=params)
        r.encoding = 'utf-8'
        data = r.text

        # print(data)

        # window.QRLogin.code = 200; window.QRLogin.uuid = "oZwt_bFfRg==";
        regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
        pm = re.search(regx, data)

        self.request.session["code"] =  pm.group(1) 
        self.request.session["uuid"] =  pm.group(2) 

        if self.request.session["code"] == '200':
            return True

        return False

    #获取QR图片
    def loginQr(self):
        #更新uuid
        if not self.getUuid():
            return False

        url = 'https://login.weixin.qq.com/qrcode/' + self.request.session["uuid"]
        params = {
            't': 'webwx',
            '_': int(time.time()),
        }

        #r = self.myRequests.get(url=url, params=params)
        self.request.session["tip"] = 1

        return url

    #等待scan
    def waitScan(self):
        url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (
        self.request.session["tip"], self.request.session["uuid"], int(time.time()))

        r = self.myRequests.get(url=url)
        r.encoding = 'utf-8'
        data = r.text

        # print(data)

        # window.code=500;
        regx = r'window.code=(\d+);'
        pm = re.search(regx, data)

        code = pm.group(1)

        if code == '201':  # 已扫描
            self.request.session["tip"] = 0
        elif code == '200':  # 已登录
            regx = r'window.redirect_uri="(\S+?)";'
            pm = re.search(regx, data)
            redirect_uri = pm.group(1) + '&fun=new'
            

            base_uri = redirect_uri[:redirect_uri.rfind('/')]
            self.request.session["base_uri"] = base_uri

            # push_uri与base_uri对应关系(排名分先后)(就是这么奇葩..)
            services = [
                ('wx2.qq.com', 'webpush2.weixin.qq.com'),
                ('qq.com', 'webpush.weixin.qq.com'),
                ('web1.wechat.com', 'webpush1.wechat.com'),
                ('web2.wechat.com', 'webpush2.wechat.com'),
                ('wechat.com', 'webpush.wechat.com'),
                ('web1.wechatapp.com', 'webpush1.wechatapp.com'),
            ]
            push_uri = base_uri
            for (searchUrl, pushUrl) in services:
                if base_uri.find(searchUrl) >= 0:
                    push_uri = 'https://%s/cgi-bin/mmwebwx-bin' % pushUrl
                    break

            #登录
            baseRequest = self.login(redirect_uri)

            if baseRequest:
                #初始化
                self.webwxinit(base_uri, baseRequest)
        elif code == '408':  # 超时
            #此时会更新qr
            pass

        print('waiting....'+code)
        return code


    def login(self, redirect_uri):
        r = self.myRequests.get(url=redirect_uri)
        r.encoding = 'utf-8'
        data = r.text

        # print(data)

        doc = xml.dom.minidom.parseString(data)
        root = doc.documentElement
        for node in root.childNodes:
            if node.nodeName == 'skey':
                skey = node.childNodes[0].data
            elif node.nodeName == 'wxsid':
                wxsid = node.childNodes[0].data
            elif node.nodeName == 'wxuin':
                wxuin = node.childNodes[0].data
            elif node.nodeName == 'pass_ticket':
                pass_ticket = node.childNodes[0].data

        # print('skey: %s, wxsid: %s, wxuin: %s, pass_ticket: %s' % (skey, wxsid,
        # wxuin, pass_ticket))

        if not all((skey, wxsid, wxuin, pass_ticket)):
            return False


        BaseRequest = {
            'Uin': int(wxuin),
            'Sid': wxsid,
            'Skey': skey,
            'DeviceID': 'e000000000000000',
        }

        self.request.session["wx_base_request"] = BaseRequest
        self.request.session["pass_ticket"] = pass_ticket

        return BaseRequest


    def webwxinit(self, base_uri, baseRequest):

        url = (base_uri + 
            '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
                self.request.session["pass_ticket"], baseRequest['Skey'], int(time.time())) )
        params  = {'BaseRequest': baseRequest }
        headers = {'content-type': 'application/json; charset=UTF-8'}

        r = self.myRequests.post(url=url, data=json.dumps(params),headers=headers)
        r.encoding = 'utf-8'
        data = r.json()

        self.request.session["wx_user"] = data['User']
        #保存cookie
        self.request.session["wx_cookies"] = self.myRequests.cookies.get_dict()
        #保存synccheck ===> 可接收消息, 目前只是为了心跳，否则返回1101
        self.request.session["wx_sync"] = data['SyncKey']['List']

        #从ChatSet中和contactlist中取群号
        roomList = []
        for item in data['ContactList']:
            if item['UserName'].startswith('@@'):
                roomList.append(item['UserName'])
        tmp_chartset = data['ChatSet'].split(',')
        for item in tmp_chartset:
            if item.startswith('@@'):
                roomList.append(item)

        
        if len(roomList)<1:
            return data
        roomList2 = self.groups(roomList)

        #if len(roomList2)<1:
            #return data
        #self.groups(roomList2)
       
        return data

    #拉取群主列表
    def groups(self, roomList):
        #去重
        roomList = list(set(roomList))

        url = '%s/webwxbatchgetcontact?type=ex&r=%s' % (self.request.session["base_uri"], int(time.time()))
        headers = {
            'ContentType': 'application/json; charset=UTF-8',
            'User-Agent' : self.user_agent }
        data = {
            'BaseRequest': self.request.session["wx_base_request"],
            'Count': len(roomList),
            'List': [{
                'UserName': u,
                'ChatRoomId': '', } for u in roomList], }

        r = self.myRequests.post(url, data=json.dumps(data), headers=headers)
        r.encoding = 'utf-8'
        rs = r.json()
        handel_groups(self, rs['ContactList'])

        #groups = []
        #for group in rs['ContactList']:
            #groups.append({'user_name':group['UserName'],'nick_name':group['NickName'], 'img':group['HeadImgUrl'], 'room_id':group['EncryChatRoomId'], 'remark_name':group['RemarkName']})
            #写入数据库
            #groups.append(group['UserName'])
            #self.storeGroups(group)
        #print(len(groups))
        #self.request.session["wx_base_request"]['DeviceID'] = 'e000000000000001'
        return True

    def storeGroups(self,group):

        #过滤emoji奇葩字符
        emoji_pattern = re.compile(
            u"(\ud83d[\ude00-\ude4f])|"  # emoticons
            u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
            u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
            u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
            u"(\ud83c[\udde0-\uddff])|"  # flags (iOS)
            u"(\U00010000-\U0010ffff)|"
            u"([\uD800-\uDBFF][\uDC00-\uDFFF])"
            "+", flags=re.UNICODE
        )
        nick_name = emoji_pattern.sub(r'', group['NickName'])
        try:  
            #只是更新username
            groups_obj = Wxgroups.objects.get(user_id=self.uid, nick_name=nick_name)
            groups_obj.user_name = group['UserName']
            groups_obj.save() 

        except Wxgroups.DoesNotExist:  
            #保存图片路径 uid+attr_id
            #wechat.savaImg(item['HeadImgUrl'], img_name)
            img_name = str(self.uid) + "_" + group['EncryChatRoomId']
            img_name = self.savaImg(group['UserName'], img_name)
            #img_name = self.saveGroupImg("https://wx2.qq.com"+group['HeadImgUrl'], img_name)
            print(img_name)
            Wxgroups.objects.create(
                user_id=self.uid,
                room_id = group['EncryChatRoomId'],
                user_name = emoji_pattern.sub(r'', group['UserName']),
                nick_name = nick_name,
                remark_name = emoji_pattern.sub(r'', group['RemarkName']),
                img = img_name,
            )

    #拉取好友
    def friends(self):
        base_uri = self.request.session["base_uri"]
        pass_ticket = self.request.session["pass_ticket"]
        skey = self.request.session["wx_base_request"]['Skey']

        #url = (base_uri + '/webwxgetcontact?lang=zh_CN&seq=0&pass_ticket=%s&skey=%s&r=%s' % (pass_ticket, skey, int(time.time())) )
        #https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact?lang=zh_CN&pass_ticket=$pass_ticket&seq=0&skey=$skey
        #headers = {'content-type': 'application/json; charset=UTF-8'}
        url = (base_uri + 
        '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (
            pass_ticket, skey, int(time.time())) )
        headers = {'content-type': 'application/json; charset=UTF-8'}

        r = self.myRequests.post(url=url,headers=headers, cookies=self.request.session["wx_cookies"])

        r.encoding = 'utf-8'
        #print(r.text)
        dic = r.json()


        MemberList = dic['MemberList']

        # 倒序遍历,不然删除的时候出问题..
        SpecialUsers = ["newsapp", "fmessage", "filehelper", "weibo", "qqmail", "tmessage", "qmessage", "qqsync", "floatbottle", "lbsapp", "shakeapp", "medianote", "qqfriend", "readerapp", "blogapp", "facebookapp", "masssendapp",
                        "meishiapp", "feedsapp", "voip", "blogappweixin", "weixin", "brandsessionholder", "weixinreminder", "wxid_novlwrv3lqwv11", "gh_22b87fa7cb3c", "officialaccounts", "notification_messages", "wxitil", "userexperience_alarm"]
        
        #print(len(MemberList))
        #fl = open('friends2.json','w+')
        #fl.write(json.dumps(MemberList)) 
        #fl.close()

  
        for i in range(len(MemberList) - 1, -1, -1):
            Member = MemberList[i]
            if Member['VerifyFlag'] & 8 != 0:  # 公众号/服务号
                MemberList.remove(Member)
            elif Member['UserName'] in SpecialUsers:  # 特殊账号
                MemberList.remove(Member)
            elif Member['UserName'].find('@@') != -1:  # 群聊
                print(Member['UserName'])
                MemberList.remove(Member)
            elif Member['UserName'] == self.request.session["wx_user"]['UserName']:  # 自己
                MemberList.remove(Member)
          
        #print(type(MemberList))
        print(len(MemberList))
        fl = open('friends.json','w+')
        fl.write(json.dumps(MemberList)) 
        fl.close()

        #self.sendMsg('hulei testing....')
        #保存第一个图片
        #self.savaImg(MemberList[1]['UserName'],'999_0500')


        return MemberList

    #向好友发送消息
    def sendMsg(self, to_user, msg):
        msg = "[wiki系统推送]" + msg
        #print(msg)
        headers = {'content-type': 'application/json; charset=UTF-8'}
        base_uri = self.request.session["base_uri"]
        url = '%s/webwxsendmsg' % base_uri

        #hulei: @ce8f422afc9a4af182b64aef6e27ba6461d28f45154b795162d667066f3176d3
        #wenqing: @5a9fbdfa8983fa2d3c67fbb7897a1bd8

        #from: @8ff03162d3e1133745aee8ff214939a77cac5548111ee7ed061d77cc301b8f6b
        #weq: @491cc3381f2d940cd20b3c822a6002ce

        data = {
            'BaseRequest': self.request.session["wx_base_request"],
            'Msg': {
                'Type': 1,
                'Content': msg,
                'FromUserName': self.request.session["wx_user"]['UserName'],
                'ToUserName': to_user,
                'LocalID': int(time.time() * 1e4),
                'ClientMsgId': int(time.time() * 1e4),
                }, 
            'Scene': 0, 
        }

        r = self.myRequests.post(url, headers=headers,data=json.dumps(data, ensure_ascii=False).encode('utf8'), cookies=self.request.session["wx_cookies"])

        resp = r.json()
        print(resp)
        if str(resp['BaseResponse']['Ret']) == '0':
            return True

        return False

    #保存头像
    def savaImg(self, username, img_id):
        name = 'static/wechat/'+img_id+'.png'
        print(name)
        default = 'static/wechat/default.png'
        if username.startswith('@@'):
            imageUrl = self.request.session["base_uri"]+'/webwxgetheadimg'
            params = {
                'seq': 0, 
                'userName': username,
                'skey': self.request.session["wx_base_request"]['Skey']
            }

        else:
            imageUrl = self.request.session["base_uri"]+'/webwxgeticon'
            params = {
                'userName': username,
                'skey': self.request.session["wx_base_request"]['Skey'],
                'type': 'big', 
            }

        headers = {'User-agent': self.user_agent}
        r = self.myRequests.get(url=imageUrl, headers=headers, params= params, cookies=self.request.session["wx_cookies"]) #headers?

        imageContent = (r.content)
        if len(imageContent)<10:
            return default

        fileImage = open(name,'wb')
        fileImage.write(imageContent)
        fileImage.close()

        try:
            img = Image.open(name)
            out = img.resize((30, 30),Image.ANTIALIAS) #resize image with high-quality
            out.save(name, 'png')
        except Exception,e:
            print('error:...'+str(e))
            return default

        return name

    #保存临时pdf文件
    def getPdf(self, url):
        pdf_name = str(int(time.time()))+'.pdf'
        #pdf_name ='1517894306.pdf'
        fpath = 'static/attach/'+pdf_name

        try:
            #生成pdf
            pdfkit.from_url(url, fpath)

            #上传pdf到微信
            rs = self.upload_file(fpath, 'doc')
            print(rs)
            print(rs[0], rs[1])
            tmp_pdf_msg = ("<appmsg appid='wxeb7ec651dd0aefa9' sdkver=''><title>[wiki系统推送]%s</title>" % os.path.basename(fpath) +
                "<des></des><action></action><type>6</type><content></content><url></url><lowurl></lowurl>" +
                "<appattach><totallen>%s</totallen><attachid>%s</attachid>" % (rs[0], rs[1]) +
                "<fileext>%s</fileext></appattach><extinfo></extinfo></appmsg>" % os.path.splitext(fpath)[1].replace('.',''))

        except Exception, e:
            print(e)
            tmp_pdf_msg = ''
        finally:
            #无论是否成功, 删除临时pdf
            if os.path.exists(fpath):
                #os.remove(fpath)
                print('needs to be deleted')

        return tmp_pdf_msg

    #上传pdf到文件助手
    def upload_file(self, fpath, fileSymbol):
        fileDict = {}
        with open(fpath, 'rb') as f:
            file_ = f.read()

        #file_ = open(fpath, 'rb').read()
        fileSize = len(file_)
        fileDict['fileMd5'] = hashlib.md5(file_).hexdigest()
        fileDict['file_'] = io.BytesIO(file_)

        chunks = int((fileSize - 1) / 524288) + 1

        uploadMediaRequest = json.dumps(OrderedDict([
            ('UploadType', 2),
            ('BaseRequest', self.request.session["wx_base_request"]),
            ('ClientMediaId', int(time.time() * 1e4)),
            ('TotalLen', fileSize),
            ('StartPos', 0),
            ('DataLen', fileSize),
            ('MediaType', 4),
            ('FromUserName', self.request.session["wx_user"]['UserName']),
            ('ToUserName', 'filehelper'),
            ('FileMd5', fileDict['fileMd5'])]
            ), separators = (',', ':'))

        #r = {'BaseResponse': {'Ret': -1005, 'ErrMsg': 'Empty file detected'}}
        #fileSymbol = 'pdf'
        print(uploadMediaRequest)
        for chunk in range(chunks):
            r = self.upload_chunk_file(fpath, fileSymbol, fileSize,
                fileDict['file_'], chunk, chunks, uploadMediaRequest).json()

        fileDict['file_'].close()
        print(r)
        if r and isinstance(r, dict):
            mediaId = r['MediaId']
            return (str(fileSize), mediaId)
        else:
            return False

    # 分段上传
    def upload_chunk_file(self, fileDir, fileSymbol, fileSize,
        file_, chunk, chunks, uploadMediaRequest):

        url = 'https://file.wx2.qq.com/cgi-bin/mmwebwx-bin/webwxuploadmedia?f=json'
        #https://file2.wx.qq.com/cgi-bin/mmwebwx-bin/webwxuploadmedia?f=json

        # save it on server
        fileType = mimetypes.guess_type(fileDir)[0] or 'application/octet-stream'
        files = OrderedDict([
            ('id', (None, 'WU_FILE_0')),
            ('name', (None, os.path.basename(fileDir))),
            ('type', (None, fileType)),
            ('lastModifiedDate', (None, time.strftime('%a %b %d %Y %H:%M:%S GMT+0800 (CST)'))),
            ('size', (None, str(fileSize))),
            ('chunks', (None, None)),
            ('chunk', (None, None)),
            ('mediatype', (None, fileSymbol)),
            ('uploadmediarequest', (None, uploadMediaRequest)),
            ('webwx_data_ticket', (None, self.request.session["wx_cookies"]["webwx_data_ticket"])),
            ('pass_ticket', (None, self.request.session["pass_ticket"])),
            ('filename' , (os.path.basename(fileDir), file_.read(524288), 'application/octet-stream'))])
        
        if chunks == 1:
            del files['chunk']; del files['chunks']
        else:
            files['chunk'], files['chunks'] = (None, str(chunk)), (None, str(chunks))

        headers = {'User-agent': self.user_agent}
        return self.myRequests.post(url, files=files, headers=headers, cookies=self.request.session["wx_cookies"])

    #发送文件消息
    def sendAppMsg(self, to_user, fmsg):

        headers = {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json;charset=UTF-8', 
        }
        base_uri = self.request.session["base_uri"]
        url = '%s/webwxsendappmsg?fun=async&f=json' % base_uri
        data = {
            'BaseRequest': self.request.session["wx_base_request"],
            'Msg': {
                'Type': 6,
                'Content': fmsg,
                'FromUserName': self.request.session["wx_user"]['UserName'],
                'ToUserName': to_user,
                'LocalID': int(time.time() * 1e4),
                'ClientMsgId': int(time.time() * 1e4),
                }, 
            'Scene': 0, 
        }

        r = self.myRequests.post(url, headers=headers,data=json.dumps(data, ensure_ascii=False).encode('utf8'), cookies=self.request.session["wx_cookies"])

        resp = r.json()
        print(resp)
        if str(resp['BaseResponse']['Ret']) == '0':
            return True

        return False

    #心跳检查
    def synccheck(self):
        base_uri = self.request.session["base_uri"]
        url = base_uri + '/synccheck'
        SyncKey = self.request.session["wx_sync"]
        
        SyncKeyItems = ['%s_%s' % (item['Key'], item['Val']) for item in SyncKey]
        SyncKeyStr = '|'.join(SyncKeyItems)
        BaseRequest = self.request.session["wx_base_request"]

        params = {
            'skey': BaseRequest['Skey'],
            'sid': BaseRequest['Sid'],
            'uin': BaseRequest['Uin'],
            'deviceId': BaseRequest['DeviceID'],
            'synckey': SyncKeyStr,
            'r': int(time.time()),
        }
        cookies = self.request.session["wx_cookies"]
        try:
            r = self.myRequests.get(url=url,params=params, cookies=cookies, timeout=2)
            r.encoding = 'utf-8'
            data = r.text
            print(data)
        except Exception,e:
            print(e)
            return False

        regx = r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}'
        pm = re.search(regx, data)
        retcode = pm.group(1)
   

        if retcode != '0':
            #网络断开
            return False
        else:
            #延续syncckey
            pass_ticket = urllib.quote_plus(self.request.session["pass_ticket"])

            url = base_uri + '/webwxsync?lang=zh_CN&skey=%s&sid=%s&pass_ticket=%s' % (BaseRequest['Skey'], BaseRequest['Sid'], pass_ticket)
            params = {
                'BaseRequest': BaseRequest,
                'SyncKey': SyncKey,
                'rr': ~int(time.time()),
            }
            headers = {'content-type': 'application/json; charset=UTF-8'}

            r = self.myRequests.post(url=url, data=json.dumps(params), headers=headers, cookies=cookies,timeout=2)
            r.encoding = 'utf-8'
            data = r.json()
            print(data)
            #更新synckey
            self.request.session["wx_sync"] = data['SyncKey']['List']

            return True


    def savaImgTest(self, url):
        name = 'static/wechat/test.png'
      
        r = self.myRequests.get(url) #headers?
        imageContent = (r.content)

        fileImage = open(name,'wb')
        fileImage.write(imageContent)
        fileImage.close()

        try:
            img = Image.open(name)
            out = img.resize((30, 30),Image.ANTIALIAS) #resize image with high-quality
            out.save(name, 'png')
        except:
            print('error:...')

     #保存群组头像【暂时没用】
    def saveGroupImg(self, url, name):
        name = 'static/wechat/'+name+'.png'
        default = 'static/wechat/default.png'

        print(url)
        headers = {'User-agent': self.user_agent}
        r = self.myRequests.get(url=url, headers=headers, cookies=self.request.session["wx_cookies"]) #headers?
        print(r.text)

        imageContent = (r.content)
        if len(imageContent)<10:
            return default

        fileImage = open(name,'wb')
        fileImage.write(imageContent)
        fileImage.close()

        try:
            img = Image.open(name)
            out = img.resize((30, 30),Image.ANTIALIAS) #resize image with high-quality
            out.save(name, 'png')
        except Exception,e:
            print('error:...'+str(e))
            return default

        return name

    #好友分析图片并上传微信
    def getAnalysis(self, friends):

        sex_dic = {'unknow': 0, 'male':0, 'female':0}
        province = {'未知':0, '国外':0}
        text = ""
        check_en = re.compile(r'[A-Za-z]',re.S)

        for item in friends:
            
            #性别分析   
            if item.sex == '1':
                sex_dic['male'] += 1
            elif item.sex == '2':
                sex_dic['female'] += 1
            else:
                sex_dic['unknow'] += 1

            #省份分析
            if item.province == '':
                province['未知'] += 1
            elif len(re.findall(check_en, item.province)):
                province['国外'] += 1
            else:
                if province.has_key(item.province):
                    province[item.province] += 1
                else:
                    province[item.province] = 1

            #云词分析
            sign = item.sign.strip()
            sign = sign.replace("class", "").replace("emoji", "").replace("span","").replace(" ", "")
            if len(sign)>0 :

                text += ' '.join(jieba.cut(sign))
                text += ' '

        
        #设置中文字体
        font = fontmanager.FontProperties(fname='C:\Windows\Fonts\simfang.ttf')
        pname = 'static/attach/'+str(int(time.time())) + '_'
        arr = [ pname+ '1.png',  pname+ '2.png',  pname+ '3.png',  pname+ '4.png']

        #画性别图
        x_label = [0, 1, 2]
        #注意，遍历之后顺序可能打乱
        y_label = [sex_dic['unknow'], sex_dic['male'],sex_dic['female']]
     
        
        plt.close('all')
        plt.xticks((0,1,2),("未知", "男性", "女性"), FontProperties=font)
        plt.bar(range(len(y_label)), y_label, width=0.7, color = 'byg')

        #plt.xlabel(u"性别", FontProperties=font)
        plt.ylabel(u'数目', FontProperties=font)
        plt.title(u'性别分布', y=1.08, FontProperties=font)
        
      
        for a,b in zip(x_label, y_label):
            #b = str(b)
            plt.text(a, b, '%.0f'%b, ha= 'center', va='bottom',fontsize = 7)
        plt.savefig(arr[0], format='png')


        #省份分析
        pname = province.keys()
        pvals = province.values()
        pindex = pvals.index(max(pvals))

        colors = ['red', 'yellow', 'blue', 'green']
        #explode = (0.05,0,0,0,0,0,0,0,0,0)
        plt.close('all')
        plt.pie(pvals, labels= pname, colors= colors, labeldistance=1.1,
                autopct='%3.0f%%', shadow=False, startangle=90, pctdistance= 0.8)
        plt.axis('equal')
        plt.title(u'省份分布', y=1.08, FontProperties=font)
        plt.legend(loc='upper left', bbox_to_anchor=(-0.1, 1))
        plt.grid()
        plt.savefig(arr[1], format='png')


        #云词分析
        wc=WordCloud( 
            background_color='white', 
            #mask=backgroud_Image, 
            font_path='C:\Windows\Fonts\simfang.ttf', 
            #若是有中文的话，这句代码必须添加，不然会出现方框，不出现汉字 
            max_words=2000, 
            stopwords=STOPWORDS, 
            max_font_size=150, 
            random_state=30 
        )
        wc.generate_from_text(text)
        plt.close('all')
        plt.title(u'签名关键词分析', y=1.08)
        plt.imshow(wc) 
        plt.axis('off') 
        plt.savefig(arr[2], format='png')


        toImage = Image.new('RGBA',(640, 1440))
        for i in range(3):
            fromImge = Image.open(arr[i])
            # loc = ((i % 2) * 200, (int(i/2) * 200))
            loc = (0, i * 480)
            print(loc)
            toImage.paste(fromImge, loc)

        toImage.save(arr[3])

        try:
            #生成图片

            #上传pdf到微信
            rs = self.upload_file(arr[3], 'pic')

            send_rs = rs[1]

        except Exception, e:
            print(e)
            send_rs = ''
        finally:
            #无论是否成功, 删除临时pdf
            for pic in arr:
                if os.path.exists(pic):
                    #os.remove(pic)
                    pass

        return send_rs

    #发送图片
    def sendPic(self, toUserName, mediaId):
        url = '%s/webwxsendmsgimg?fun=async&f=json' % self.request.session["base_uri"]
        data = {
            'BaseRequest': self.request.session["wx_base_request"],
            'Msg': {
                'Type': 3,
                'MediaId': mediaId,
                'FromUserName': self.request.session["wx_user"]['UserName'],
                'ToUserName': toUserName,
                'LocalID': int(time.time() * 1e4),
                'ClientMsgId': int(time.time() * 1e4), },
            'Scene': 0, }

        headers = {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json;charset=UTF-8', }
        r = self.myRequests.post(url, headers=headers,
            data=json.dumps(data, ensure_ascii=False).encode('utf8'), cookies=self.request.session["wx_cookies"])
        resp = r.json()
        print(resp)

        if str(resp['BaseResponse']['Ret']) == '0':
            return True
        else:
            return False





