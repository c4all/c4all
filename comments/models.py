from django.db import models
from django.db.models import Q
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
from urlparse import urljoin


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None):

        if not email:
            raise ValueError('Users must have an email')

        user = self.model(
            email=CustomUserManager.normalize_email(email),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email,
        organization and password.
        """
        user = self.create_user(
            email=email,
            password=password)

        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)
        return user

    def bulk_delete(self, users, *args, **kwargs):
        self.filter(id__in=users, *args, **kwargs).delete()


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Inherits from both the AbstractBaseUser and
    PermissionMixin.
    """
    email = models.EmailField(
        max_length=255,
        db_index=True,
        unique=True,
        blank=True
    )
    full_name = models.CharField(max_length=255)
    USERNAME_FIELD = 'email'
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    objects = CustomUserManager()
    avatar_num = models.IntegerField(default=6)  # green diamond
    hidden = models.ManyToManyField(
        'Site', blank=True, related_name='hidden_users')
    created = models.DateTimeField(default=timezone.now)

    def get_full_name(self):
        return self.full_name if self.full_name else self.email

    def get_short_name(self):
        return self.email

    def __unicode__(self):
        return self.get_full_name()

    def get_avatar(self):
        return '%02d.png' % self.avatar_num

    def get_user_domain_data(self):
        liked_threads = list(
            self.liked_threads.all().values_list('id', flat=True)
        )
        disliked_threads = list(
            self.disliked_threads.all().values_list('id', flat=True)
        )
        posted_comments = list(
            Comment.objects.filter(user=self).values_list('id', flat=True)
        )
        liked_comments = list(
            self.liked_comments.all().values_list('id', flat=True)
        )
        disliked_comments = list(
            self.disliked_comments.all().values_list('id', flat=True)
        )

        return {
            'liked_threads': liked_threads,
            'disliked_threads': disliked_threads,
            'posted_comments': posted_comments,
            'liked_comments': liked_comments,
            'disliked_comments': disliked_comments
        }

    def is_site_admin(self, domain_name):
        if self.is_superuser:
            return True
        if self.is_staff and self.site_set.filter(domain=domain_name):
            return True
        return False

    def get_sites(self):
        if self.is_superuser:
            return Site.objects.all()
        return self.site_set.all()

    def get_threads(self, thread_id=None):
        q = Q()
        if not self.is_superuser:
            q = q & Q(site__in=self.get_sites())
        if thread_id:
            q = q & Q(id=thread_id)
        threads = Thread.objects.filter(q)
        return threads

    def get_comments(self, comment_id=None):
        q = Q()
        if not self.is_superuser:
            q = q & Q(thread__site__in=self.get_sites())
        if comment_id:
            q = q & Q(id=comment_id)
        comments = Comment.objects.filter(q)
        return comments

    def get_users(self, user_id=None):
        q = Q(is_staff=False)
        if not self.is_superuser:
            q = q & Q(comments__thread__site__in=self.get_sites())
        if user_id:
            q = q & Q(id=user_id)
        users = CustomUser.objects.filter(q).distinct()
        return users

    def hide(self, site):
        """
        Sets hidden flag to True. Only non staff users can be hidden using
        this method. Hiding the user disables login and therefore posting
        any comments.
        """
        if self.is_staff:
            return
        self.hidden.add(site)
        self.save()

    def unhide(self, site):
        """
        Sets hidden flag to False. Unhiding user enables login and posting
        comments.
        """
        self.hidden.remove(site)
        self.save()

    def delete(self):
        """
        Deletes user comments from database. Only non-staff comments can be
        """
        if self.is_staff:
            return
        super(CustomUser, self).delete()


class Site(models.Model):
    domain = models.CharField(null=False, max_length=255)
    admins = models.ManyToManyField(
        CustomUser, blank=True, limit_choices_to={
            'is_superuser': False,
            'is_staff': True
        })
    anonymous_allowed = models.BooleanField(default=False)
    rs_customer_id = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.domain


class Thread(models.Model):
    class Meta:
        unique_together = (('site', 'url'),)

    site = models.ForeignKey(Site, related_name='threads')
    url = models.CharField(null=False, max_length=255)
    created = models.DateTimeField(editable=False, default=timezone.now)
    allow_comments = models.BooleanField(default=True)
    liked_by_count = models.IntegerField(default=0)
    disliked_by_count = models.IntegerField(default=0)
    liked_by = models.ManyToManyField(
        CustomUser,
        related_name='liked_threads',
        blank=True
    )
    disliked_by = models.ManyToManyField(
        CustomUser,
        related_name='disliked_threads',
        blank=True
    )
    titles = JSONField(default={
        'selector_title': "",
        'page_title': "",
        'h1_title': ""
    })

    def like(self, user):
        if user.is_anonymous():
            self.liked_by_count += 1
        else:
            self.liked_by.add(user)

        self.save()

    def undo_like(self, user):
        if self.likes_count < 1:
            return
        if user.is_anonymous():
            self.liked_by_count -= 1
        else:
            self.liked_by.remove(user)

        self.save()

    def dislike(self, user):
        if user.is_anonymous():
            self.disliked_by_count += 1
        else:
            self.disliked_by.add(user)

        self.save()

    def undo_dislike(self, user):
        if self.dislikes_count < 1:
            return
        if user.is_anonymous():
            self.disliked_by_count -= 1
        else:
            self.disliked_by.remove(user)

        self.save()

    @property
    def likes_count(self):
        count = self.liked_by_count

        if self.liked_by:
            count += self.liked_by.count()

        return count

    @property
    def dislikes_count(self):
        count = self.disliked_by_count

        if self.disliked_by:
            count += self.disliked_by.count()

        return count

    @property
    def title(self):
        if self.titles['selector_title']:
            return self.titles['selector_title']
        elif self.titles['page_title']:
            return self.titles['page_title']
        elif self.titles['h1_title']:
            return self.titles['h1_title']
        else:
            return self.url

    @property
    def full_url(self):
        return urljoin("%s%s" % ('http://', self.site.domain), self.url)


class CommentManager(models.Manager):

    def bulk_delete(self, comments, *args, **kwargs):
        self.filter(id__in=comments, *args, **kwargs).delete()


class Comment(models.Model):
    class Meta:
        ordering = ["created"]

    user = models.ForeignKey(CustomUser, related_name='comments', null=True)
    poster_name = models.CharField(max_length=100)
    thread = models.ForeignKey(Thread, related_name='comments')
    text = models.TextField()
    created = models.DateTimeField(editable=False, default=timezone.now)
    liked_by_count = models.IntegerField(default=0)
    disliked_by_count = models.IntegerField(default=0)
    liked_by = models.ManyToManyField(
        CustomUser,
        related_name='liked_comments',
        blank=True
    )
    disliked_by = models.ManyToManyField(
        CustomUser,
        related_name='disliked_comments',
        blank=True
    )

    avatar_num = models.IntegerField(default=6)  # green diamond
    hidden = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True)

    objects = CommentManager()

    def get_avatar(self):
        if self.user is not None:
            return "%02d" % self.user.avatar_num
        else:
            return "%02d" % self.avatar_num

    def like(self, user):
        if user.is_anonymous():
            self.liked_by_count += 1
        else:
            self.liked_by.add(user)

        self.save()

    def undo_like(self, user):
        if self.likes_count < 1:
            return

        if user.is_anonymous():
            self.liked_by_count -= 1
        else:
            self.liked_by.remove(user)

        self.save()

    def dislike(self, user):
        if user.is_anonymous():
            self.disliked_by_count += 1
        else:
            self.disliked_by.add(user)

        self.save()

    def undo_dislike(self, user):
        if self.dislikes_count < 1:
            return

        if user.is_anonymous():
            self.disliked_by_count -= 1
        else:
            self.disliked_by.remove(user)

        self.save()

    @property
    def likes_count(self):
        count = self.liked_by_count

        if self.liked_by:
            count += self.liked_by.count()

        return count

    @property
    def dislikes_count(self):
        count = self.disliked_by_count

        if self.disliked_by:
            count += self.disliked_by.count()

        return count

    def hide(self):
        self.hidden = True
        self.save()

    def unhide(self):
        self.hidden = False
        self.save()

    def delete(self, user):
        """
        Deletes comment if user is staff/admin or admin for site.
        """
        if user.is_staff:
            super(Comment, self).delete()
