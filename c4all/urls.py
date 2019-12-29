from django.conf.urls import include, url

from django.contrib import admin as djadmin
djadmin.autodiscover()

from comments import urls as comments_urls

urlpatterns = [
    # Examples:
    # url(r'^$', 'myapp.views.home', name='home'),
    # url(r'^myapp/', include('myapp.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^djadmin/', include(djadmin.site.urls)),
    url(r'^admin/', include('admin.urls', namespace='c4all_admin')),
    url(r'', include(comments_urls, namespace='comments'))
]
