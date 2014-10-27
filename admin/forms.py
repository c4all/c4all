from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

from comments.models import Comment

from datetime import date, datetime, timedelta


UserModel = get_user_model()

class IntervalSelectionForm(forms.Form):
    """
    Form used for interval filtering for various objects which have some kind
    of date to be filtered upon (e.g. created date).
    """
    INTERVAL_CHOICE_ALL_DATES = "all_dates"
    INTERVAL_CHOICE_TODAY = "today"
    INTERVAL_CHOICE_THIS_WEEK = "this_week"
    INTERVAL_CHOICE_THIS_MONTH = "this_month"

    INTERVAL_FILTER_CHOICES = [
        (INTERVAL_CHOICE_ALL_DATES, _("Show all dates")),
        (INTERVAL_CHOICE_TODAY, _("Today")),
        (INTERVAL_CHOICE_THIS_WEEK, _("This Week")),
        (INTERVAL_CHOICE_THIS_MONTH, _("This Month")),
    ]


    interval = forms.ChoiceField(
        choices=INTERVAL_FILTER_CHOICES,
        initial=INTERVAL_CHOICE_ALL_DATES
    )

    def get_date(self):
        # if form is valid, return one of the values dependent on interval
        # field choice
        interval = self.cleaned_data['interval']

        if interval == self.INTERVAL_CHOICE_TODAY:
            return date.today()
        elif interval == self.INTERVAL_CHOICE_THIS_WEEK:
            return date.today() - timedelta(datetime.today().weekday())
        elif interval == self.INTERVAL_CHOICE_THIS_MONTH:
            return date.today() - timedelta(date.today().day - 1)
        # if form is not valid or interval value was not found, return date
        # which is the start date of the UNIX epoch (Thursday, 1 January 1970)
        else:
            return datetime.utcfromtimestamp(0)


class BulkActionForm(forms.Form):
    BULK_ACTION_CHOICES = [
        ('delete', _('Delete')),
        ('hide', _('Unpublish'))
    ]
    site_id = forms.CharField(required=True)
    action = forms.ChoiceField(choices=BULK_ACTION_CHOICES)


class UserBulkActionForm(BulkActionForm):
    choices = forms.ModelMultipleChoiceField(
        queryset=UserModel.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )


class CommentBulkActionForm(BulkActionForm):
    choices = forms.ModelMultipleChoiceField(
        queryset=Comment.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )
