# -*- coding:utf-8 -*-
import json
import re
import os
from django.db.models import Q
from collections import OrderedDict
from django.http import HttpResponse,HttpResponseRedirect
from django.contrib.auth import get_user_model

from django.views.generic import View, DetailView, ListView
from django.db.models import Count
from zer0Blog.settings import PERNUM
from tagging.models import TaggedItem

from blog.pagination import paginator_tool
from .models import Post, Carousel, Comment, Repository, Catalogue, User, Product, Content, Media, Album, Growth, Events, Youzipic
from django.shortcuts import render
from .rest_api import apidoc

class BaseMixin(object):

    def get_context_data(self, **kwargs):
        context = super(BaseMixin, self).get_context_data(**kwargs)
        try:
            context['hot_article_list'] = Post.objects.filter(status=1).order_by("-view_count")[0:10]
            # context['man_list'] = get_user_model().objects.annotate(Count("post"))
            context['man_list'] = get_user_model().objects.raw('select *, COUNT(post.id) as counts from blog_user as user LEFT JOIN blog_post post ON post.status=1 and post.author_id=user.id GROUP BY user.id');
        except Exception as e:
            print e

        return context

# 前端查看的页面 登录
class IndexView(BaseMixin, ListView):
    template_name = 'blog/index.html'
    context_object_name = 'growth_list'

    def get_queryset(self):
        #成长数据
        growth_list = Growth.objects.all()
        data = {'x':[], 'y1':[],  'y2':[], 'y3':[]}
        for i in range(len(growth_list)):
            data['x'].append(growth_list[i].record_time.strftime("%Y-%m-%d"))
            data['y1'].append(str(growth_list[i].height))
            data['y2'].append(str(growth_list[i].weight))
            data['y3'].append(str(growth_list[i].head))
        return data

    def get_context_data(self, **kwargs):

        context = super(IndexView, self).get_context_data(**kwargs)

        #成长事件
        events = Events.objects.all()
        events_html = ''
        img_suffixs = '.jpg.png.gif.'
        for i in range(len(events)):
            #时间
            events_html += '{time:"' + events[i].record_time.strftime("%Y-%m-%d") + '",'
            #标题
            if events[i].title :
                events_html += 'header:"' + events[i].title + '",'

            #body
            events_html += 'body:['

            #图片或视频
            if events[i].media_id :
                mid = str(events[i].media_id)
                file_suffix = os.path.splitext(mid)[len(os.path.splitext(mid)) - 1]
                print file_suffix
                if file_suffix in img_suffixs:
                    #图片
                    events_html += '{ tag: "img", attr: {src: "/upload/youzi/'+ mid + '", width: "150px", cssclass: "img-responsive" }},'
                else :
                    #视频
                    events_html += '{ tag: "video", attr: {src: "/upload/youzi/' + mid + '", width: "150px", controls:"controls", cssclass: "img-responsive" }},'

            #内容
            events_html += '{ tag: "p", content:"' + events[i].content + '"}],'

            #有相册
            if events[i].album_id :
                events_html += 'footer:"<a href=\'/album/'+ str(events[i].album_id) +'\' target=\'_blank\'>查看相册</a>",'

            events_html += '},'

        context['events_html'] = '[' + events_html + ']'

        #置顶图片
        context['top_pic'] =  Youzipic.objects.select_related('pic_id').get(pic_type=1).pic_id.name

        #轮播图片
        crousel_list = Youzipic.objects.select_related('pic_id').filter(pic_type=0).all()
        crousel_muster = '''
[
		{img:'upload/youzi/1.jpg', x:-1000, y:0, z:1500, nx:0, nz:1},
		{img:'upload/youzi/2.jpg', x:0,     y:0, z:1500, nx:0, nz:1},
		{img:'upload/youzi/3.jpg', x:1000,  y:0, z:1500, nx:0, nz:1},
		{img:'upload/youzi/4.jpg', x:1500,  y:0, z:1000, nx:-1, nz:0},
		{img:'upload/youzi/5.jpg', x:1500,  y:0, z:0, nx:-1, nz:0},
		{img:'upload/youzi/6.jpg', x:1500,  y:0, z:-1000, nx:-1, nz:0},
		{img:'upload/youzi/7.jpg', x:1000,  y:0, z:-1500, nx:0, nz:-1},
		{img:'upload/youzi/8.jpg', x:0,     y:0, z:-1500, nx:0, nz:-1},
		{img:'upload/youzi/9.jpg', x:-1000, y:0, z:-1500, nx:0, nz:-1},
		{img:'upload/youzi/10.jpg', x:-1500, y:0, z:-1000, nx:1, nz:0},
		{img:'upload/youzi/11.jpg', x:-1500, y:0, z:0, nx:1, nz:0},
		{img:'upload/youzi/12.jpg', x:-1500, y:0, z:1000, nx:1, nz:0}
]
        '''
        for i in range(len(crousel_list)):
            crousel_muster = crousel_muster.replace('/'+str(i+1)+'.jpg', '/' + crousel_list[i].pic_id.name)

        context['crousel_pics'] = crousel_muster
        return context



class PostView(BaseMixin, DetailView):
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    queryset = Post.objects.filter(status=1)

    # 用于记录文章的阅读量，每次请求添加一次阅读量
    def get(self, request, *args, **kwargs):
        pkey = self.kwargs.get("pk")
        posts = self.queryset.get(pk=pkey)
        posts.view_count += 1
        posts.save()
        return super(PostView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PostView, self).get_context_data(**kwargs)
        pkey = self.kwargs.get("pk")

        comment_queryset = self.queryset.get(pk=pkey).comment_set.all().order_by('publish_Time')
        comment_dict = self.handle_comment(comment_queryset)
        context['comment_list'] = comment_dict
        return context

    def handle_comment(self, queryset):
        comment_dict = OrderedDict()
        root_list = []
        child_list = []
        every_child_list = []
        # 将有根节点的评论和无根节点的评论分开
        for comment in queryset:
            if comment.root_id == 0:
                root_list.append(comment)
            else:
                child_list.append(comment)
        # 将根评论作为键，子评论列表作为值，组合成dict
        for root_comment in root_list:
            for child_comment in child_list:
                if child_comment.root_id == root_comment.id:
                    every_child_list.append(child_comment)
                    # every_child_list.reverse()
            comment_dict[root_comment] = every_child_list
            every_child_list = []
        return comment_dict

# 产品详情
class ProductView(BaseMixin, DetailView):
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    queryset = Post.objects.filter(status=1)

    # 用于记录文章的阅读量，每次请求添加一次阅读量
    def get(self, request, *args, **kwargs):
        pkey = self.kwargs.get("pk")
        posts = self.queryset.get(pk=pkey)
        posts.view_count += 1
        posts.save()
        return super(PostView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PostView, self).get_context_data(**kwargs)
        pkey = self.kwargs.get("pk")

        comment_queryset = self.queryset.get(pk=pkey).comment_set.all().order_by('publish_Time')
        comment_dict = self.handle_comment(comment_queryset)
        context['comment_list'] = comment_dict
        return context

    def handle_comment(self, queryset):
        comment_dict = OrderedDict()
        root_list = []
        child_list = []
        every_child_list = []
        # 将有根节点的评论和无根节点的评论分开
        for comment in queryset:
            if comment.root_id == 0:
                root_list.append(comment)
            else:
                child_list.append(comment)
        # 将根评论作为键，子评论列表作为值，组合成dict
        for root_comment in root_list:
            for child_comment in child_list:
                if child_comment.root_id == root_comment.id:
                    every_child_list.append(child_comment)
                    # every_child_list.reverse()
            comment_dict[root_comment] = every_child_list
            every_child_list = []
        return comment_dict


class CommentView(View):
    def post(self, request, *args, **kwargs):
        # 获取当前用户
        user = self.request.user
        # 获取评论
        comment = self.request.POST.get("comment", "")
        root_id = self.request.POST.get("root_id", 0)
        parent_id = self.request.POST.get("parent_id", 0)

        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)
        if not comment:
            return HttpResponse(u"请输入评论", status=403)
        if len(comment) > 200:
            return HttpResponse(u"评论过长，请重新输入", status=403)

        # 获取用户IP地址
        if request.META.has_key("HTTP_X_FORWARDED_FOR"):
            ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            ip = request.META['REMOTE_ADDR']

        # 处理comment中的@事件
        comment = self.handle_at_str(comment)
        # 处理comment中的emoji表情，只有root_id为0的评论才会有表情
        if root_id == 0:
            comment = self.handle_emoji_str(comment)

        pkey = self.kwargs.get("pk", "")
        post_foreignkey = Post.objects.get(pk=pkey)

        comment = Comment.objects.create(
            post=post_foreignkey,
            author=user,
            content=comment,
            ip_address=ip,
            root_id=root_id,
            parent_id=parent_id,
        )

        result_dict = {'post_id': post_foreignkey.id,
                       'csrf_token': request.COOKIES["csrftoken"],
                       'user_avatar': unicode(user.avatar_path),
                       'user_id': user.id,
                       'author_id': comment.author.id,
                       'comment_id': comment.id,
                       'comment_author': comment.author.name,
                       'comment_publish_time': comment.publish_Time.strftime("%Y年%m月%d日 %H:%M"),
                       'comment_content': comment.content}

        return HttpResponse(json.dumps(result_dict))

    def handle_at_str(self, str):
        pattern = re.compile('@\S+ ')
        result = pattern.findall(str)
        for string in result:
            handler_str = '<a>' + string + '</a>'
            str = re.sub(string, handler_str, str)
        return str

    def handle_emoji_str(self, str):
        keys = ':(add1|-1|airplane|alarm_clock|alien|angel|angry|anguished|art|astonished|basketball|beers|bicyclist|birthday|blush|broken_heart|cat|chicken|clap|confounded|confused|cow|cry|disappointed|dizzy_face|dog|expressionless|fearful|flushed|frowning|full_moon_with_face|ghost|grimacing|grin|grinning|heart_eyes|high_brightness|hushed|innocent|joy|kissing_heart|laughing|mask|neutral_face|new_moon_with_face|pencil2|persevere|person_frowning|person_with_blond_hair|relaxed|relieved|satisfied|scream|sleeping|smile|smirk|sob|stuck_out_tongue_winking_eye|sunglasses|sweat|tired_face|triumph|tulip|u7981|unamused|unlock|v|weary|wink|worried|yum|zzz):'
        pattern = re.compile(keys)
        result = pattern.findall(str)
        for string in result:
            key = string
            # key = result[1:-1]
            url = '/static/jquery-emojiarea/packs/basic/emojis'
            extension = '.png'
            src = url + '/' + key + extension
            handler_str = '<img class="emoji" width="20" height="20" align="absmiddle" src="' + src + '"/>'
            str = re.sub(':'+string+':', handler_str, str)
        return str


class CommentDeleteView(View):
    def post(self, request, *args, **kwargs):
        # 获取当前用户
        user = self.request.user
        # 判断当前用户是否是活动的用户
        if not user.is_authenticated():
            return HttpResponse(u"请登陆！", status=403)

        pkey = self.kwargs.get("pk", "")
        comment = Comment.objects.filter(author_id=user.id).get(pk=pkey)

        # 如果root_id为0，代表为父评论，获取父评论的所有子评论
        if comment.root_id == 0:
            children_comment_set = Comment.objects.filter(root_id=comment.id)
            children_comment_set.delete()

        # 返回当前评论
        result = {'comment_id': comment.id}
        comment.delete()

        return HttpResponse(json.dumps(result))


class RepositoryView(BaseMixin, ListView):
    template_name = 'blog/repository.html'
    context_object_name = 'repository_list'
    queryset = Repository.objects.all()

    def get_context_data(self, **kwargs):
        page = self.kwargs.get('page') or self.request.GET.get('page') or 1
        objects, page_range = paginator_tool(pages=page, queryset=self.queryset, display_amount=PERNUM)
        context = super(RepositoryView, self).get_context_data(**kwargs)
        context['page_range'] = page_range
        context['objects'] = objects
        return context


class RepositoryDetailView(BaseMixin, DetailView):
    template_name = 'blog/repository_detail.html'
    context_object_name = 'repository'
    queryset = Repository.objects.all()

    # 用于记录文章的阅读量，每次请求添加一次阅读量
    def get(self, request, *args, **kwargs):
        pkey = self.kwargs.get("pk")
        repositorys = self.queryset.get(pk=pkey)
        repositorys.view_count += 1
        repositorys.save()
        return super(RepositoryDetailView, self).get(request, *args, **kwargs)


class TagListView(BaseMixin, ListView):
    template_name = template_name = 'blog/index.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        slug_key = self.kwargs.get("slug")
        post_list = TaggedItem.objects.get_by_model(Post, slug_key)
        return post_list

    def get_context_data(self, **kwargs):
        page = self.kwargs.get('page') or self.request.GET.get('page') or 1
        objects, page_range = paginator_tool(pages=page, queryset=self.get_queryset(), display_amount=PERNUM)
        context = super(TagListView, self).get_context_data(**kwargs)
        context['carousel_page_list'] = Carousel.objects.all()
        context['page_range'] = page_range
        context['objects'] = objects
        return context


class CategoryListView(BaseMixin, ListView):
    template_name = template_name = 'blog/index.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        slug_key = self.kwargs.get("slug")
        catalogue_key = Catalogue.objects.get(pk=slug_key)
        post_list = Post.objects.filter(catalogue_id=catalogue_key)
        return post_list

    def get_context_data(self, **kwargs):
        page = self.kwargs.get('page') or self.request.GET.get('page') or 1
        objects, page_range = paginator_tool(pages=page, queryset=self.get_queryset(), display_amount=PERNUM)
        context = super(CategoryListView, self).get_context_data(**kwargs)
        context['carousel_page_list'] = Carousel.objects.all()
        context['page_range'] = page_range
        context['objects'] = objects
        return context


class AuthorPostListView(BaseMixin, ListView):
    template_name = template_name = 'blog/index.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        pkey = self.kwargs.get("pk")
        user = User.objects.get(pk=pkey)
        post_list = Post.objects.filter(author_id=user).filter(status=1)
        return post_list

    def get_context_data(self, **kwargs):
        page = self.kwargs.get('page') or self.request.GET.get('page') or 1
        objects, page_range = paginator_tool(pages=page, queryset=self.get_queryset(), display_amount=PERNUM)
        context = super(AuthorPostListView, self).get_context_data(**kwargs)
        context['carousel_page_list'] = Carousel.objects.all()
        context['page_range'] = page_range
        context['objects'] = objects
        return context


# 查看文档内容，包含目录和第一页, 暂不做评论
class DocumentView(DetailView):
    template_name = 'blog/document_detail.html'
    context_object_name = 'document'
    queryset = Product.objects.filter(is_deleted=0)

    # 用于记录文章的阅读量，每次请求添加一次阅读量
    def get(self, request, *args, **kwargs):
        pkey = self.kwargs.get("pk")

        # 判断当前用户是否是活动的用户
        user = self.request.user

        try:
            if not user.is_authenticated():
                #未登录只能查看公开文档
                document = self.queryset.get(pk=pkey, is_public=1)
            elif user.is_superuser:
                #超管看所有文档权限
                document = self.queryset.get(pk=pkey)
            else:
                # 普通登录用户只能查看自己的文档
                document = self.queryset.get(pk=pkey,author_id=user.id)

            return super(DocumentView, self).get(request, *args, **kwargs)
        except Product.DoesNotExist: 
            return HttpResponseRedirect('/admin/login')

    def get_context_data(self, **kwargs):
        context = super(DocumentView, self).get_context_data(**kwargs)
        
        return context

    # ajax获取单页内容
    def post(self, request, *args, **kwargs):
        result = {}
        result['success'] = 0
        result['message'] = '未找到页面内容'
        result['data'] = {}

        menu_id = request.POST.get("menu_id", "")
        product_id = request.POST.get("product_id", "")
        try:  
            content_obj = Content.objects.get(product_id=product_id, menu_id=menu_id)
            result['success'] = 1
            result['message'] = '内容获取成功'
            result['data']['content_type'] = content_obj.content_type
            result['data']['content'] = content_obj.content
            result['data']['publish_time'] = content_obj.publish_time.strftime('%Y-%m-%d %H:%M:%S')  
            result['data']['modify_time'] = content_obj.modify_time.strftime('%Y-%m-%d %H:%M:%S')
            result['data']['publish_time'] = ''
            result['data']['modify_time'] = ''
        except Content.DoesNotExist:  
            result['data']['content_type'] = 0
            result['data']['content'] = ''
            result['data']['publish_time'] = ''
            result['data']['modify_time'] = ''
            
        return HttpResponse(json.dumps(result))

#将测试结果显示在页面上
def ApiTest(request, pid, mid):

    """A view of all bands."""

    api = apidoc()
    rs_list = []
    try :
        content = Content.objects.get(product_id=pid, menu_id=1)
        item = api.api(content.content)
        item['doc_url'] = '/document/' + str(pid)
        rs_list.append(item)

        if str(mid) == '1':
            #循环其他所有的接口
            content = Content.objects.filter(product_id=pid).exclude(menu_id=1)
            for ci in content:
                item = api.api(ci.content)
                item['doc_url'] = '/document/' + str(pid) + '?subMenu=' + str(ci.menu_id)
                rs_list.append(item)

        else:
            #只测试当前接口
            content = Content.objects.get(product_id=pid, menu_id=mid)
            item = api.api(content.content)
            item['doc_url'] = '/document/' + str(pid) + '?subMenu=' + str(mid)
            rs_list.append(item)

    except Exception,e:
        print(e)
    
    return render(request, 'blog/api_test.html', {'rs':rs_list})

class DocumentListView(BaseMixin, ListView):

    template_name = 'blog/document_list.html'
    context_object_name = 'docu_list'

    def get_queryset(self):

        # 判断当前用户是否是活动的用户
        user = self.request.user
        print(user)
        if not user.is_authenticated():
            return HttpResponseRedirect('/admin/login')

        if user.is_superuser:
            product_list = Product.objects.all()
        else:
            product_list = Product.objects.filter(author_id=user.id).exclude(is_deleted=1)

        return product_list

#前台查看相册
class AlbumListView(BaseMixin, ListView):

    template_name = 'blog/album.html'
    context_object_name = 'album_list'
    album_id = 0

    def get_queryset(self):

        # 判断当前用户是否是活动的用户
        user = self.request.user
        self.album_id = self.kwargs.get("pk")
        print self.album_id

        if not user.is_authenticated():
            return HttpResponseRedirect('/admin/login')

        album_list = Media.objects.filter(album_id = self.album_id).all()
        return album_list

    def get_context_data(self, **kwargs):
        context = super(AlbumListView, self).get_context_data(**kwargs)
        context['ablum_detail'] =Album.objects.select_related('creator').get(id=self.album_id)
        return context

