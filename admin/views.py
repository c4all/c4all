from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.utils.translation import ugettext as _
from django.db.models import Max

from comments.models import Thread, Comment, CustomUser, Site
from comments.forms import StaffUserLoginForm
from admin.decorators import admin_required, ajax_required
from admin.paginator import paginate_data
from admin.forms import (
    IntervalSelectionForm, UserBulkActionForm, CommentBulkActionForm)

import json


def login_admin(request):
    if request.user.is_authenticated and request.user.is_staff:
        if 'last_site_id' in request.session:
            return redirect('c4all_admin:get_threads', site_id=request.session['last_site_id'])

        return redirect('c4all_admin:get_threads')

    form = StaffUserLoginForm(request.POST or None)

    if form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('c4all_admin:get_threads')

    return render(request, "custom_admin/login.html", {'form': form})


@admin_required
def logout_admin(request):
    logout(request)
    return redirect("c4all_admin:login_admin")


@admin_required
@ajax_required
def change_password(request, user_id):
    """
    Changes user's password. Cannot change admins's password.
    """
    user = get_object_or_404(CustomUser, id=user_id, is_staff=False)
    form = AdminPasswordChangeForm(user, data=request.POST or None)

    if form.is_valid():
        if request.user.is_superuser:
            form.save()

    resp = render(
        request,
        "snippets/change_password_form.html",
        {"form": form}
    )

    response_data = {"html": resp.content, 'user_id': user.id}

    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json"
    )


@admin_required
def threads(request, site_id=None):
    """
    Fetches and returns threads for a given time period. If site_id not
    provided, threads from first site in DB are returned.
    """
    site = None
    sites = request.user.get_sites()

    if site_id:
        site = get_object_or_404(sites, id=site_id)
    elif request.session.get('last_site_id'):
        site_id = request.session['last_site_id']
        site = get_object_or_404(sites, id=site_id)
    else:
        site = sites[0] if sites.exists() else None

    interval_selection_form = IntervalSelectionForm(request.POST or None)

    date = None
    if interval_selection_form.is_valid():
        date = interval_selection_form.get_date()

    thread_list = Thread.objects.filter(site__in=sites).annotate(
        max_comment_date=Max('comments__created'))

    if date:
        thread_list = thread_list.filter(created__gte=date)

    if site:
        thread_list = thread_list.filter(site=site)

    sort_by = request.GET.get("sort_by", None)

    if sort_by == "thread_date":
        thread_list = thread_list.order_by('-created')
    else:
        list_thread_list = list(thread_list.filter(
                    max_comment_date__isnull=False).order_by('-max_comment_date'))

        list_thread_list += list(thread_list.filter(
                    max_comment_date__isnull=True).order_by('-max_comment_date'))

        thread_list = list_thread_list

    threads = paginate_data(request, thread_list)

    if site:
        request.session['last_site_id'] = site.id

    return render(
        request,
        "custom_admin/threads.html",
        {
            "threads": threads,
            "interval_selection_form": interval_selection_form,
            "sites": sites,
            "selected_site": site,
            "pagination_objects_name": _("articles"),
        }
    )


@admin_required
def comments(request, thread_id):
    """
    Returns all comments for thread with thread_id. If hidden param is true,
    returns only hidden comments for aforementioned thread.
    """
    threads = request.user.get_threads()
    thread = get_object_or_404(threads, id=thread_id)

    hidden = request.GET.get('hidden', False)
    comments_list = thread.comments.all()

    if hidden:
        comments_list = comments_list.filter(hidden=True)

    hidden_comments_count = comments_list.filter(hidden=True).count()

    comments = paginate_data(request, comments_list)

    bulk_action_form = CommentBulkActionForm()

    return render(
        request,
        "custom_admin/comments.html",
        {
            "comments": comments,
            "thread": thread,
            "hidden_comments_count": hidden_comments_count,
            "selected_site": thread.site,
            "bulk_action_form": bulk_action_form,
            "pagination_objects_name": _("comments"),
        }
    )


@admin_required
@require_POST
@ajax_required
def hide_comment(request, comment_id):
    comment = get_object_or_404(request.user.get_comments(), id=comment_id)
    comment.hide()

    return HttpResponse(
        json.dumps({'state': 'hidden'}),
        content_type="application/json"
    )


@admin_required
@require_POST
@ajax_required
def unhide_comment(request, comment_id):
    comment = get_object_or_404(request.user.get_comments(), id=comment_id)
    comment.unhide()

    return HttpResponse(
        json.dumps({'state': 'unhidden'}),
        content_type="application/json"
    )


@admin_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(request.user.get_comments(), id=comment_id)

    comment.delete(request.user)

    return redirect('c4all_admin:get_thread_comments', comment.thread.id)


@admin_required
def users(request, site_id):
    """
    Returns all users if hidden parameter not provided, hidden users if
    hidden parameter is True.
    """
    site = None
    sites = request.user.get_sites()

    if site_id:
        site = get_object_or_404(sites, id=site_id)
    elif request.session.get('last_site_id'):
        site_id = request.session['last_site_id']
        site = get_object_or_404(sites, id=site_id)
    else:
        site = sites[0] if sites.exists() else None

    hidden = request.GET.get('hidden', False)
    user_list = request.user.get_users()
    if site:
        user_list = user_list.filter(comments__thread__site=site)
        request.session['last_site_id'] = site.id

    if hidden and site:
        user_list = user_list.filter(hidden__in=[site])

    hidden_users_count = user_list.filter(hidden__in=[site]).count()

    users = paginate_data(request, user_list)

    bulk_action_form = UserBulkActionForm()
    return render(
        request,
        "custom_admin/users.html",
        {
            "users": users,
            "hidden_users_count": hidden_users_count,
            "bulk_action_form": bulk_action_form,
            "pagination_objects_name": _("users"),
            "sites": sites,
            "selected_site": site,
        }
    )


@admin_required
@require_POST
def user_bulk_actions(request):
    """
    Endpoint which handles bulk actions (namely hide and delete) for users.
    Redirects user to users page from which he came.
    """
    form = UserBulkActionForm(request.POST or None)

    if form.is_valid():
        cd = form.cleaned_data
        site = get_object_or_404(Site, id=form.cleaned_data['site_id'])

        if cd['action'] == 'delete':
            users = cd['choices'].filter(
                id__in=request.user.get_users(), is_staff=False)
            Comment.objects.filter(user__id__in=users).delete()
        if cd['action'] == 'hide':
            users = cd['choices'].filter(id__in=request.user.get_users())
            for user in users:
                user.hidden.add(site)

    return redirect("c4all_admin:get_users")


@admin_required
@require_POST
def comment_bulk_actions(request, thread_id):
    """
    Endpoint which handles bulk actions (namely hide and delete) for comments.
    Redirects user to comments page from which he came.
    """
    form = CommentBulkActionForm(request.POST or None)

    if form.is_valid():
        cd = form.cleaned_data
        comments = cd['choices'].filter(id__in=request.user.get_comments())
        if cd['action'] == 'delete':
            Comment.objects.bulk_delete(comments)
        if cd['action'] == 'hide':
            Comment.objects.filter(
                id__in=comments).update(hidden=True)

    return redirect("c4all_admin:get_thread_comments", thread_id)


@admin_required
@require_POST
@ajax_required
def hide_user(request, site_id, user_id):
    """
    Endpoint which handles user hiding. If provided user or site id doesn't
    exist or identifies staff member, 404 response is returned.
    """
    user = get_object_or_404(
        request.user.get_users(), id=user_id, is_staff=False)
    site = get_object_or_404(
        request.user.get_sites(), id=site_id)
    user.hide(site)

    return HttpResponse(
        json.dumps({'state': 'hidden'}),
        content_type="application/json"
    )


@admin_required
@require_POST
@ajax_required
def unhide_user(request, site_id, user_id):
    """
    Endpoint which handles user unhiding. If provided user or site id doesn't
    exist or identifies staff member, 404 response is returned.
    """
    user = get_object_or_404(
        request.user.get_users(), id=user_id, is_staff=False)
    site = get_object_or_404(
        request.user.get_sites(), id=site_id)
    user.unhide(site)

    return HttpResponse(
        json.dumps({'state': 'unhidden'}),
        content_type="application/json"
    )


@admin_required
def delete_user(request, site_id, user_id):
    """
    Endpoint for user deletion. All user comments for site are erased from
    DB. Redirects to all users endpoint.
    """
    user = get_object_or_404(
        request.user.get_users(), id=user_id, is_staff=False)
    comments = user.comments.filter(thread__site__id=site_id)
    comments.delete()

    return redirect("c4all_admin:get_users")
