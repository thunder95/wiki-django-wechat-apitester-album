#!/usr/bin/env python
# encoding=utf-8
from __future__ import print_function

import threading
from .models import Wxgroups,Wxfriends
import sys
import time 
import json
import re
import hashlib

reload(sys)
sys.setdefaultencoding("utf-8")

class GroupsThread(threading.Thread):  
    def __init__ (self, gitem):
        threading.Thread.__init__(self)
        self.gitem = gitem

    def run(self):  
        group = self.gitem

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
            print(group['UserName'])
            groups_obj = Wxgroups.objects.get(user_id=uid, nick_name=nick_name)
            groups_obj.user_name = group['UserName']
            groups_obj.save() 

            #Wxgroups.objects.filter(user_id=uid, nick_name=nick_name).update(user_name=group['UserName'])

        except Wxgroups.DoesNotExist:  
            #保存图片路径 uid+attr_id
            #wechat.savaImg(item['HeadImgUrl'], img_name)
            img_name = str(uid) + "_" + group['EncryChatRoomId']
            img_name = wechat_obj.savaImg(group['UserName'], img_name)
            #img_name = self.saveGroupImg("https://wx2.qq.com"+group['HeadImgUrl'], img_name)
            print(img_name)
            Wxgroups.objects.create(
                user_id=uid,
                room_id = group['EncryChatRoomId'],
                user_name = emoji_pattern.sub(r'', group['UserName']),
                nick_name = nick_name,
                remark_name = emoji_pattern.sub(r'', group['RemarkName']),
                img = img_name,
            )


#好友
class FriendsThread(threading.Thread):  
    def __init__ (self, fitem):
        threading.Thread.__init__(self)
        self.fitem = fitem

    def run(self):
        item = self.fitem
        #attr也不唯一, 这里使用 arr+nick的md5
        m5 = hashlib.md5()   
        m5.update(str(item['AttrStatus'])+item['NickName'])
        item['AttrStatus'] = m5.hexdigest() 
        try:  
            

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

            #img_name = str(uid)+ "_"+ str(item['AttrStatus'])
            
            try:  
                #只是更新username
                #begin = time.time()

                friends_obj = Wxfriends.objects.get(user_id=uid, attr_id=item['AttrStatus'])
                friends_obj.user_name =item['UserName']
                friends_obj.save() 
                
                #经测试 update还要慢一些
                #Wxfriends.objects.filter(user_id=uid, attr_id=item['AttrStatus']).update(user_name=item['UserName'])

                #stop = time.time()
                #print(str(item['AttrStatus'])+"=====>"+str(stop-begin))

            except Wxfriends.DoesNotExist: 
                try:
                    img_name = wechat_obj.savaImg(item['UserName'], item['AttrStatus'])
                    print(img_name)

                    Wxfriends.objects.create(
                        user_id=uid,
                        attr_id=item['AttrStatus'],
                        user_name =item['UserName'],
                        nick_name =emoji_pattern.sub(r'', item['NickName']),
                        remark_name =item['RemarkName'],
                        province =item['Province'],
                        city =item['City'],
                        sex =item['Sex'],
                        #img =item['HeadImgUrl'],
                        img = img_name,
                        sign = emoji_pattern.sub(r'', item['Signature']),
                        contact_flag =item['ContactFlag'],
                        sns_flag =item['SnsFlag']
                    )
                except Exception, e:
                    print(item['AttrStatus'], e)

        except Exception, e:
                print(item['AttrStatus'], e)



def handel_friends(request):
    from .wechat import Wechat
    init = time.time()
    global uid
    uid = request.user.id
    global wechat_obj
    wechat_obj = Wechat(request)

    print('get friends...')
    friends = wechat_obj.friends()

    #多线程写入数据库
    print('threading start....'+str(len(friends)))
    start = time.time()
    thread_list = [FriendsThread(item) for item in friends]
    for t in thread_list:
        t.setDaemon(True)
        t.start()
    for t in thread_list:
        t.join()

    end = time.time()
    print(start-init)
    print(end-start)

    print('threading stop....')


def handel_groups(wechat, groups):

    global uid
    uid = wechat.uid
    global wechat_obj
    wechat_obj = wechat

    print('get groups...')
  
    #多线程写入数据库
    print('threading start....')
    start = time.time()
    thread_list = [GroupsThread(item) for item in groups]
    for t in thread_list:
        t.setDaemon(True)
        t.start()
    for t in thread_list:
        t.join()

    end = time.time()
    print(end-start)
    print('threading stop....')


if __name__ == '__main__':
    print('this is test...')





