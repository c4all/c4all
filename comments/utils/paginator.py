def get_paginated_data(data, start, count, order='-id'):
    if order.startswith('-'):
        asc = False
        order_field = order[1:]
    else:
        asc = True
        order_field = order

    ordered_data = data.order_by(order)
    if start:
        filter_fields = {
            order_field + ('__gte' if asc else '__lte'): start
        }
        ordered_data = ordered_data.filter(**filter_fields)

    retval = list(ordered_data[:count + 1])
    if len(retval) > count:
        obj = retval[count]
        while '__' in order_field:
            prefix, order_field = order_field.split('__', 1)
            obj = getattr(obj, prefix)
        next = getattr(obj, order_field)
        retval = retval[:-1]
    else:
        next = None

    return (retval, next)
