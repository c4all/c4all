try:
    from django.conf.urls import *
except ImportError:  # django < 1.4
    from django.conf.urls.defaults import *

from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

from .views import *


urlpatterns = patterns('',
    url(r'^register$', register_user, name='register_user'),
    url(r'^login$', login_user, name='login_user'),
    url(r'^logout$', logout_user, name='logout_user'),
    url(r'^set_avatar$', set_avatar_image, name='set_avatar_image'),
    url(r'^comment$', comment, name='comment'),
    url(r'^comment/(?P<comment_id>\d+)/like', like_comment, name='like_comment'),
    url(r'^comment/(?P<comment_id>\d+)/dislike', dislike_comment, name='dislike_comment'),
    url(r'^comment/(?P<comment_id>\d+)/hide', hide_comment, name='hide_comment'),
    url(r'^comment/(?P<comment_id>\d+)/unhide', unhide_comment, name='unhide_comment'),
    url(r'^comments$', get_comments, name='get_comments'),
    url(r'^thread_info$', thread_info, name='thread_info'),
    url(r'^thread/(?P<thread_id>\d+)/like$', like_thread, name='like_thread'),
    url(r'^thread/(?P<thread_id>\d+)/dislike$', dislike_thread, name='dislike_thread'),
    url(r'^header', get_header, name='get_header'),
    url(r'^footer', get_footer, name='get_footer'),
    url(r'^spellcheck/incorrect_words$', incorrect_words, name='incorrect_words'),
    url(r'^spellcheck/suggestions$', spellcheck_suggestions, name='spellcheck_suggestions'),
    url(r'^comment_count$', comment_count, name='comment_count'),

    # test url
    url(r'^testpage$', login_required(TemplateView.as_view(template_name='usertest-example.html')), name="testpage"),

)
