# -*- coding:utf-8 -*-
from django.conf.urls import url,include

from blog.admin_views import PostView, DeletePost, NewPost, UpdatePostIndexView, AddPost, \
    UpdateDraft, UpdatePost, UpdateEditor, LogoutView, CarouselIndexView, CarouselEditView, \
    AddCarousel, DeleteCarousel, CarouselUpdateView, UpdateCarousel, markdown_image_upload_handler, \
    tinymce_image_upload_handler, UserSetView, NewUserView, AddUser, avatar_image_upload_handler, \
    ProductView, DeleteProduct, RestoreProduct, NewProduct, AddProduct, ProductUpdate, UpdateProduct, \
    DocutypeView, DeleteDocutype, NewDocutype, AddDocutype, DocutypeUpdate, UpdateDocutype, \
    ProductMenu, update_product_menu, update_product_content,retrieve_product_content, DeleteUser, \
    UserUpdate, UpdateUser, Retrieve_wechat, Wait_scan, Retrieve_wxfriends,Retrieve_dbfriends, \
    Send_msg, Wx_sync, api_test, YouziView, youzi_upload, delete_growth, save_growth, media_list, \
    save_config, events_list, save_events, delete_events, save_album, select_album, docu_lock

urlpatterns = [
    url(r'^admin/', include([
        #url(r'^$', PostView.as_view(), name='index'),
        #url(r'^delete/(?P<pk>[0-9]+)$', DeletePost.as_view()),
        #url(r'^new$', NewPost.as_view()),
        #url(r'^add$', AddPost.as_view()),
        #产品名称
        url(r'^$', ProductView.as_view(), name='index'),
        url(r'^delete/(?P<pk>[0-9]+)$', DeleteProduct.as_view()),
        url(r'^restore/(?P<pk>[0-9]+)$', RestoreProduct.as_view()),
        url(r'^new$', NewProduct.as_view()),
        url(r'^add$', AddProduct.as_view()),
        url(r'^update/(?P<pk>[0-9]+)$', ProductUpdate.as_view()),
        url(r'^update/id/(?P<pk>[0-9]+)$', UpdateProduct.as_view()),
        url(r'^menu/(?P<pk>[0-9]+)$', ProductMenu.as_view()),
        url(r'^docu/lock$', docu_lock),

        #文档类型
        url(r'^docutype$', DocutypeView.as_view()),
        url(r'^docutype/delete/(?P<pk>[0-9]+)$', DeleteDocutype.as_view()),
        url(r'^docutype/new$', NewDocutype.as_view()),
        url(r'^docutype/add$', AddDocutype.as_view()),
        url(r'^docutype/update/(?P<pk>[0-9]+)$', DocutypeUpdate.as_view()),
        url(r'^docutype/update/id/(?P<pk>[0-9]+)$', UpdateDocutype.as_view()),
        #删除用户
        url(r'^user$', UserSetView.as_view()),
        url(r'^user/new$', NewUserView.as_view()),
        url(r'^user/add$', AddUser.as_view()),
        url(r'^user/delete/(?P<pk>[0-9]+)$', DeleteUser.as_view()),
        url(r'^user/update/(?P<pk>[0-9]+)$', UserUpdate.as_view()),
        url(r'^user/update/id/(?P<pk>[0-9]+)$', UpdateUser.as_view()),

        #修改目录
        url(r'^menu/update$', update_product_menu),
        #修改内容
        url(r'^menu/update/content$', update_product_content),
        #获取内容
        url(r'^menu/retrieve/content$', retrieve_product_content),
        #测试接口
        url(r'^menu/api/test$', api_test),

        #微信相关
        url(r'^menu/retrieve/wechat$', Retrieve_wechat),
        url(r'^menu/waitScan$', Wait_scan),
        url(r'^menu/wxfriends$', Retrieve_wxfriends),
        url(r'^menu/dbfriends$', Retrieve_dbfriends),
        url(r'^menu/send/msg$', Send_msg),
        url(r'^wx_sync$', Wx_sync), #启动微信心跳

        #柚子
        url(r'^youzi$', YouziView.as_view()),
        url(r'^youzi/upload$', youzi_upload),
        url(r'^youzi/growth/save$', save_growth),
        url(r'^youzi/growth/delete$', delete_growth),
        url(r'^youzi/media$', media_list),
        url(r'^youzi/config/save$', save_config),
        url(r'^youzi/events$', events_list),
        url(r'^youzi/events/save$', save_events),
        url(r'^youzi/events/delete$', delete_events),
        url(r'^youzi/album/save$', save_album),
        url(r'^youzi/album/select$', select_album),
        
        url(r'^update/draft/(?P<pk>[0-9]+)$', UpdateDraft.as_view()),
        url(r'^update/post/(?P<pk>[0-9]+)$', UpdatePost.as_view()),
        url(r'^update/(?P<pk>[0-9]+)$', UpdatePostIndexView.as_view()),
        url(r'^upload/markdown/post$', markdown_image_upload_handler),
        url(r'^upload/tinymce/post$', tinymce_image_upload_handler),
        url(r'^update/editor$', UpdateEditor.as_view()),
        url(r'^carousel$', CarouselIndexView.as_view()),
        url(r'^new/carousel$', CarouselEditView.as_view()),
        url(r'^add/carousel$', AddCarousel.as_view()),
        url(r'^delete/carousel/(?P<pk>[0-9]+)$', DeleteCarousel.as_view()),
        url(r'^update/carousel/(?P<pk>[0-9]+)$', CarouselUpdateView.as_view()),
        url(r'^update/carousel/id/(?P<pk>[0-9]+)$', UpdateCarousel.as_view()),
        url(r'^repository$', PostView.as_view(), name='index'),

        url(r'^set/upload/avatar$', avatar_image_upload_handler),
        
    ])),
    url(r'^logout$', LogoutView.as_view()),
]