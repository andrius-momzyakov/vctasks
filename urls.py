# coding: UTF-8
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from django.contrib import auth
from django.contrib.auth.views import login, logout
import vctasks.addtask.views
import vctasks.settings as settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
admin.autodiscover()

urlpatterns = patterns('vctasks.addtask.views',
		url(r'^addtask/$', 'add_task_form'),
		url(r'^addtask/(\d+)/$', 'add_task_form'),
		url(r'^appointtask/$', 'appoint_task_form'),
		url(r'^appointtask/(\d+)/$', 'appoint_task_form'),
		url(r'^executetask/$', 'execute_task_form'),
		url(r'^executetask/(\d+)/$', 'execute_task_form'),
		url(r'^addfile/$', 'add_file_form'),
		url(r'^deletefile/(?P<ptask_id>\d+)/(?P<pdoc_id>\d+)/$', 'delete_file'),
    url(r'^tasklist/$', 'common_tasklist'),
    url(r'^tasklist/(\d+)/$', 'common_tasklist'),
    url(r'^home/$', 'home_page'),
    url(r'^$', 'start_page'),
    url(r'^edit_task/(\d+)/$', 'edit_task'),
    url(r'^taskdetail/(\d+)/$', 'task_detail'),
    url(r'^file/$', 'serve_base_file'),
    url(r'^findtask/$', 'find_task'), # by ID  
    url(r'^search_form/$', 'search_form'),
    url(r'^change_password/$', 'change_password'),
    url(r'^task_notfound/$', 'task_notfound'),
    url(r'^appraise/(\d+)/$',  'appraise_form'),
    url(r'^show_fsencoding/$', 'show_fsencoding'),
    url(r'^show_user/$', 'show_user'),
    url(r'^admin_submenu/$', 'admin_submenu'),
    url(r'^import_users/$', 'import_users'),
    url(r'^search_user_form/$', 'search_user_form'),
    url(r'^users_found/$', 'search_user_form'),
    url(r'^edit_user/$', 'edit_user'),
    url(r'^edit_user/(\d+)/$', 'edit_user'),
    url(r'^drop_password/(\d+)/$', 'drop_password'),
    url(r'^subtask/(\d+)/$', 'create_subtask'),
)

urlpatterns += patterns('',
#    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
#    url(r'^file/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'c:/media/'}),
    url(r'^accounts/login/$',  login),
#    url(r'^accounts/logout/$', logout),
    url(r'^accounts/logout/$', vctasks.addtask.views.my_logout),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
