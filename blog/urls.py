from django.conf.urls import url
from django.views.decorators.cache import cache_page

from blog.views import IndexView, PostView, CommentView, RepositoryView, RepositoryDetailView, TagListView, \
    CategoryListView, AuthorPostListView, CommentDeleteView,ProductView, DocumentView, ApiTest, DocumentListView, \
    AlbumListView

urlpatterns = [
    url(r'^$',  cache_page(2592000)(IndexView.as_view())), #youzi cache 30 days
    #url(r'^document$', DocumentListView.as_view()),
    url(r'^album/(?P<pk>[0-9]+)$', AlbumListView.as_view()),
    url(r'^document/(?P<pk>[0-9]+)$', DocumentView.as_view()),
    url(r'^product/(?P<pk>[0-9]+)$', ProductView.as_view()),
    url(r'^post/(?P<pk>[0-9]+)$', PostView.as_view()),
    url(r'^comment/add/(?P<pk>[0-9]+)$', CommentView.as_view()),
    url(r'^comment/delete/(?P<pk>[0-9]+)$', CommentDeleteView.as_view()),
    url(r'^repository$', RepositoryView.as_view()),
    url(r'^repository/(?P<pk>[0-9]+)$', RepositoryDetailView.as_view()),
    url(r'^tag/(?P<slug>[\w\u4e00-\u9fa5]+)$', TagListView.as_view()),
    url(r'^category/(?P<slug>[\w\u4e00-\u9fa5]+)$', CategoryListView.as_view()),
    url(r'^author/(?P<pk>[0-9]+)$', AuthorPostListView.as_view()),
    url(r'^api/(?P<pid>[0-9]+)/(?P<mid>[0-9]+)$', ApiTest)
]