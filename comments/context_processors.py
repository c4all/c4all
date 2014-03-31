def base_url(request):
    from django.conf import settings
    return {
        'BASE_URL': settings.BASE_URL,
        'BASE_STATIC': settings.BASE_STATIC,
        'WIDGET_COMMENTS_DEFAULT_NUMBER': settings.WIDGET_COMMENTS_DEFAULT_NUMBER,
    }
