from django.core.paginator import (Paginator, EmptyPage, PageNotAnInteger)
from django.conf import settings

def paginate_data(request, data, per_page=settings.PER_PAGE):
    paginator = Paginator(data, per_page)

    page = request.GET.get('page')

    try:
        data = paginator.page(page)
    except PageNotAnInteger:
        data = paginator.page(1)
    except EmptyPage:
        data = paginator.page(paginator.num_pages)

    return data
