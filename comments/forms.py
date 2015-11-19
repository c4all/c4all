from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth import authenticate

from models import (Comment, Site, Thread)
from django.utils.translation import ugettext as _

import re


UserModel = get_user_model()


class UserLoginForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True, widget=forms.PasswordInput())

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        self.user = authenticate(email=email, password=password)

        if self.user is None:
            raise forms.ValidationError(_("wrong username or password"))

        if not self.user.is_active:
            raise forms.ValidationError(_("user not active"))

        return self.cleaned_data


class RegularUserLoginForm(UserLoginForm):
    site_id = forms.CharField(required=True, widget=forms.HiddenInput())

    def clean(self):
        super(RegularUserLoginForm, self).clean()

        if not self.user:
            return self.cleaned_data

        if self.user.hidden.filter(id__in=[self.cleaned_data['site_id']]):
            raise forms.ValidationError(_("user hidden"))

        return self.cleaned_data

    def get_user(self):
        return self.user


class StaffUserLoginForm(UserLoginForm):

    def clean(self):
        super(StaffUserLoginForm, self).clean()

        if not self.user:
            return self.cleaned_data

        if not self.user.is_staff:
            raise forms.ValidationError(_("user not staff"))

        if not self.user.get_sites().count():
            raise forms.ValidationError(
                _("user is not admin for any site, log in as \
                    superuser to assign the user to a site"))

        return self.cleaned_data

    def get_user(self):
        return self.user


class CustomUserCreationForm(forms.ModelForm):
    """
    A form for creating new users. Includes all the
    required fields, plus a repeated password.
    """
    class Meta:
        model = UserModel
        fields = ("email", "full_name", "avatar_num")

    email = forms.EmailField(required=True)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Password Confirmation",
        widget=forms.PasswordInput
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserModel.objects.filter(email=email).exists():
            raise forms.ValidationError(_("You have already registered"))
        return email

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if not full_name:
            raise forms.ValidationError(_("Please enter your name"))
        return full_name

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            msg = _("Passwords don't match")
            raise forms.ValidationError(msg)
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.full_name = self.cleaned_data.get('full_name')
        if commit:
            user.save()
        return user


class CustomUserChangeForm(forms.ModelForm):
    """
    A form for updating users. Includes all the fields
    on the user, but replaces the password field with
    admin"s password hash display field.
    """
    class Meta:
        model = UserModel

    password = ReadOnlyPasswordHashField(
        help_text=(
            "Raw passwords are not stored, so there is no way to see "
            "this user's password, but you can change the password "
            "using <a href=\"password/\">this form</a>.")
    )

    def clean_password(self):
        # Regardless of what the user provides, return the
        # initial value. This is done here, rather than on
        # the field, because the field does not have access
        # to the initial value
        return self.initial["password"]


class PostCommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text', 'poster_name', 'thread')

    domain = forms.CharField(required=True)
    poster_name = forms.CharField(required=False)

    def __init__(self, data, request, *args, **kwargs):
        self.user = request.user

        # default avatar -> green diamond -> "6.png"
        self.avatar_num = request.session.get('user_avatar_num', 6)
        self.ip_address = data.get('ip_address')
        super(PostCommentForm, self).__init__(data)

    def clean_poster_name(self):
        # user can be anonymous but must have a name
        name = self.cleaned_data.get('poster_name')
        if name:
            return name
        elif not self.user.is_anonymous():
            return self.user.get_full_name()
        else:
            raise forms.ValidationError(_('poster name not provided'))

    def clean_domain(self):
        domain = self.cleaned_data.get('domain')

        if domain:
            if Site.objects.filter(domain=domain).exists():
                return domain
            else:
                raise forms.ValidationError(
                    _("site with domain %s does not exist") % domain
                )
        else:
            raise forms.ValidationError(_("domain not provided"))

    def clean(self):
        domain = self.cleaned_data.get('domain')
        thread = self.cleaned_data.get('thread')

        if not thread or not domain:
            raise forms.ValidationError(_("thread not provided"))

        if not thread.allow_comments:
            raise forms.ValidationError(_("comments not allowed"))

        try:
            site = Site.objects.get(domain=domain)
            if not self.user.is_anonymous():
                if self.user.hidden.filter(id=site.id):
                    raise forms.ValidationError(
                        _('user is disabled on site with id %s') % site.id
                    )
            site.threads.get(id=thread.id)
        except Thread.DoesNotExist:
            raise forms.ValidationError(
                _('thread with id %s does not exist') % thread.id
            )

        return self.cleaned_data

    def save(self, *args, **kwargs):
        comment = super(PostCommentForm, self).save(
            *args,
            commit=False,
            **kwargs
        )

        comment.user = None if self.user.is_anonymous() else self.user

        comment.avatar_num = self.avatar_num
        if self.ip_address:
            comment.ip_address = self.ip_address
        comment.save()

        return comment


class GetRequestValidationForm(forms.Form):

    domain = forms.CharField()
    thread = forms.IntegerField()
    start = forms.DateTimeField(required=False)
    count = forms.IntegerField(required=False, initial=100)


class SiteForm(forms.ModelForm):

    class Meta:
        model = Site

    def clean_domain(self):
        p = re.compile(settings.DOMAIN_URL_PATTERN)
        m = p.match(self.cleaned_data['domain'])

        if m:
            self.cleaned_data['domain'] = m.groups()[1]
        else:
            raise forms.ValidationError(_("Enter a valid value"))

        return self.cleaned_data['domain']
