from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from comments.models import Site

import json


def json_response(func):
    """
    A decorator thats takes a view response and turns it
    into json. If a callback is added through GET or POST
    the response is JSONP.
    """
    def decorator(request, *args, **kwargs):
        objects = func(request, *args, **kwargs)
        if isinstance(objects, HttpResponse):
            return objects

        data = json.dumps(objects)
        if 'callback' in request.REQUEST:
            # a jsonp response!
            data = '%s(%s);' % (request.REQUEST['callback'], data)
            return HttpResponse(data, "text/javascript")

        return HttpResponse(data, "application/json")
    return decorator


def cross_domain_post_response(func):
    def decorator(request, *args, **kwargs):
        resp = func(request, *args, **kwargs)

        iframe_id = request.POST.get('iframeId', '')

        data = {
            "status_code": resp.status_code,
            "resp_data": resp.content,
            "request_path": request.path,
            "iframeId": iframe_id,
        }

        return render(
            request,
            'post_response.html',
            {'data': json.dumps(data)}
        )

    return decorator


def host_check(func):
    def decorator(request, *args, **kwargs):
        domain = request.POST.get('domain')

        if domain:
            try:
                Site.objects.get(domain=domain)
            except Site.DoesNotExist:
                data = {
                    'placement': 'comments_container',
                    'content': 'unknown domain'
                }
                return HttpResponseBadRequest(json.dumps(data))
        else:
            data = {
                'placement': 'comments_container',
                'content': 'no domain provided'
            }
            return HttpResponseBadRequest(json.dumps(data))

        return func(request, *args, **kwargs)

    return decorator
