from django.conf.urls import patterns, url

from views import (threads, comments, hide_comment, unhide_comment,
    delete_comment, login_admin, logout_admin, users, user_bulk_actions,
    comment_bulk_actions, hide_user, unhide_user, delete_user, change_password,
    unpublished_comments, unpublished_comment_bulk_actions
)

urlpatterns = patterns("",
    url(r'^site(?:/(?P<site_id>\d+))?/threads$', threads, name='get_threads'),
    url(r'^thread/(?P<thread_id>\d+)/comments$', comments, name='get_thread_comments'),
    url(r'^thread/(?P<thread_id>\d+)/comment_bulk_actions$',
        comment_bulk_actions,
        name="comment_bulk_actions"
    ),
    url(r'^site(?:/(?P<site_id>\d+))?/comment/unpublished$', unpublished_comments, name='unpublished_comments'),
    url(r'^site(?:/(?P<site_id>\d+))?/unpublished_comment_bulk_actions$',
        unpublished_comment_bulk_actions,
        name="unpublished_comment_bulk_actions"
    ),
    url(r'^comment/(?P<comment_id>\d+)/hide$', hide_comment, name='hide_comment'),
    url(r'^comment/(?P<comment_id>\d+)/unhide$',
        unhide_comment,
        name='unhide_comment'
    ),
    url(r'^comment/(?P<comment_id>\d+)/delete$',
        delete_comment,
        name='delete_comment'
    ),

    url(r'^$', login_admin, name='login_admin'),
    url(r'^logout$', logout_admin, name='logout_admin'),

    url(r'^site(?:/(?P<site_id>\d+))?/users$', users, name='get_users'),
    url(r'^user_bulk_actions$', user_bulk_actions, name="user_bulk_actions"),
    url(r'^user/(?P<site_id>\d+)/(?P<user_id>\d+)/hide$', hide_user, name='hide_user'),
    url(r'^user/(?P<site_id>\d+)/(?P<user_id>\d+)/unhide$', unhide_user, name='unhide_user'),
    url(r'^user/(?P<site_id>\d+)/(?P<user_id>\d+)/delete$',
        delete_user, name='delete_user'),
    url(r'^user/(?P<user_id>\d+)/change_password$',
        change_password,
        name="change_password"
    ),
)
