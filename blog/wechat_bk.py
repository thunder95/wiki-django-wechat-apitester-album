#!/usr/bin/env python
# encoding=utf-8
from __future__ import print_function

import os
import requests
import re
import time
import xml.dom.minidom
import json
import sys
import math
import subprocess
import ssl
import threading
import urllib3
from PIL import Image
import io
import pdfkit
import sys
import hashlib
from collections import OrderedDict
import mimetypes, hashlib

reload(sys)
sys.setdefaultencoding("utf-8")


class Wechat:
    def __init__(self, request):
        self.request = request

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

                #保存cookies
                self.request.session["wx_cookies"] = self.myRequests.cookies.get_dict()
                print(self.request.session["wx_cookies"])
                #拉取好友
                #self.friends()


        elif code == '408':  # 超时
            #此时会更新qr
            pass

        print(code)
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

        #fl = open('init.json','w')
        #fl.write(r.text)
        #fl.close()
      

       
        return data


    #拉取好友和聊天室
    def friends(self):

        def _get_contact(seq=0):
            print('start...'+str(seq))
            base_uri = self.request.session["base_uri"]
            pass_ticket = self.request.session["pass_ticket"]
            skey = self.request.session["wx_base_request"]['Skey']

            url = '%s/webwxgetcontact?r=%s&seq=%s&skey=%s' % (base_uri,
                int(time.time()), seq, skey)

            headers = {
                'ContentType': 'application/json; charset=UTF-8',
                'User-Agent' : self.user_agent, 
            }
            try:
                r = self.myRequests.get(url, headers=headers, cookies=self.request.session["wx_cookies"])
            except Exception,e:
                print(e)
                return 0, []

            j = json.loads(r.content.decode('utf-8', 'replace'))
            return j.get('Seq', 0), j.get('MemberList')

        seq, memberList = 0, []
        while 1:
            seq, batchMemberList = _get_contact(seq)
            memberList.extend(batchMemberList)
            if seq == 0:
                break
        chatroomList, otherList = [], []
        for m in memberList:
            if m['Sex'] != 0:
                otherList.append(m)
            elif '@@' in m['UserName']:
                chatroomList.append(m)
            elif '@' in m['UserName']:
                # mp will be dealt in update_local_friends as well
                otherList.append(m)
        
        fl = open('chatroom.json','w')
        fl.write(json.dumps(chatroomList))
        fl.close()

        fl = open('users.json','w')
        fl.write(json.dumps(otherList))
        fl.close()
        


        return otherList

    #向好友发送消息
    def sendMsg(self, to_user, msg):
        #msg = "[wiki系统推送]" + msg
        print(msg)
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
        print(img_id)
        name = 'static/wechat/'+img_id+'.png'
        default = 'static/wechat/default.png'
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
        #pdf_name ='1517814209.pdf'
        fpath = 'static/attach/'+pdf_name

        try:
            #生成pdf
            pdfkit.from_url(url, fpath)

            #上传pdf到微信
            tmp_pdf_msg = self.upload_pdf(fpath)
        except Exception, e:
            print(e)
            tmp_pdf_msg = ''
        finally:
            #无论是否成功, 删除临时pdf
            if os.path.exists(fpath):
                os.remove(fpath)
                #print('needs to be deleted')

        return tmp_pdf_msg

    #上传pdf到文件助手
    def upload_pdf(self, fpath):
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
        fileSymbol = 'pdf'
        for chunk in range(chunks):
            r = self.upload_chunk_file(fpath, fileSymbol, fileSize,
                fileDict['file_'], chunk, chunks, uploadMediaRequest).json()

        fileDict['file_'].close()

        if r and isinstance(r, dict):
            mediaId = r['MediaId']
            return ("<appmsg appid='wxeb7ec651dd0aefa9' sdkver=''><title>[wiki系统推送]%s</title>" % os.path.basename(fpath) +
                "<des></des><action></action><type>6</type><content></content><url></url><lowurl></lowurl>" +
                "<appattach><totallen>%s</totallen><attachid>%s</attachid>" % (str(fileSize), mediaId) +
                "<fileext>%s</fileext></appattach><extinfo></extinfo></appmsg>" % os.path.splitext(fpath)[1].replace('.',''))
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





