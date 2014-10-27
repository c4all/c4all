from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils.timezone import now

from comments.models import (Site, Thread, Comment)

from datetime import timedelta, date


User = get_user_model()


class AdminThreadTestCases(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            "donald@duck.com",
            "password"
        )

        self.client = Client()
        self.site = Site.objects.create()

    def test_get_threads_succeeds(self):
        self.client.login(email="donald@duck.com", password="password")

        Thread.objects.create(site=self.site, url='test_url')

        resp = self.client.get(reverse("c4all_admin:get_threads", args=[self.site.id, ]))
        self.assertEqual(resp.status_code, 200)

    def test_get_threads_filter_1_day_success(self):
        time_period = 1

        t1 = Thread.objects.create(site=self.site, url='test_url')
        t2 = Thread.objects.create(
            site=self.site,
            url='test_url_2',
        )
        t2.created = now() - timedelta(days=time_period)
        t2.save()

        self.client.login(email="donald@duck.com", password="password")

        resp = self.client.post(
            reverse("c4all_admin:get_threads", args=[self.site.id, ]),
            {'interval': 'today'}
        )

        threads = resp.context['threads'].object_list

        self.assertTrue(t1 in threads)
        self.assertTrue(t2 not in threads)

    def test_get_threads_filter_1_day_borderline_case(self):
        t1 = Thread.objects.create(site=self.site, url='test_url')
        t1.created = date.today()
        t1.save()

        self.client.login(email="donald@duck.com", password="password")

        resp = self.client.post(
            reverse("c4all_admin:get_threads", args=[self.site.id, ]),
            {'interval': 'today'}
        )

        threads = resp.context['threads'].object_list

        self.assertTrue(t1 in threads)

    def test_get_threads_filter_1_week_success(self):
        time_period = 7

        t1 = Thread.objects.create(site=self.site, url='test_url')
        t2 = Thread.objects.create(
            site=self.site,
            url='test_url_2',
        )
        t2.created = now() - timedelta(days=time_period)
        t2.save()

        self.client.login(email="donald@duck.com", password="password")

        resp = self.client.post(
            reverse("c4all_admin:get_threads", args=[self.site.id, ]),
            {'interval': 'this_week'}
        )

        threads = resp.context['threads'].object_list

        self.assertTrue(t1 in threads)
        self.assertTrue(t2 not in threads)

    def test_get_threads_filter_1_week_borderline_case(self):
        t1 = Thread.objects.create(site=self.site, url='test_url')
        t1.created = date.today() - timedelta(date.today().weekday())
        t1.save()

        self.client.login(email="donald@duck.com", password="password")

        resp = self.client.post(
            reverse("c4all_admin:get_threads", args=[self.site.id, ]),
            {'interval': 'this_week'}
        )

        threads = resp.context['threads'].object_list

        self.assertTrue(t1 in threads)

    def test_get_threads_filter_1_month_success(self):
        time_period = now().day

        t1 = Thread.objects.create(site=self.site, url='test_url')
        t2 = Thread.objects.create(
            site=self.site,
            url='test_url_2',
        )
        t2.created = now() - timedelta(days=time_period)
        t2.save()

        self.client.login(email="donald@duck.com", password="password")

        resp = self.client.post(
            reverse("c4all_admin:get_threads", args=[self.site.id, ]),
            {'interval': 'this_month'}
        )

        threads = resp.context['threads'].object_list

        self.assertTrue(t1 in threads)
        self.assertTrue(t2 not in threads)

    def test_get_threads_filter_1_month_borderline(self):
        t1 = Thread.objects.create(site=self.site, url='test_url')
        t1.created = date.today() - timedelta(date.today().day - 1)
        t1.save()

        self.client.login(email="donald@duck.com", password="password")

        resp = self.client.post(
            reverse("c4all_admin:get_threads", args=[self.site.id, ]),
            {'interval': 'this_month'}
        )

        threads = resp.context['threads'].object_list

        self.assertTrue(t1 in threads)

    def test_get_threads_filter_all_time_success(self):
        time_period = 100

        t1 = Thread.objects.create(site=self.site, url='test_url')
        t2 = Thread.objects.create(
            site=self.site,
            url='test_url_2',
        )
        t2.created = now() - timedelta(weeks=time_period)
        t2.save()

        self.client.login(email="donald@duck.com", password="password")

        resp = self.client.post(
            reverse("c4all_admin:get_threads", args=[self.site.id, ]),
            {'interval': 'all_dates'}
        )

        threads = resp.context['threads'].object_list

        self.assertTrue(t1 in threads)
        self.assertTrue(t2 in threads)

    def test_get_threads_returns_all_threads_if_period_not_provided_post(self):
        t1 = Thread.objects.create(site=self.site, url='test_url')
        t2 = Thread.objects.create(site=self.site, url='test_url_2')
        self.client.login(email="donald@duck.com", password="password")

        resp = self.client.post(reverse("c4all_admin:get_threads", args=[self.site.id, ]))

        threads = resp.context['threads'].object_list

        self.assertTrue(t1 in threads)
        self.assertTrue(t2 in threads)

    def test_get_threads_returns_all_threads_if_period_not_provided_get(self):
        t1 = Thread.objects.create(site=self.site, url='test_url')
        t2 = Thread.objects.create(site=self.site, url='test_url_2')
        self.client.login(email="donald@duck.com", password="password")

        resp = self.client.get(reverse("c4all_admin:get_threads", args=[self.site.id, ]))

        threads = resp.context['threads'].object_list

        self.assertTrue(t1 in threads)
        self.assertTrue(t2 in threads)

    def test_get_threads_site_doesnt_exist_returns_404(self):
        self.client.login(email="donald@duck.com", password="password")

        Thread.objects.create(site=self.site, url='test_url')

        resp = self.client.get(reverse("c4all_admin:get_threads", args=[9999, ]))
        self.assertEqual(resp.status_code, 404)

    def test_get_threads_returns_all_threads_if_no_id_token(self):
        self.client.login(email="donald@duck.com", password="password")

        t = Thread.objects.create(site=self.site, url='test_url')

        resp = self.client.get(reverse("c4all_admin:get_threads"))

        threads = resp.context['threads'].object_list

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(t in threads)

    def test_get_threads_returns_all_threads_by_latest_comment(self):
        self.client.login(email="donald@duck.com", password="password")

        t1 = Thread.objects.create(site=self.site, url='test_url')
        t2 = Thread.objects.create(site=self.site, url='test_url_2')

        Comment.objects.create(thread=t2, user=self.admin)

        resp = self.client.get(reverse("c4all_admin:get_threads"))

        threads = resp.context['threads'].object_list

        self.assertEqual(resp.status_code, 200)
        threads = resp.context['threads'].object_list
        self.assertEqual(len(threads), 2)
        self.assertEqual(threads[0].id, t2.id)
        self.assertEqual(threads[1].id, t1.id)

    def test_get_threads_returns_all_threads_by_thread_date(self):
        self.client.login(email="donald@duck.com", password="password")

        t1 = Thread.objects.create(site=self.site, url='test_url')
        t2 = Thread.objects.create(site=self.site, url='test_url_2')

        Comment.objects.create(thread=t1, user=self.admin)

        resp = self.client.get(reverse("c4all_admin:get_threads"),
            data={"sort_by": "thread_date"}
        )

        threads = resp.context['threads'].object_list

        self.assertEqual(resp.status_code, 200)
        threads = resp.context['threads'].object_list
        self.assertEqual(len(threads), 2)
        self.assertEqual(threads[0].id, t2.id)
        self.assertEqual(threads[1].id, t1.id)

    def test_get_threads_returns_threads_from_site_with_lowest_id_if_site_id_not_provided(self):
        self.site_2 = Site.objects.create()

        t1 = Thread.objects.create(site=self.site, url='test_url')
        t2 = Thread.objects.create(site=self.site_2, url='test_url_2')
        self.client.login(email="donald@duck.com", password="password")

        resp = self.client.get(reverse("c4all_admin:get_threads"))

        threads = resp.context['threads'].object_list

        self.assertTrue(t1 in threads)
        self.assertTrue(t2 not in threads)

    def test_get_filtered_threads_admins_can_access(self):
        self.site_2 = Site.objects.create()
        t1 = Thread.objects.create(site=self.site, url='test_url')
        t2 = Thread.objects.create(site=self.site_2, url='test_url_2')
        self.client.login(email="donald@duck.com", password="password")

        self.admin.is_superuser = False
        self.admin.save()
        self.assertFalse(self.admin.get_threads())

        self.site.admins.add(self.admin)
        num_of_threads = self.admin.get_threads().count()
        self.assertEqual(num_of_threads, 1)
        self.assertEqual(
            self.admin.get_threads()[num_of_threads - 1].id, t1.id)

        self.site_2.admins.add(self.admin)
        self.site.admins.add(self.admin)
        num_of_threads = self.admin.get_threads().count()
        self.assertEqual(num_of_threads, 2)
        self.assertEqual(
            self.admin.get_threads()[num_of_threads - 2].id, t1.id)
        self.assertEqual(
            self.admin.get_threads()[num_of_threads - 1].id, t2.id)

    def test_superuser_can_get_all_threads(self):
        self.site_2 = Site.objects.create()
        t1 = Thread.objects.create(site=self.site, url='test_url')
        t2 = Thread.objects.create(site=self.site_2, url='test_url_2')
        self.client.login(email="donald@duck.com", password="password")

        self.site_2.admins.add(self.admin)
        self.site.admins.add(self.admin)
        num_of_threads = self.admin.get_threads().count()
        self.assertEqual(num_of_threads, 2)
        self.assertEqual(
            self.admin.get_threads()[num_of_threads - 2].id, t1.id)
        self.assertEqual(
            self.admin.get_threads()[num_of_threads - 1].id, t2.id)

    def test_get_filtered_comments_admins_can_access(self):
        self.site_2 = Site.objects.create()
        t1 = Thread.objects.create(site=self.site, url='test_url')
        t2 = Thread.objects.create(site=self.site_2, url='test_url_2')
        c1 = Comment.objects.create(thread=t1, hidden=True)
        c2 = Comment.objects.create(thread=t2, hidden=True)
        c3 = Comment.objects.create(thread=t2, hidden=True)

        self.client.login(email="donald@duck.com", password="password")
        self.admin.is_superuser = False
        self.admin.save()
        self.assertFalse(self.admin.get_comments())

        self.site.admins.add(self.admin)
        num_of_comments = self.admin.get_comments().count()
        self.assertEqual(num_of_comments, 1)
        self.assertEqual(
            self.admin.get_comments()[num_of_comments - 1].id, c1.id)

        self.site_2.admins.add(self.admin)
        num_of_comments = self.admin.get_comments().count()
        self.assertEqual(num_of_comments, 3)
        self.assertEqual(
            self.admin.get_comments()[num_of_comments - 3].id, c1.id)
        self.assertEqual(
            self.admin.get_comments()[num_of_comments - 2].id, c2.id)
        self.assertEqual(
            self.admin.get_comments()[num_of_comments - 1].id, c3.id)

    def test_superuser_can_get_all_comments(self):
        self.site_2 = Site.objects.create()
        t1 = Thread.objects.create(site=self.site, url='test_url')
        t2 = Thread.objects.create(site=self.site_2, url='test_url_2')
        c1 = Comment.objects.create(thread=t1, hidden=True)
        c2 = Comment.objects.create(thread=t2, hidden=True)
        c3 = Comment.objects.create(thread=t2, hidden=True)

        num_of_comments = self.admin.get_comments().count()
        self.assertEqual(num_of_comments, 3)
        self.assertEqual(
            self.admin.get_comments()[num_of_comments - 3].id, c1.id)
        self.assertEqual(
            self.admin.get_comments()[num_of_comments - 2].id, c2.id)
        self.assertEqual(
            self.admin.get_comments()[num_of_comments - 1].id, c3.id)
