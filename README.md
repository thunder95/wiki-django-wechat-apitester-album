此项目主要是为了学习python而做的业余练习项目，请勿用作任何的商业用途，尚有诸多bugs，后期慢慢维护

项目功能：

用户管理
文档类型管理
文档管理，维护基本属性
ztree插件维护文档目录
通过ueditor和markdown，编辑文件内容
根据文档ID，在前台页面通过目录结构查看
每个单页目录，可以将连接、文本和pdf分享发送至微信好友和群聊，额外的功能做了个好友统计分析可发送图片
基于markdownAPI文档模板建立
后端解析相关参数信息，可整个API全部通测，也可以单个API测试，所有的测试会自动登录并返回结果检验
测试报告是一个单独的html页面，可方便的查看json格式信息，通过浏览器也可导出pdf，这里没做自动导出pdf功能
nginx部署 https://www.cnblogs.com/CongZhang/p/6548529.html

部署过程：

检查python版本 2.7

创建项目wiki.qingsonglaoban.com,将项目文件复制上去

安装 pip install django==1.9.13 PyMySQL django-tagging pillow（pip可能需要更新：pip install --upgrade pip）

setting中修改数据库配置， 删除mwiki\blog\migrations中的文件只剩下init.py

初始化数据库 python manage.py makemigrations python manage.py migrate

创建超级管理员 python manage.py createsuperuser， 账号admin 密码qslb2018

运行服务器 python manage.py runserver 0.0.0.0:8090

若有nginx部署

pip install uwsgi (centos7报错就运行下：yum install python-devel)
centos下的坑 http://www.linuxidc.com/Linux/2016-10/135743p3.htm
[uwsgi]

env = DJANGO_PRODUCTION_SETTINGS=TRUE

chdir = /home/wiki.qingsonglaoban.com module = zer0Blog.wsgi

master=True processes = 4 http = :8091 vaccum=True socket = 127.0.0.1:8092 touch-reload = /home/wiki.qingsonglaoban.com daemonize = /var/log/uwsgi.log

复制静态文件： STATIC_ROOT = os.path.join(BASE_DIR, 'static') python manage.py collectstatic


[2018-03-30]新增:
前台页面cms的后台管理
接口文档的测试功能
首页缓存

注意重启uswgi否则代码缓存:
killall  -9 uwsgi
killall -s HUP /var/www/uwsgi 
killall -s HUP /usr/local/bin/uwsgi
uwsgi --ini uwsgi.ini&

django+datatables: http://www.fdevops.com/?p=502