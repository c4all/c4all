from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Site, Thread, Comment
from .forms import CustomUserChangeForm, CustomUserCreationForm, SiteForm


class CustomUserAdmin(UserAdmin):
    # Set the add/modify forms
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ("email", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions",)
    fieldsets = (
        (
            None,
            {"fields": ("email", "password", "full_name")}
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions")
            }
        ),
        (
            "Important dates",
            {
                "fields": ("last_login",)
            }
        ),
    )
    add_fieldsets = (
        (None,
            {
                "classes": ("wide",),
                "fields": ("email", "password", "password2", "full_name")
            }),
    )


class SiteAdmin(admin.ModelAdmin):
    form = SiteForm
    filter_horizontal = ('admins',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Site, SiteAdmin)
admin.site.register(Thread)
admin.site.register(Comment)
