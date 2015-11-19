from django.http import HttpResponse
from django.http import (HttpResponseBadRequest, HttpResponseNotFound,
    HttpResponseForbidden)
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.conf import settings

import json
import random

from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET

from utils.spellcheck_localization import SPELLCHECK_LOCALIZATION

from forms import (
    CustomUserCreationForm,
    GetRequestValidationForm,
    PostCommentForm,
    RegularUserLoginForm,
)
from models import Site, Thread, Comment
from decorators import json_response, cross_domain_post_response, host_check

try:
    import enchant
    from enchant.checker import SpellChecker
except ImportError:
    settings.SPELLCHECK_ENABLED = False


def add_to_session_list(request, key, value):
    session_data = request.session.setdefault(key, [])
    session_data.append(value)
    request.session[key] = session_data
    return request.session[key]


def remove_from_session_list(request, key, value):
    session_data = request.session.setdefault(key, [])
    if value in session_data:
        session_data.remove(value)
        request.session[key] = session_data

    return session_data


@require_POST
@csrf_exempt
@cross_domain_post_response
def register_user(request):
    form = CustomUserCreationForm(request.POST)

    if not form.is_valid():
        return HttpResponseBadRequest(_("Submitted data not valid."))

    cd = form.cleaned_data

    user = form.save()
    user = authenticate(email=cd['email'], password=cd['password'])
    login(request, user)

    return HttpResponse(unicode(user))


@require_POST
@csrf_exempt
@cross_domain_post_response
def logout_user(request):
    if request.user.is_authenticated():
        logout(request)
    return HttpResponse(
        _('logged out')
    )


@require_POST
@csrf_exempt
@cross_domain_post_response
def set_avatar_image(request):
    avatar_num = int(request.POST.get('avatar_num'))

    if avatar_num < settings.AVATAR_NUM_MIN or avatar_num > settings.AVATAR_NUM_MAX:
        HttpResponseBadRequest(
            _('invalid avatar_num number: ') + str(avatar_num)
        )

    if request.user.is_authenticated():
        u = request.user
        u.avatar_num = avatar_num
        u.save()

    request.session['user_avatar_num'] = avatar_num

    return HttpResponse('ok')


@require_POST
@csrf_exempt
@cross_domain_post_response
def login_user(request):
    form = RegularUserLoginForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest(
            _("Submitted data not valid.")
        )
    user = form.get_user()
    login(request, user)
    data = user.get_user_domain_data()
    request.session.update(data)

    return HttpResponse(unicode(user))


@require_POST
@csrf_exempt
@cross_domain_post_response
def comment(request):
    form = PostCommentForm(request.POST, request)
    if not form.is_valid():
        data = {'placement': 'comments_container', 'content': form.errors}
        return HttpResponseBadRequest(json.dumps(data))
    else:
        site = Site.objects.get(domain=form.cleaned_data['domain'])
        if not request.user.is_anonymous():
            if request.user.hidden.filter(id=site.id):
                return HttpResponseBadRequest(
                    _("User doesn't have permissions to post to this site."))
        new_comment = form.save()

    posted = add_to_session_list(request, 'posted_comments', new_comment.id)
    comments = form.cleaned_data['thread'].comments.all()

    if request.user.is_anonymous():
        site_admin = False
    else:
        site_admin = bool(request.user.get_comments(new_comment.id))

    request.session['all_comments'] = True

    resp = render(
        request,
        'comments.html',
        {
            'comments': comments,
            'posted_comments': posted,
            'last_posted_comment_id': posted[-1] if posted else None,
            'rs_customer_id': site.rs_customer_id,
            'all_comments': request.session.get('all_comments', False),
            'site_admin': site_admin
        }
    )
    data = {
        'placement': 'comments_container',
        'content': resp.content,
        'comment_id': new_comment.id
    }

    return HttpResponse(json.dumps(data))


@require_POST
@csrf_exempt
@cross_domain_post_response
@host_check
def like_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist as e:
        data = {'placement': 'comments_container', 'content': str(e)}
        return HttpResponseNotFound(json.dumps(data))

    if request.user.is_anonymous():
        site_admin = False
    else:
        site_admin = bool(request.user.get_comments(comment_id))

    if site_admin:
        if request.user.hidden.filter(id=comment.thread.site.id):
            return HttpResponseBadRequest(
                _('user is disabled on site with id %s') % comment.thread.site.id
            )

    liked_comments = request.session.get('liked_comments', [])
    disliked_comments = request.session.get('disliked_comments', [])

    if comment.id in disliked_comments:
        comment.undo_dislike(request.user)
        remove_from_session_list(request, 'disliked_comments', comment.id)
        comment.like(request.user)
        add_to_session_list(request, 'liked_comments', comment.id)

    elif comment.id not in liked_comments:
        comment.like(request.user)
        add_to_session_list(request, 'liked_comments', comment.id)

    comments = Comment.objects.filter(thread=comment.thread)
    posted_comments = request.session.get('posted_comments', [])

    site = comment.thread.site

    resp = render(
        request,
        'comments.html',
        {
            'comments': comments,
            'posted_comments': posted_comments,
            'last_posted_comment_id': posted_comments[-1] if posted_comments else None,
            'rs_customer_id': site.rs_customer_id,
            'all_comments': request.session.get('all_comments', False),
            'site_admin': site_admin,
        }
    )
    data = {'placement': 'comments_container', 'content': resp.content}

    return HttpResponse(json.dumps(data))


@require_POST
@csrf_exempt
@cross_domain_post_response
@host_check
def dislike_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist as e:
        data = {'placement': 'comments_container', 'content': str(e)}
        return HttpResponseNotFound(json.dumps(data))

    if request.user.is_anonymous():
        site_admin = False
    else:
        site_admin = bool(request.user.get_comments(comment_id))

    if site_admin:
        if request.user.hidden.filter(id=comment.thread.site.id):
            return HttpResponseBadRequest(
                _('user is disabled on site with id %s') % comment.thread.site.id
            )

    liked_comments = request.session.get('liked_comments', [])
    disliked_comments = request.session.get('disliked_comments', [])

    if comment.id in liked_comments:
        comment.undo_like(request.user)
        remove_from_session_list(request, 'liked_comments', comment.id)
        comment.dislike(request.user)
        add_to_session_list(request, 'disliked_comments', comment.id)

    elif comment.id not in disliked_comments:
        comment.dislike(request.user)
        add_to_session_list(request, 'disliked_comments', comment.id)

    comments = Comment.objects.filter(thread=comment.thread)
    posted_comments = request.session.get('posted_comments', [])

    site = comment.thread.site

    resp = render(
        request,
        'comments.html',
        {
            'comments': comments,
            'posted_comments': posted_comments,
            'last_posted_comment_id': posted_comments[-1] if posted_comments else None,
            'rs_customer_id': site.rs_customer_id,
            'all_comments': request.session.get('all_comments', False),
            'site_admin': site_admin,
        }
    )
    data = {'placement': 'comments_container', 'content': resp.content}

    return HttpResponse(json.dumps(data))


@require_POST
@csrf_exempt
@cross_domain_post_response
def hide_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist as e:
        data = {'placement': 'comments_container', 'content': str(e)}
        return HttpResponseNotFound(json.dumps(data))

    if request.user.is_anonymous():
        site_admin = False
    else:
        site_admin = bool(request.user.get_comments(comment_id))
    if not site_admin:
        data = {
            'placement': 'comments_container',
            'content': _("User not staff")
        }
        return HttpResponseForbidden(json.dumps(data))

    comment.hide()

    comments = Comment.objects.filter(thread=comment.thread)
    posted_comments = request.session.get('posted_comments', [])

    site = comment.thread.site

    resp = render(
        request,
        'comments.html',
        {
            'comments': comments,
            'posted_comments': posted_comments,
            'last_posted_comment_id': posted_comments[-1] if posted_comments else None,
            'rs_customer_id': site.rs_customer_id,
            'all_comments': request.session.get('all_comments', False),
            'site_admin': site_admin,
        }
    )
    data = {'placement': 'comments_container', 'content': resp.content}

    return HttpResponse(json.dumps(data))


@require_POST
@csrf_exempt
@cross_domain_post_response
def unhide_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist as e:
        data = {'placement': 'comments_container', 'content': str(e)}
        return HttpResponseNotFound(json.dumps(data))

    if request.user.is_anonymous():
        site_admin = False
    else:
        site_admin = bool(request.user.get_comments(comment_id))
    if not site_admin:
        data = {
            'placement': 'comments_container',
            'content': _("User not staff")
        }
        return HttpResponseForbidden(json.dumps(data))

    comment.unhide()

    comments = Comment.objects.filter(thread=comment.thread)
    posted_comments = request.session.get('posted_comments', [])

    site = comment.thread.site

    resp = render(
        request,
        'comments.html',
        {
            'comments': comments,
            'posted_comments': posted_comments,
            'last_posted_comment_id': posted_comments[-1] if posted_comments else None,
            'rs_customer_id': site.rs_customer_id,
            'all_comments': request.session.get('all_comments', False),
            'site_admin': site_admin,
        }
    )
    data = {'placement': 'comments_container', 'content': resp.content}

    return HttpResponse(json.dumps(data))


@require_POST
@csrf_exempt
@cross_domain_post_response
def like_thread(request, thread_id):
    try:
        thread = Thread.objects.get(id=thread_id)
    except Thread.DoesNotExist as e:
        data = {
            'placement': 'comments_header',
            'content': str(e)
        }
        return HttpResponseNotFound(json.dumps(data))

    if not request.user.is_anonymous():
        if request.user.hidden.filter(id=thread.site.id):
            return HttpResponseBadRequest(
                _('user is disabled on site with id %s') % thread.site.id
            )

    liked_threads = request.session.get('liked_threads', [])
    disliked_threads = request.session.get('disliked_threads', [])

    # if user disliked thread already, remove his dislike and add like
    if thread.id in disliked_threads:
        thread.undo_dislike(request.user)
        remove_from_session_list(request, 'disliked_threads', thread.id)
        thread.like(request.user)
        add_to_session_list(request, 'liked_threads', thread.id)

    elif thread.id not in liked_threads:
        # if user haven't had interaction with thread, like the thread
        thread.like(request.user)
        # save liked information to the session
        add_to_session_list(request, 'liked_threads', thread.id)

    resp = render(request, 'header.html', {'thread': thread})
    data = {'placement': 'comments_header', 'content': resp.content}

    return HttpResponse(json.dumps(data))


@require_POST
@csrf_exempt
@cross_domain_post_response
def dislike_thread(request, thread_id):
    try:
        thread = Thread.objects.get(id=thread_id)
    except Thread.DoesNotExist as e:
        data = {
            'placement': 'comments_header',
            'content': str(e)
        }
        return HttpResponseNotFound(json.dumps(data))

    if not request.user.is_anonymous():
        if request.user.hidden.filter(id=thread.site.id):
            return HttpResponseBadRequest(
                _('user is disabled on site with id %s') % thread.site.id
            )
    liked_threads = request.session.get('liked_threads', [])
    disliked_threads = request.session.get('disliked_threads', [])

    # if user disliked thread already, remove his dislike and add like
    if thread.id in liked_threads:
        thread.undo_like(request.user)
        remove_from_session_list(request, 'liked_threads', thread.id)
        thread.dislike(request.user)
        add_to_session_list(request, 'disliked_threads', thread.id)

    elif thread.id not in disliked_threads:
        # if user haven't had interaction with thread, like the thread
        thread.dislike(request.user)
        # save liked information to the session
        add_to_session_list(request, 'disliked_threads', thread.id)

    resp = render(request, 'header.html', {'thread': thread})
    data = {'placement': 'comments_header', 'content': resp.content}

    return HttpResponse(json.dumps(data))


@require_GET
@csrf_exempt
@json_response
def comment_count(request):
    domain = request.GET.get('domain', None)
    thread_url = request.GET.get('thread_url', None)

    try:
        site = Site.objects.get(domain=domain)
    except Site.DoesNotExist:
        return HttpResponseBadRequest(
            _('site with domain %s not found') % domain
        )

    try:
        thread = site.threads.get(url=thread_url)
    except Thread.DoesNotExist:
        return HttpResponseBadRequest(
            _('thread with url %s not found') % thread_url
        )

    comment_count = thread.comments.filter(hidden=False).count()

    return {"comment_count": comment_count}


@require_GET
@csrf_exempt
@json_response
def get_comments(request):
    form = GetRequestValidationForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest(
            _('could not get comments, errors: %s') % form.errors
        )

    domain_name = form.cleaned_data['domain']
    thread_id = form.cleaned_data['thread']

    try:
        site = Site.objects.get(domain=domain_name)
        if not request.user.is_anonymous():
            if request.user.hidden.filter(id=site.id):
                return HttpResponseBadRequest(
                    _('user is disabled on site with id %s') % site.id
                )
    except Site.DoesNotExist:
        return HttpResponseBadRequest(
            'domain with name %s does not exist' % domain_name
        )

    if not thread_id:
        return HttpResponseBadRequest(
            _('thread url not provided')
        )

    thread, created = site.threads.get_or_create(id=thread_id)

    posted_comments = request.session.get('posted_comments', [])
    all_comments = request.GET.get('all', False)
    if all_comments:
        request.session['all_comments'] = True

    if request.user.is_anonymous():
        site_admin = False
    else:
        site_admin = request.user.is_site_admin(domain_name)

    comments = thread.comments.exclude(user__hidden__in=[site]).distinct()
    resp = render(
        request,
        "comments.html",
        {
            'comments': comments,
            'posted_comments': posted_comments,
            'last_posted_comment_id': posted_comments[-1] if posted_comments else None,
            'rs_customer_id': site.rs_customer_id,
            'all_comments': all_comments,
            'site_admin': site_admin
        }
    )

    return {"html": resp.content, "html_container_name": "comments_container"}


@require_GET
@json_response
def thread_info(request):
    domain = request.GET.get('domain', None)
    thread_url = request.GET.get('thread', None)
    titles = {
        'selector_title': request.GET.get('selector_title', ""),
        'page_title': request.GET.get('page_title', ""),
        'h1_title': request.GET.get('h1_title', "")
    }

    try:
        site = Site.objects.get(domain=domain)
    except Site.DoesNotExist:
        return HttpResponseBadRequest(
            'site with domain %s not found' % domain
        )

    thread, created = site.threads.get_or_create(url=thread_url)
    thread.titles = titles
    thread.save()

    if request.session.get('all_comments'):
        del request.session['all_comments']

    # add random avatar to session if anonymous
    avatar_num = request.session.get("user_avatar_num", None)

    if not avatar_num and request.user.is_anonymous():
        avatar_num = random.randint(
            settings.AVATAR_NUM_MIN,
            settings.AVATAR_NUM_MAX
        )
        request.session['user_avatar_num'] = avatar_num

    return {
        "thread_id": thread.id,
        "comments_enabled": thread.allow_comments,
        "spellcheck_enabled": settings.SPELLCHECK_ENABLED,
        "spellcheck_localization": SPELLCHECK_LOCALIZATION
    }


@require_GET
@json_response
def get_header(request):
    form = GetRequestValidationForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest(
            _('could not get comments, errors: %s') % form.errors
        )

    domain_name = form.cleaned_data['domain']
    thread_id = form.cleaned_data['thread']

    try:
        site = Site.objects.get(domain=domain_name)
    except Site.DoesNotExist:
        return HttpResponseBadRequest(
            _('domain with name %s does not exist') % domain_name
        )

    thread, created = site.threads.get_or_create(id=thread_id)

    resp = render(request, "header.html", {'thread': thread})

    return {"html": resp.content, "html_container_name": "comments_header"}


@require_GET
@json_response
def get_footer(request):
    form = GetRequestValidationForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest(
            _('could not get comments, errors: %s') % form.errors
        )

    domain_name = form.cleaned_data['domain']
    thread_id = form.cleaned_data['thread']

    try:
        site = Site.objects.get(domain=domain_name)
    except Site.DoesNotExist:
        return HttpResponseBadRequest(
            _('domain with name %s does not exist') % domain_name
        )

    thread, created = site.threads.get_or_create(id=thread_id)

    resp = render(
        request,
        "footer.html", {
            'user': request.user,
            'site': site,
            'avatars': range(1, 29),
            'user_avatar_num': request.session.get('user_avatar_num', 6),
            'rs_customer_id': site.rs_customer_id,
        }
    )

    return {"html": resp.content, "html_container_name": "comments_footer"}


@require_POST
@csrf_exempt
@cross_domain_post_response
def incorrect_words(request):
    """
    Checks text and returns list of incorrectly spelled words.
    """
    if not settings.SPELLCHECK_ENABLED:
        return HttpResponseBadRequest(
            _('spell checking not supported')
        )

    text = request.POST.get('text')

    if not text:
        return HttpResponseBadRequest(
            _('text not provided')
        )

    chkr = SpellChecker(settings.LANGUAGE_CODE)
    chkr.set_text(text)
    errors = [err.word for err in chkr]
    data = {'data': [errors]}

    return HttpResponse(json.dumps(data))


@require_POST
@csrf_exempt
@cross_domain_post_response
def spellcheck_suggestions(request):
    """
    Returns suggested solutions for incorrectly spelled word.
    """
    if not settings.SPELLCHECK_ENABLED:
        return HttpResponseBadRequest(
            _('spell checking not supported')
        )

    word = request.POST.get('word')

    if not word:
        return HttpResponseBadRequest(
            _('word not provided')
        )

    d = enchant.Dict(settings.LANGUAGE_CODE)
    suggestions = d.suggest(word) if not d.check(word) else []

    return HttpResponse(json.dumps({'data': suggestions}))
