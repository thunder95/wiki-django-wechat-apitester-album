# -*- coding:utf-8 -*-
from __future__ import division

import datetime
import time
import json
import os
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.template.response import TemplateResponse
from django.views.generic import View, ListView, CreateView, UpdateView
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from zer0Blog.settings import MEDIA_ROOT, MEDIA_URL, image_type

from zer0Blog.settings import PERNUM
from blog.pagination import paginator_tool
from .models import Post, Catalogue, Carousel, User, EDITOR, Product, Docutype, Content, Wxfriends, Wxgroups, Media, Youzipic, Growth, Events, Album
from thumbnail import ThumbnailTool
from PIL import Image
from .wechat import Wechat
from .wechat_db import handel_friends
import re
import sys
from .rest_api import apidoc
from django.core.cache import cache

reload(sys)
sys.setdefaultencoding("utf-8")


@csrf_exempt
def markdown_image_upload_handler(request):
    # 要返回的数据字典，组装好后，序列化为json格式
    if request.method == "POST":
        result = {}
        try:
            file_img = request.FILES['editormd-image-file']
            file_suffix = os.path.splitext(file_img.name)[len(os.path.splitext(file_img.name)) - 1]
            filename = uuid.uuid1().__str__() + file_suffix

            # 检查图片格式
            if file_suffix not in image_type:
                result['success'] = 0
                result['message'] = "上传失败，图片格式不正确"
            else:
                path = MEDIA_ROOT + "/post/"
                if not os.path.exists(path):
                    os.makedirs(path)

                # 图片宽大于825的时候，将其压缩到824px，刚好适合13吋pc的大小
                img = Image.open(file_img)
                width, height = img.size
                if width > 824:
                    img = ThumbnailTool.constrain_thumbnail(img, times=width/824.0)

                file_name = path + filename
                img.save(file_name)

                file_img_url = "http://" + request.META['HTTP_HOST'] + MEDIA_URL + "post/" + filename

                result['success'] = 1
                result['message'] = "上传成功"
                result['url'] = file_img_url

        except Exception, e:
            result['success'] = 0
            result['message'] = e
            print e

        return HttpResponse(json.dumps(result))


@csrf_exempt
def tinymce_image_upload_handler(request):
    if request.method == "POST":
        try:
            file_img = request.FILES['tinymce-image-file']
            file_suffix = os.path.splitext(file_img.name)[len(os.path.splitext(file_img.name)) - 1]
            # 检查图片格式
            if file_suffix not in image_type:
                return HttpResponse("请上传正确格式的图片文件")
            filename = uuid.uuid1().__str__() + file_suffix

            # 图片宽大于824的时候，将其压缩到824px，刚好适合13吋pc的大小
            img = Image.open(file_img)
            width, height = img.size
            if width > 824:
                img = ThumbnailTool.constrain_thumbnail(img, times=width/824.0)

            path = MEDIA_ROOT + "/post/"
            if not os.path.exists(path):
                os.makedirs(path)

            file_name = path + filename
            img.save(file_name)

            file_img_url = "http://" + request.META['HTTP_HOST'] + MEDIA_URL + "post/" + filename

            context = {
                'result': "file_uploaded",
                'resultcode': "ok",
                'file_name': file_img_url
            }

        except Exception, e:
            context = {
                'result': e,
                'resultcode': "failed",
            }
            print e

        return TemplateResponse(request, "admin/plugin/ajax_upload_result.html", context)


def avatar_image_upload_handler(request):
    if request.method == "POST":
        try:
            file_img = request.FILES['avatar']
            file_suffix = os.path.splitext(file_img.name)[len(os.path.splitext(file_img.name)) - 1]
            # 检查图片格式
            if file_suffix not in image_type:
                return HttpResponse("请上传正确格式的图片文件")
            filename = uuid.uuid1().__str__() + file_suffix

            # 把头像压缩成90大小
            img = Image.open(file_img)
            img = ThumbnailTool.constrain_len_thumbnail(img, 90)

            path = MEDIA_ROOT + "/avatar/"
            if not os.path.exists(path):
                os.makedirs(path)

            file_name = path + filename
            img.save(file_name)

            file_img_url = "http://" + request.META['HTTP_HOST'] + MEDIA_URL + "avatar/" + filename
            user = request.user
            user.avatar_path = file_img_url
            user.save()

        except Exception, e:
            print e

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', "/"))

#####################################分割线###########################################
#保存目录
def update_product_menu(request):
    result = {}
    result['success'] = 0
    result['message'] = '请求方式错误'

    #只接受post
    if request.method == "POST":
        menu = request.POST.get("menu", "")
        pk = request.POST.get("pk", "")

        product = Product.objects.get(id=pk)
        
        product.menu_json = menu
        product.save()

        result['success'] = 1
        result['message'] = '目录更新成功'

    return HttpResponse(json.dumps(result))


    

#保存文档,内容
def update_product_content(request):
    result = {}
    result['success'] = 0
    result['message'] = '请求方式错误'

    #只接受post
    if request.method == "POST":
        menu_id = request.POST.get("menu_id", "")
        product_id = request.POST.get("product_id", "")
        content = request.POST.get("content", "")
        content_type = request.POST.get("content_type", "")

        try:  
            content_obj = Content.objects.get(product_id=product_id, menu_id=menu_id)
            content_obj.content_type = content_type
            content_obj.content = content
            content_obj.save() 
        except Content.DoesNotExist:  
            Content.objects.create(
                menu_id = menu_id,
                product_id = product_id,
                content = content,
                content_type = content_type
            )

        result['success'] = 1
        result['message'] = '内容更新成功'

    return HttpResponse(json.dumps(result))
  
#获取文档,内容
def retrieve_product_content(request):
    result = {}
    result['success'] = 0
    result['message'] = '请求方式错误'
    result['data'] = {}

    #只接受post
    if request.method == "POST":
        menu_id = request.POST.get("menu_id", "")
        product_id = request.POST.get("product_id", "")
      
        try:  
            content_obj = Content.objects.get(product_id=product_id, menu_id=menu_id)
            result['data']['content_type'] = content_obj.content_type
            result['data']['content'] = content_obj.content  
        except Content.DoesNotExist:  
            result['data']['content_type'] = 0
            result['data']['content'] = ''

        result['success'] = 1
        result['message'] = '内容获取成功'

    return HttpResponse(json.dumps(result))
   
# 产品名称列表
class ProductView(ListView):
    template_name = 'admin/product_admin.html'
    context_object_name = 'product_list'
    

    def get_queryset(self):
        user = self.request.user
        self.kwd = self.kwargs.get('kwd') or self.request.GET.get('kwd') or ''

        p_obj = Product.objects
        if len(self.kwd)>0:
            p_obj = p_obj.filter(name__icontains=self.kwd)

        if user.is_superuser:
            product_list = p_obj.all()
        else:
            product_list = p_obj.filter(author_id=user.id).exclude(is_deleted=1)

        return product_list

    def get_context_data(self, **kwargs):
        context = super(ProductView, self).get_context_data(**kwargs)
        page = self.kwargs.get('page') or self.request.GET.get('page') or 1
        objects, page_range = paginator_tool(pages=page, queryset=self.object_list, display_amount=PERNUM)
        context['page_range'] = page_range
        context['objects'] = objects
        context['is_superuser'] = self.request.user.is_superuser
        context['kwd'] = self.kwd
        return context

class DeleteProduct(View):
    def get(self, request, *args, **kwargs):
        # 获取当前用户
        user = self.request.user
        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)
        # 获取删除的博客ID
        pkey = self.kwargs.get('pk')
        product = Product.objects.filter(author_id=user.id).get(pk=pkey)
        product.is_deleted = 1
        product.save()
        return HttpResponseRedirect('/admin/')

class RestoreProduct(View):
    def get(self, request, *args, **kwargs):
        # 获取当前用户
        user = self.request.user
        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)
        # 获取删除的博客ID
        pkey = self.kwargs.get('pk')
        product = Product.objects.filter(author_id=user.id).get(pk=pkey)
        product.is_deleted = 0
        product.save()
        return HttpResponseRedirect('/admin/')


class NewProduct(CreateView):
    template_name = 'admin/product_new.html'
    model = Product
    fields = ['name', 'docutype', 'description']

    def get_context_data(self, **kwargs):
        context = super(NewProduct, self).get_context_data(**kwargs)
        context['docutype_list'] = Docutype.objects.filter(is_deleted=0).all()
        return context

#post提交保存
class AddProduct(View):
    def post(self, request):
        user = request.user
        name = request.POST.get("name", "")
        description = request.POST.get("description", "")
        docutype = request.POST.get("docutype", "")
        docutypet_foreignkey = Docutype.objects.get(pk=docutype)

        #创建文档
        post_obj = Product.objects.create(
            name=name,
            author=user,
            docutype=docutypet_foreignkey,
            description=description,
            menu_json = '[{ id:1, pId:0, name:"根目录"},{lastId:2}]'
        )

        return HttpResponseRedirect('/admin/')

#编辑
class ProductUpdate(UpdateView):
    template_name = 'admin/product_update.html'
    model = Product
    fields = ['name', 'docutype', 'description']

    def get_context_data(self, **kwargs):
        context = super(ProductUpdate, self).get_context_data(**kwargs)
        context['docutype_list'] = Docutype.objects.all()
        return context


class UpdateProduct(View):
    def post(self, request, *args, **kwargs):

        # 将文件路径和其余信息存入数据库
        name = request.POST.get("name", "")
        description = request.POST.get("description", "")
        docutype = request.POST.get("docutype", "")
        docutypet_foreignkey = Docutype.objects.get(pk=docutype)

        pkey = self.kwargs.get('pk')
        product = Product.objects.get(id=pkey)
        
        product.name = name
        product.description = description
        product.docutype = docutypet_foreignkey
        product.save()

        return HttpResponseRedirect('/admin')


#文档内容 目录编辑页
class ProductMenu(UpdateView):
    template_name = 'admin/content_admin.html'
    model = Product
    fields = ['menu_json']

    def get_context_data(self, **kwargs):
        context = super(ProductMenu, self).get_context_data(**kwargs)

        #查询是否有响应的内容, 默认该文档的根目录
        pkey = self.kwargs.get('pk')

        try:  
            content = Content.objects.get(product_id=pkey, menu_id=1)
            context['content_type'] = content.content_type
            #context['content'] = content.content.replace("\n", "<br>").replace('\t','')
            context['content'] = ''
        except Content.DoesNotExist:  
            #默认editor编辑器
            context['content_type'] = 0
            context['content'] = ''

        return context


# 文档类型列表
class DocutypeView(ListView):
    template_name = 'admin/docutype_admin.html'
    context_object_name = 'docu_list'

    def get_queryset(self):
        user = self.request.user
        docu_list = Docutype.objects.filter(author_id=user.id).exclude(is_deleted=1)
        return docu_list

    def get_context_data(self, **kwargs):
        context = super(DocutypeView, self).get_context_data(**kwargs)
        page = self.kwargs.get('page') or self.request.GET.get('page') or 1
        objects, page_range = paginator_tool(pages=page, queryset=self.object_list, display_amount=PERNUM)
        context['page_range'] = page_range
        context['objects'] = objects
        context['editor_list'] = EDITOR
        return context

class DeleteDocutype(View):
    def get(self, request, *args, **kwargs):
        # 获取当前用户
        user = self.request.user
        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)
        # 获取删除的博客ID
        pkey = self.kwargs.get('pk')
        docutype = Docutype.objects.filter(author_id=user.id).get(pk=pkey)
        docutype.is_deleted = 1
        docutype.save()
        return HttpResponseRedirect('/admin/docutype')


class NewDocutype(CreateView):
    template_name = 'admin/docutype_new.html'
    model = Docutype
    fields = ['name']

    def get_context_data(self, **kwargs):
        context = super(NewDocutype, self).get_context_data(**kwargs)
        return context

#post提交保存
class AddDocutype(View):
    def post(self, request):
        # 获取当前用户
        user = request.user
        # 获取评论
        name = request.POST.get("name", "")


        post_obj = Docutype.objects.create(
            name=name,
            author=user,
        )

        return HttpResponseRedirect('/admin/docutype')

#编辑
class DocutypeUpdate(UpdateView):
    template_name = 'admin/docutype_update.html'
    model = Docutype
    fields = ['name']

    def get_context_data(self, **kwargs):
        context = super(DocutypeUpdate, self).get_context_data(**kwargs)
        return context


class UpdateDocutype(View):
    def post(self, request, *args, **kwargs):

        # 将文件路径和其余信息存入数据库
        name = request.POST.get("name", "")
        pkey = self.kwargs.get('pk')
        docutype = Docutype.objects.get(id=pkey)
        docutype.name = name
        docutype.save()

        return HttpResponseRedirect('/admin/docutype')


#####################################分割线###########################################
class PostView(ListView):
    template_name = 'admin/blog_admin.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        user = self.request.user
        post_list = Post.objects.filter(author_id=user.id).exclude(status=2)
        return post_list

    def get_context_data(self, **kwargs):
        context = super(PostView, self).get_context_data(**kwargs)
        page = self.kwargs.get('page') or self.request.GET.get('page') or 1
        objects, page_range = paginator_tool(pages=page, queryset=self.object_list, display_amount=PERNUM)
        context['page_range'] = page_range
        context['objects'] = objects
        context['editor_list'] = EDITOR
        return context


class DeletePost(View):
    def get(self, request, *args, **kwargs):
        # 获取当前用户
        user = self.request.user
        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)
        # 获取删除的博客ID
        pkey = self.kwargs.get('pk')
        post = Post.objects.filter(author_id=user.id).get(pk=pkey)
        post.status = 2
        post.save()
        return HttpResponseRedirect('/admin/')


class NewPost(CreateView):
    template_name = 'admin/post_new.html'
    model = Post
    fields = ['title']

    def get_context_data(self, **kwargs):
        context = super(NewPost, self).get_context_data(**kwargs)
        context['catalogue_list'] = Catalogue.objects.all()
        return context


class UpdatePostIndexView(UpdateView):
    template_name = 'admin/post_new.html'
    model = Post
    fields = ['title']

    def get_context_data(self, **kwargs):
        context = super(UpdatePostIndexView, self).get_context_data(**kwargs)
        context['catalogue_list'] = Catalogue.objects.all()
        return context


class AddPost(View):
    def post(self, request):
        # 获取当前用户
        user = request.user
        # 获取评论
        title = request.POST.get("title", "")
        content = request.POST.get("content", "")
        catalogue = request.POST.get("catalogue", "")
        tags = request.POST.getlist("tag", "")
        action = request.POST.get("action", "0")

        catalogue_foreignkey = Catalogue.objects.get(name=catalogue)
        editor_choice = user.editor_choice

        post_obj = Post.objects.create(
            title=title,
            author=user,
            content=content,
            catalogue=catalogue_foreignkey,
            status=action,
            editor_choice=editor_choice,
        )

        post_obj.update_tags(tags)

        return HttpResponseRedirect('/admin/')


class UpdateDraft(View):
    def post(self, request, *args, **kwargs):
        # 获取当前用户
        user = request.user
        # 获取要修改的博客
        pkey = self.kwargs.get('pk')
        post = Post.objects.filter(author_id=user.id).get(pk=pkey)
        # 获取评论
        title = request.POST.get("title", "")
        content = request.POST.get("content", "")
        catalogue = request.POST.get("catalogue", "")
        tags = request.POST.getlist("tag", "")
        action = request.POST.get("action", "0")

        catalogue_foreignkey = Catalogue.objects.get(name=catalogue)

        post.title = title
        post.content = content
        post.catalogue = catalogue_foreignkey
        post.status = action
        post.modify_time = datetime.datetime.now()
        post.save()

        post.update_tags(tags)

        return HttpResponseRedirect('/admin/')


class UpdatePost(View):
    def post(self, request, *args, **kwargs):
        # 获取当前用户
        user = request.user
        # 获取要修改的博客
        pkey = self.kwargs.get('pk')
        post = Post.objects.filter(author_id=user.id).get(pk=pkey)
        # 获取评论
        title = request.POST.get("title", "")
        content = request.POST.get("content", "")
        catalogue = request.POST.get("catalogue", "")
        tags = request.POST.getlist("tag", "")
        action = 1

        catalogue_foreignkey = Catalogue.objects.get(name=catalogue)

        post.title = title
        post.content = content
        post.catalogue = catalogue_foreignkey
        post.status = action
        post.modify_time = datetime.datetime.now()
        post.save()

        post.update_tags(tags)

        return HttpResponseRedirect('/admin/')


class UpdateEditor(View):
    def post(self, request, *args, **kwargs):
        # 获取当前用户
        user = request.user

        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)
        # 获取编辑器
        editor = request.POST.get("editor", "")
        user.editor_choice = editor
        user.save()

        return HttpResponseRedirect('/admin/')


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        from django.contrib.auth.views import logout
        return logout(request, next_page='/')


class CarouselIndexView(ListView):
    template_name = 'admin/carousel_admin.html'
    context_object_name = 'carousel_list'
    queryset = Carousel.objects.all()


class CarouselEditView(CreateView):
    template_name = 'admin/carousel_new.html'
    model = Carousel
    fields = ['title']

    def get_context_data(self, **kwargs):
        context = super(CarouselEditView, self).get_context_data(**kwargs)
        context['post_list'] = Post.objects.filter(status=1)
        return context


class AddCarousel(View):
    def post(self, request, *args, **kwargs):

        # 将文件路径和其余信息存入数据库
        title = request.POST.get("title", "")
        post = request.POST.get("post", "")
        post_foreignkey = Post.objects.get(pk=post)
        image_link = request.POST.get("image_link", "")

        if not image_link:
            filename = ""
            try:
                file_img = request.FILES['files']
                file_suffix = os.path.splitext(file_img.name)[len(os.path.splitext(file_img.name)) - 1]
                filename = uuid.uuid1().__str__() + file_suffix

                # 把过大的图像压缩成合适的轮播图大小
                img = Image.open(file_img)
                img = ThumbnailTool.constrain_len_thumbnail(img, 865)

                path = MEDIA_ROOT + "/carousel/"
                if not os.path.exists(path):
                    os.makedirs(path)

                file_name = path + filename
                img.save(file_name)
            except Exception, e:
                print e
            file_img_url = "http://" + request.META['HTTP_HOST'] + MEDIA_URL + "carousel/" + filename
            Carousel.objects.create(
                title=title,
                post=post_foreignkey,
                img=file_img_url,
            )
        else:
            Carousel.objects.create(
                title=title,
                post=post_foreignkey,
                img=image_link,
            )
        return HttpResponseRedirect('/admin/carousel')


class DeleteCarousel(View):
    def get(self, request, *args, **kwargs):
        # 获取删除的博客ID
        pkey = self.kwargs.get('pk')
        carousel = Carousel.objects.get(id=pkey)
        carousel.delete()
        return HttpResponseRedirect('/admin/carousel')


class CarouselUpdateView(UpdateView):
    template_name = 'admin/carousel_update.html'
    model = Carousel
    fields = ['title']

    def get_context_data(self, **kwargs):
        context = super(CarouselUpdateView, self).get_context_data(**kwargs)
        context['post_list'] = Post.objects.all()
        return context


class UpdateCarousel(View):
    def post(self, request, *args, **kwargs):

        # 将文件路径和其余信息存入数据库
        title = request.POST.get("title", "")
        post = request.POST.get("post", "")
        post_foreignkey = Post.objects.get(pk=post)
        image_link = request.POST.get("image_link", "")

        pkey = self.kwargs.get('pk')
        carousel = Carousel.objects.get(id=pkey)

        if not image_link:
            try:
                file_img = request.FILES['files']
                file_suffix = os.path.splitext(file_img.name)[len(os.path.splitext(file_img.name)) - 1]
                filename = uuid.uuid1().__str__() + file_suffix

                # 把过大的图像压缩成合适的轮播图大小
                img = Image.open(file_img)
                img = ThumbnailTool.constrain_len_thumbnail(img, 865)

                path = MEDIA_ROOT + "/carousel/"
                if not os.path.exists(path):
                    os.makedirs(path)

                file_name = path + filename
                img.save(file_name)
            except Exception, e:
                print e
            file_img_url = "http://" + request.META['HTTP_HOST'] + MEDIA_URL + "carousel/" + filename

            carousel.title = title
            carousel.post = post_foreignkey
            carousel.img = file_img_url
            carousel.save()

        else:
            carousel.title = title
            carousel.post = post_foreignkey
            carousel.img = image_link
            carousel.save()
        return HttpResponseRedirect('/admin/carousel')


class UserSetView(ListView):
    template_name = 'admin/userset_admin.html'
    context_object_name = 'user_list'

    def get_queryset(self):
        user_list = User.objects.all()
        return user_list

    def get_context_data(self, **kwargs):
        context = super(UserSetView, self).get_context_data(**kwargs)
        page = self.kwargs.get('page') or self.request.GET.get('page') or 1
        objects, page_range = paginator_tool(pages=page, queryset=self.object_list, display_amount=PERNUM)
        context['page_range'] = page_range
        context['objects'] = objects
        return context


class NewUserView(CreateView):
    template_name = 'admin/userset_new.html'
    model = User
    fields = ['username']


class AddUser(View):
    def post(self, request):
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        name = request.POST.get("name", "")
        email = request.POST.getlist("email", "")

        user_obj = User.objects.create_user(
            username="".join(username),
            password="".join(password),
            email="".join(email),
        )

        user_obj.name = name
        user_obj.is_superuser = 0
        user_obj.is_staff = 1

        user_obj.save()

        return HttpResponseRedirect('/admin/user')


class DeleteUser(View):
    def get(self, request, *args, **kwargs):
        # 获取当前用户
        user = self.request.user
        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)

        # 获取删除的博客ID
        pkey = self.kwargs.get('pk')
        User.objects.get(pk=pkey).delete()

        #刷新页面
        return HttpResponseRedirect('/admin/user')

#编辑
class UserUpdate(UpdateView):
    template_name = 'admin/userset_update.html'
    model = User
    fields = ['name', 'username', 'email']

    def get_context_data(self, **kwargs):
        context = super(UserUpdate, self).get_context_data(**kwargs)
        return context


class UpdateUser(View):
    def post(self, request, *args, **kwargs):
        # 获取当前用户
        user = self.request.user
        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)


        # 将文件路径和其余信息存入数据库
        username = request.POST.get("username", "")
        name = request.POST.get("name", "")
        email = request.POST.get("email", "")
        is_pwd_reset = request.POST.get("is_pwd_reset", "")
        pwd = request.POST.get("password", "")
        
        pkey = self.kwargs.get('pk')
        user_obj = User.objects.get(id=pkey)

        if is_pwd_reset:
            user_obj.set_password(pwd)
        
        user_obj.name = name
        user_obj.email = email
        user_obj.username = username
        user_obj.save()

        return HttpResponseRedirect('/admin/user')


#登录微信, 获取二维码
def Retrieve_wechat(request):
    result = {}
    result['success'] = 0
    result['message'] = '请求方式错误'
    result['data'] = {}
    
    # 判断当前用户是否是活动的用户
    user = request.user
    if not user.is_authenticated():
        return HttpResponse(u"请登陆！", status=403)

    #只接受post
    if request.method == "POST":
        wechat = Wechat(request)

        result['success'] = 1
        result['message'] = '操作成功'
        result['data'] = wechat.loginQr()

    return HttpResponse(json.dumps(result))

#轮询等待扫描结果
def Wait_scan(request):
    result={}
    result['success'] = 0
    uid = request.user.id
    wechat = Wechat(request, uid)

    num = 0
    while num<100:
        if wechat.waitScan() == '200' :
            print('no wait...')
            result['success'] = 1
            break
        num += 1

    return HttpResponse(json.dumps(result))

#从数据库取出微信好友
def Retrieve_dbfriends(request):
    result = {}
    result['success'] = 1
    result['message'] = '好友读取成功'
    result['data'] = {'friends':[], 'groups':[]}
    uid = request.user.id
    flist = Wxfriends.objects.filter(user_id=uid)[0:]
    glist = Wxgroups.objects.filter(user_id=uid)[0:]

    if len(flist) < 1:
        result['success'] = 0
        result['message'] = '好友读取失败'
        return HttpResponse(json.dumps(result))

    for item in flist:
        tmp_name = item.remark_name if len(item.remark_name)>0 else item.nick_name

        tmp = { "id": item.user_name, "text": '<div style="background: url(/'+item.img+') no-repeat center left;padding-left: 50px;background-size: 30px 30px;line-height: 30px;"/>'+ tmp_name +'</div>'}
        result['data']['friends'].append(tmp)

    for item in glist:
        tmp_name = item.remark_name if len(item.remark_name)>0 else item.nick_name

        tmp = { "id": item.user_name, "text": '<div style="background: url(/'+item.img+') no-repeat center left;padding-left: 50px;background-size: 30px 30px;line-height: 30px;"/>'+ tmp_name +'</div>'}
        result['data']['groups'].append(tmp)



    return HttpResponse(json.dumps(result))


#拉取微信好友
def Retrieve_wxfriends(request):
    #测试===>删
    #Wxfriends.objects.filter(user_id=request.user.id).delete()
    handel_friends(request)
    return Retrieve_dbfriends(request)


#拉取微信好友
def Retrieve_wxfriends_bk(request):
    result = {}
    result['success'] = 0
    result['message'] = '好友拉取失败'
    result['data'] = {'friends':[], 'groups':[]}
    uid = request.user.id

    wechat = Wechat(request)
    friends = wechat.friends()
    
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

    #获取好友
    start = time.time()
    for item in friends:
        img_name = str(uid)+ "_"+ str(item['AttrStatus'])
        
        
        try:  
            #只是更新username
            friends_obj = Wxfriends.objects.get(user_id=uid, attr_id=item['AttrStatus'])
            friends_obj.user_name =item['UserName']
            friends_obj.save() 

        except Wxfriends.DoesNotExist:  
            #保存图片路径 uid+attr_id
            #wechat.savaImg(item['HeadImgUrl'], img_name)
            img_name = wechat.savaImg(item['UserName'], img_name)
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
        tmp_name = item['RemarkName'] if len(item['RemarkName'])>0 else emoji_pattern.sub(r'', item['NickName'])
        tmp = { "id": item['UserName'], "text": '<div style="background: url(/'+img_name+') no-repeat center left;padding-left: 50px;background-size: 30px 30px;line-height: 30px;"/>'+ tmp_name +'</div>'}
        result['data']['friends'].append(tmp)

    end = time.time()
    print(end-start)
    print('threading stop....')

    #获取群组
    glist = Wxgroups.objects.filter(user_id=uid)[0:]
    for item in glist:
        tmp_name = item.remark_name if len(item.remark_name)>0 else item.nick_name

        tmp = { "id": item.user_name, "text": '<div style="background: url(/'+item.img+') no-repeat center left;padding-left: 50px;background-size: 30px 30px;line-height: 30px;"/>'+ tmp_name +'</div>'}
        result['data']['groups'].append(tmp)


    return HttpResponse(json.dumps(result))


#发送消息
def Send_msg(request):
    result = {}
    result['success'] = 1
    result['message'] = '消息发送成功'
    result['data'] = []
   
    to_user = request.POST.getlist('to_user[]')
    msg = request.POST.get("msg", "")
    opt = request.POST.get("opt", "2")

    if len(to_user)<1 or len(msg)<2:
        result['success'] = 0
        result['message'] = '消息或接受者异常'
        return HttpResponse(json.dumps(result))


    wechat = Wechat(request)

    if opt == '3':
        msg = wechat.getPdf(msg)
        if not bool(msg):
            result['success'] = 0
            result['message'] = 'pdf上传失败'
            return HttpResponse(json.dumps(result))

    if opt == '4':
        flist = Wxfriends.objects.filter(user_id=request.user.id)[0:]
        picId = wechat.getAnalysis(flist)
        if not bool(picId):
            result['success'] = 0
            result['message'] = '图片上传失败'
            return HttpResponse(json.dumps(result))

    for user in to_user:
        #pdf文件
        if opt == '3' and not wechat.sendAppMsg(user, msg):
            result['success'] = 0
            result['message'] = 'pdf消息发送失败'
            return HttpResponse(json.dumps(result))
            break
        #纯文本消息
        elif (opt == '1' or opt == '2') and not wechat.sendMsg(user, msg):
            result['success'] = 0
            result['message'] = '消息发送失败'
            return HttpResponse(json.dumps(result))
            break
        #分析图片
        elif (opt == '4') and not wechat.sendPic(user, picId):
            result['success'] = 0
            result['message'] = '消息发送失败'
            return HttpResponse(json.dumps(result))
            break

   
    return HttpResponse(json.dumps(result))


#心跳
def Wx_sync(request):
    result = {}
    result['success'] = 1
    result['message'] = '连接正常'

    try :
        wechat = Wechat(request)
        if not wechat.synccheck():
            result['success'] = 0
            result['message'] = '连接断开'
    except Exception,e:
        print(e)
        result['success'] = 0
        result['message'] = '连接不存在'

    return HttpResponse(json.dumps(result))

#API接口测试
def api_test(request):
    result = {}
    result['success'] = 0
    result['message'] = '测试失败'
    menuId = request.POST.get("menu_id", "")
    productId = request.POST.get("product_id", "")

    if len(menuId)<1 or len(productId)<1 :
        return HttpResponse(json.dumps(result))

    api = apidoc()

    try :
        if menuId == 1:
            #先通过初始化登录接口
            content = Content.objects.get(product_id=productId, menu_id=1)
            api.api(content)
            #循环其他所有的接口,暂时不管
            print('--->1')
        else:
            #只测试登录和当前接口
            content = Content.objects.get(product_id=productId, menu_id=1)
            api.api(content.content)
            content = Content.objects.get(product_id=productId, menu_id=menuId)
            result['data'] = api.api(content.content)
            print('---->others')
    
        result['success'] = 1
        result['message'] = '测试成功'
    except Exception,e:
        print(e)
        result['success'] = 0
        result['message'] = '测试失败'

    return HttpResponse(json.dumps(result))


# 柚子空间
class YouziView(ListView):
    template_name = 'admin/youzi.html'
    context_object_name = 'growth_list'

    def get_queryset(self):

        user = self.request.user
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)

        return Growth.objects.all()

    def get_context_data(self, **kwargs):
        # 成长数据
        context = super(YouziView, self).get_context_data(**kwargs)

        #置顶图片
        pics =  Youzipic.objects.all()
        pic_list = []
        for pic in pics:
            if pic.pic_type == 1 :
                context['top_pic'] = pic.pic_id
            else :
                pic_list.append(pic.pic_id)

        #轮播图片
        context['crousel_pic'] = pic_list
        #context['crousel_pic'] = Media.objects.filter(id__in=pic_list).all()

        #相册列表
        context['album'] = Album.objects.all()

        #成长记录
        return context

#保存图片或视频
def youzi_upload(request):
    result = {}
    result['success'] = 1
    result['message'] = '上传成功'
    print(request)
    if request.method == "POST":

        path = MEDIA_ROOT + "/youzi/"

        if not os.path.exists(path):
            os.makedirs(path)

        try:


            files = request.FILES.getlist('input-pd[]', None)
            fileNames =  request.POST.get("nameList", "").split(',')
            album_id = request.POST.get("album_id", 0)

            for i in range(len(files)):
                file = files[i]

                filename = fileNames[i] if len(fileNames[i])>0 else file
                print filename

                #后缀
                file_suffix = os.path.splitext(filename)[len(os.path.splitext(filename)) - 1]
                # 设置名称
                fname = uuid.uuid1().__str__() + file_suffix

                with open(path + fname, 'wb+')as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)

                #保存到数据库
                Media.objects.create(
                    name = fname,
                    origin_name = filename,
                    creator = request.user,
                    album_id = album_id
                )

        except Exception, e:
            print(e)
            result['success'] = 0
            result['message'] = '上传失败'

    else:
        result['success'] = 0
        result['message'] = '请求方式错误'

    return HttpResponse(json.dumps(result))


#新增或编辑成长数据
def save_growth(request):
    result = {}
    result['success'] = 0
    result['message'] = '请求方式错误'
    result['growth_id'] = ''

    # 只接受post
    if request.method == "POST":
        # 获取当前用户
        user = request.user

        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)

        growth_id = request.POST.get("growth_id", "").strip()
        height = request.POST.get("height", "").strip()
        weight = request.POST.get("weight", "").strip()
        head = request.POST.get("head", "").strip()
        record_time = request.POST.get("record_time", "").strip()

        result['success'] = 1
        result['message'] = '保存成长数据成功'

        try:
            content_obj = Growth.objects.get(id=growth_id)
            content_obj.height = height
            content_obj.weight = weight
            content_obj.head = head
            content_obj.record_time = record_time
            content_obj.save()
            # 清空首页缓存
            cache.clear()

        except Growth.DoesNotExist:
            try:

                g = Growth(
                    height=height,
                    weight=weight,
                    head=head,
                    record_time=record_time,
                    creator_id = user.id
                )
                g.save(force_insert=True)
                result['growth_id'] = g.id

            except Exception,e:
                print e
                result['success'] = 0
                result['message'] = '保存成长数据失败'

    return HttpResponse(json.dumps(result))

#删除成长数据
def delete_growth(request):
    result = {}
    result['success'] = 0
    result['message'] = '请求方式错误'

    # 只接受post
    if request.method == "POST":
        # 获取当前用户
        user = request.user
        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)

        growth_id = request.POST.get("growth_id", "").strip()

        try:
            Growth.objects.filter(id=growth_id).delete()
            result['success'] = 1
            result['message'] = '删除成长数据成功'
            # 清空首页缓存
            cache.clear()
        except Content.DoesNotExist:
            result['message'] = '删除成长数据异常'
    return HttpResponse(json.dumps(result))
#多媒体列表ajax
def media_list(request):
    result = {}
    result['success'] = 0
    result['message'] = '请求方式错误'

    if request.method == "GET":
        # 获取当前用户
        user = request.user
        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)

        search = request.GET.get('search[value]')
        asset_count = Media.objects.all().count()

        draw = int(request.GET.get('draw'))
        start = int(request.GET.get('start'))  # 从多少行开始
        length = int(request.GET.get('length'))  # 显示多少条数据

        end = start + length  # 到多少行结束

        if search == "":
            #无搜索
            assets_values_list = Media.objects.values_list(
                'id',
                'origin_name',
                'create_time',
                'name',

            ).order_by('-create_time')[start: end]
            _filter = asset_count
            all_lists = map(list, assets_values_list)
        else:
            #有搜索
            search_list = Media.objects.filter(
                Q(name__contains=search) |
                Q(origin_name__contains=search)
            ).values_list(
                'id',
                'origin_name',
                'create_time',
                'name',
            ).order_by('-create_time')[start: end]

            _filter = len(search_list)
            all_lists = map(list, search_list)

        img_suffixs = '.jpg.png.gif.'
        path = "/upload/youzi/"

        all_list = []
        for i in all_lists:
            i[2] = i[2].strftime("%Y-%m-%d %H:%M:%S")
            file_suffix = os.path.splitext(i[3])[len(os.path.splitext(i[3])) - 1]

            if file_suffix in img_suffixs:
                #图片
                i[3] = '<img src = "'+path+i[3]+'" >'
            else:
                #视频
                i[3] = '<video src="'+path+i[3]+'"></video>'


            all_list.append(i)

        result = {
            'success': 1,
            'message': '操作成功',
            'draw': draw,
            'recordsTotal': asset_count,
            'recordsFiltered': _filter,
            'data': all_list
        }

    return HttpResponse(json.dumps(result))

#保存配置
def save_config(request):
    result = {}
    result['success'] = 0
    result['message'] = '请求方式错误'

    # 只接受post
    if request.method == "POST":
        # 获取当前用户
        user = request.user

        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)

        top_id = request.POST.get("top_id", "")
        crousel_ids = request.POST.getlist('crousel_ids[]', [])
        print(top_id)
        print(crousel_ids)

        result['success'] = 1
        result['message'] = '保存配置数据成功'

        try:
            #删除所有数据
            Youzipic.objects.all().delete()

            #批量创建
            querysetlist = []
            for i in crousel_ids:
                querysetlist.append(Youzipic(pic_id=Media.objects.get(id=i), pic_type=0, creator_id=user.id))

            querysetlist.append(Youzipic(pic_id=Media.objects.get(id=top_id), pic_type=1, creator_id=user.id))
            Youzipic.objects.bulk_create(querysetlist)
            # 清空首页缓存
            cache.clear()

        except  Exception,e:
            print e
            result['success'] = 0
            result['message'] = '保存配置数据失败'

    return HttpResponse(json.dumps(result))

#记录列表
def events_list(request):
    result = {}
    result['success'] = 0
    result['message'] = '请求方式错误'

    if request.method == "GET":
        # 获取当前用户
        user = request.user
        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)

        search = request.GET.get('search[value]')
        asset_count = Media.objects.all().count()

        draw = int(request.GET.get('draw'))
        start = int(request.GET.get('start'))  # 从多少行开始
        length = int(request.GET.get('length'))  # 显示多少条数据

        end = start + length  # 到多少行结束

        if search == "":
            # 无搜索
            assets_values_list = Events.objects.values_list(
                'id',
                'title',
                'record_time',
                'create_time',
            ).order_by('-record_time')[start: end]
            _filter = asset_count
            all_lists = map(list, assets_values_list)
        else:
            # 有搜索
            search_list = Events.objects.filter(
                Q(title__contains=search) |
                Q(content__contains=search)
            ).values_list(
                'id',
                'title',
                'record_time',
                'create_time',
            ).order_by('-record_time')[start: end]

            _filter = len(search_list)
            all_lists = map(list, search_list)

        all_list = []
        for i in all_lists:
            i[2] = i[2].strftime("%Y-%m-%d %H:%M:%S")
            i[3] = i[3].strftime("%Y-%m-%d %H:%M:%S")
            all_list.append(i)

        result = {
            'success': 1,
            'message': '操作成功',
            'draw': draw,
            'recordsTotal': asset_count,
            'recordsFiltered': _filter,
            'data': all_list
        }

    return HttpResponse(json.dumps(result))


#保存记录
def save_events(request):
    result = {}
    result['success'] = 0
    result['message'] = '请求方式错误'

    # 只接受post
    if request.method == "POST":
        # 获取当前用户
        user = request.user

        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)

        media_id = request.POST.get("media_id", "")
        album_id = request.POST.get("album_id", "")
        title = request.POST.get("title", "")
        record_time = request.POST.get("record_time", "")
        content = request.POST.get("content", "")


        result['success'] = 1
        result['message'] = '保存配置数据成功'

        try:
            Events.objects.create(
                media_id = Media.objects.get(id=media_id),
                album_id = album_id,
                title = title,
                record_time=record_time,
                content=content,
                creator_id=user.id
            )
            # 清空首页缓存
            cache.clear()

        except  Exception,e:
            print e
            result['success'] = 0
            result['message'] = '保存配置数据失败'

    return HttpResponse(json.dumps(result))


#删除记录
def delete_events(request):
    result = {}
    result['success'] = 0
    result['message'] = '请求方式错误'

    # 只接受post
    if request.method == "GET":
        # 获取当前用户
        user = request.user
        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)

        events_id = request.GET.get("events_id", "").strip()

        try:
            Events.objects.filter(id=events_id).delete()
            result['success'] = 1
            result['message'] = '删除记录数据成功'
            # 清空首页缓存
            cache.clear()
        except Content.DoesNotExist:
            result['message'] = '删除记录数据异常'
    return HttpResponse(json.dumps(result))


#保存相册
def save_album(request):
    result = {}
    result['success'] = 0
    result['message'] = '请求方式错误'
    result['data'] = ''

    # 只接受post
    if request.method == "POST":
        # 获取当前用户
        user = request.user

        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)

        album_id = request.POST.get("id", "")
        title = request.POST.get("title", "")

        result['success'] = 1
        result['message'] = '保存配置数据成功'

        try:
            if str(album_id) == '0':
                Album.objects.create(
                    title = title,
                    creator_id=user.id
                )
            else :
                k = Album.objects.get(id=int(album_id))
                k.title = title
                k.save()
            alist = Album.objects.all();
            for alb in alist:
                if album_id == str(alb.id):
                    result['data'] += '<option selected value="'+str(alb.id) +'">'+alb.title +'</option>'
                else:
                    result['data'] += '<option value="' + str(alb.id) + '">' + alb.title + '</option>'
        except  Exception,e:
            print e
            result['success'] = 0
            result['message'] = '保存配置数据失败'

    return HttpResponse(json.dumps(result))

#更新相册，添加图片
def select_album(request):
    result = {}
    result['success'] = 0
    result['message'] = '请求方式错误'

    # 只接受post
    if request.method == "POST":
        # 获取当前用户
        user = request.user
        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)

        pic_ids = request.POST.getlist('pic_ids[]', [])
        album_id = request.POST.get("album_id", "")

        try:
            Media.objects.filter(id__in=pic_ids).update(album_id = album_id)
            result['success'] = 1
            result['message'] = '更新相册成功'
        except :
            result['message'] = '更新相册异常'
    return HttpResponse(json.dumps(result))

#文档公开或保密
def docu_lock(request):
    result = {}
    result['success'] = 0
    result['message'] = '请求方式错误'

    # 只接受post
    if request.method == "POST":
        # 获取当前用户
        user = request.user
        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)

        pid = request.POST.get("docu_id", "")

        try:
            obj = Product.objects.get(id=pid)
            if user.is_superuser or obj.author_id == user.id:
                flag = 1
                if obj.is_public:
                    flag = 0
                obj.is_public = flag
                obj.save()
                result['is_public'] = flag
                result['success'] = 1
                result['message'] = '公开属性修改成功'
            else:
                result['message'] = '公开属性修改失败'
        except :
            result['message'] = '公开属性修改失败'

    return HttpResponse(json.dumps(result))





    










