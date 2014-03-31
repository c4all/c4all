from django.db import IntegrityError
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser

from base import BaseTestCase

from comments.models import Thread, CustomUser, Site


class ThreadTestCase(BaseTestCase):

    def setUp(self):
        self.site = Site.objects.create()

    def test_create_thread_fails_without_site(self):
        with self.assertRaises(IntegrityError):
            Thread.objects.create()

    def test_create_thread_succeds(self):
        Thread.objects.create(site=self.site)

        threads = Thread.objects.all()
        self.assertEqual(threads.count(), 1)
        thread = threads[0]
        self.assertEqual(thread.site, self.site)

    def test_likes_count_property(self):
        thread = Thread.objects.create(site=self.site)
        thread.liked_by_count += 1
        thread.save()

        self.assertEqual(thread.likes_count, 1)

        user = CustomUser.objects.create_user(email="a@b.com", password="pass")
        thread.liked_by.add(user)

        self.assertEqual(thread.likes_count, 2)

    def test_dislikes_count_property(self):
        thread = Thread.objects.create(site=self.site)
        thread.disliked_by_count += 1
        thread.save()

        self.assertEqual(thread.dislikes_count, 1)

        user = CustomUser.objects.create_user(email="a@b.com", password="pass")
        thread.disliked_by.add(user)

        self.assertEqual(thread.dislikes_count, 2)

    def test_like(self):
        thread = Thread.objects.create(site=self.site)

        user = CustomUser.objects.create_user(email="a@b.com", password="pass")
        thread.like(user)
        self.assertEqual(thread.likes_count, 1)

        anon = AnonymousUser()
        thread.like(anon)
        self.assertEqual(thread.likes_count, 2)

    def test_undo_like(self):
        thread = Thread.objects.create(site=self.site)

        user = CustomUser.objects.create_user(email="a@b.com", password="pass")
        thread.like(user)
        self.assertEqual(thread.likes_count, 1)

        thread.undo_like(user)
        self.assertEqual(thread.likes_count, 0)

    def test_dislike(self):
        thread = Thread.objects.create(site=self.site)

        user = CustomUser.objects.create_user(email="a@b.com", password="pass")
        thread.dislike(user)
        self.assertEqual(thread.dislikes_count, 1)

        anon = AnonymousUser()
        thread.dislike(anon)
        self.assertEqual(thread.dislikes_count, 2)

    def test_undo_dislike(self):
        thread = Thread.objects.create(site=self.site)

        user = CustomUser.objects.create_user(email="a@b.com", password="pass")
        thread.dislike(user)
        self.assertEqual(thread.dislikes_count, 1)

        thread.undo_dislike(user)
        self.assertEqual(thread.dislikes_count, 0)

    def test_undo_dislike_doesnt_fail_if_user_didnt_dislike_before(self):
        thread = Thread.objects.create(site=self.site)

        user = CustomUser.objects.create_user(email="a@b.com", password="pass")
        user2 = CustomUser.objects.create_user(
            email="a@c.com",
            password="pass"
        )
        thread.dislike(user)
        self.assertEqual(thread.dislikes_count, 1)

        thread.undo_dislike(user2)
        self.assertEqual(thread.dislikes_count, 1)

    def test_anon_user_undo_like_succeeds(self):
        thread = Thread.objects.create(site=self.site)

        anon = AnonymousUser()
        thread.like(anon)
        self.assertEqual(thread.likes_count, 1)

        thread.undo_like(anon)
        self.assertEqual(thread.likes_count, 0)

    def test_anon_user_undo_dislike_succeeds(self):
        thread = Thread.objects.create(site=self.site)

        anon = AnonymousUser()
        thread.dislike(anon)
        self.assertEqual(thread.dislikes_count, 1)

        thread.undo_dislike(anon)
        self.assertEqual(thread.dislikes_count, 0)

    def test_title_property_returns_in_correct_order(self):
        titles = {
            'h1_title': 'h1_title',
            'selector_title': 'selector_title',
            'page_title': 'page_title',
        }
        thread = Thread.objects.create(
            site=self.site,
            titles=titles,
            url='donald/duck'
        )
        self.assertEqual(thread.title, titles['selector_title'])

        titles = {
            'h1_title': 'h1_title',
            'selector_title': '',
            'page_title': 'page_title',
        }
        thread.titles = titles
        thread.save()
        self.assertEqual(thread.title, titles['page_title'])

        titles = {
            'h1_title': 'h1_title',
            'selector_title': '',
            'page_title': '',
        }
        thread.titles = titles
        thread.save()
        self.assertEqual(thread.title, titles['h1_title'])

        titles = {
            'h1_title': '',
            'selector_title': '',
            'page_title': '',
        }
        thread.titles = titles
        thread.save()
        self.assertEqual(thread.title, "donald/duck")


class LikeThreadEndpointTestCase(BaseTestCase):

    def setUp(self):
        self.test_site = Site.objects.create(
            domain='testdomain.com',
        )
        self.test_thread = Thread.objects.create(
            site=self.test_site,
            url='test_url'
        )
        self.test_user = CustomUser.objects.create_user(
            email="a@b.com",
            password="pass"
        )

    def test_like_thread_succeeds(self):
        self.assertEqual(self.test_thread.likes_count, 0)

        r = self.client.post(
            reverse('comments:like_thread', kwargs={'thread_id': self.test_thread.id})
        )

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.likes_count, 1)

    def test_like_thread_succeeds_logged_in_user(self):
        self.client.login(email='a@b.com', password='pass')

        r = self.client.post(
            reverse('comments:like_thread', kwargs={'thread_id': self.test_thread.id})
        )

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.likes_count, 1)

    def test_like_thread_with_nonexisting_id_fails(self):
        r = self.client.post(
            reverse('comments:like_thread', kwargs={'thread_id': 9999})
        )

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 404)

    def test_like_thread_twice_does_not_undo_like(self):
        self.assertEqual(self.test_thread.likes_count, 0)

        self.client.post(
            reverse('comments:like_thread', kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.likes_count, 1)

        self.client.post(
            reverse('comments:like_thread', kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.likes_count, 1)

    def test_like_thread_twice_does_not_undo_like_logged_in_user(self):
        self.client.login(email='a@b.com', password='pass')

        self.client.post(reverse(
            'comments:like_thread',
            kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.likes_count, 1)

        self.client.post(
            reverse('comments:like_thread', kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.likes_count, 1)

    def test_like_disliked_thread_undoes_dislike_increments_thread_likes(self):
        self.client.post(reverse(
            'comments:dislike_thread',
            kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.dislikes_count, 1)

        self.client.post(
            reverse('comments:like_thread', kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.dislikes_count, 0)
        self.assertEqual(thread.likes_count, 1)

    def test_like_disliked_thread_undoes_dislike_increments_thread_likes_logged_in_user(self):
        self.client.login(email='a@b.com', password='pass')

        self.client.post(reverse(
            'comments:dislike_thread',
            kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.dislikes_count, 1)

        self.client.post(
            reverse('comments:like_thread', kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.dislikes_count, 0)
        self.assertEqual(thread.likes_count, 1)

    def test_like_thread_returns_iframe_id_if_provided(self):
        iframeId = 'some_donald_duck_id_123'

        r = self.client.post(
            reverse('comments:like_thread', kwargs={'thread_id': self.test_thread.id}),
            data={ "iframeId": iframeId }
        )

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        self.assertTrue('iframeId' in data)
        self.assertEqual(data['iframeId'], iframeId)


class DislikeThreadEndpointTestCase(BaseTestCase):

    def setUp(self):
        self.test_site = Site.objects.create(
            domain='testdomain.com',
        )
        self.test_thread = Thread.objects.create(
            site=self.test_site,
            url='test_url'
        )
        self.test_user = CustomUser.objects.create_user(
            email="a@b.com",
            password="pass"
        )

    def test_dislike_thread_succeeds(self):
        self.assertEqual(self.test_thread.dislikes_count, 0)

        r = self.client.post(reverse(
            'comments:dislike_thread',
            kwargs={'thread_id': self.test_thread.id}
        ))

        self.assertEqual(r.status_code, 200)
        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.disliked_by_count, 1)

    def test_like_thread_succeeds_logged_in_user(self):
        self.client.login(email='a@b.com', password='pass')

        r = self.client.post(reverse(
            'comments:dislike_thread',
            kwargs={'thread_id': self.test_thread.id})
        )

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.dislikes_count, 1)

    def test_dislike_thread_with_nonexisting_id_fails(self):
        r = self.client.post(reverse(
            'comments:dislike_thread',
            kwargs={'thread_id': 9999}
        ))

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 404)

    def test_dislike_thread_twice_does_not_undo_dislike(self):
        self.assertEqual(self.test_thread.likes_count, 0)

        self.client.post(
            reverse(
                'comments:dislike_thread',
                kwargs={'thread_id': self.test_thread.id}
            )
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.dislikes_count, 1)

        self.client.post(reverse(
            'comments:dislike_thread',
            kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.dislikes_count, 1)

    def test_dislike_thread_twice_does_not_undo_dislike_logged_in_user(self):
        self.client.login(email='a@b.com', password='pass')

        self.client.post(reverse(
            'comments:dislike_thread',
            kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.dislikes_count, 1)

        self.client.post(reverse(
            'comments:dislike_thread',
            kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.dislikes_count, 1)

    def test_dislike_liked_thread_undoes_like_increments_thread_dislikes(self):
        self.client.post(reverse(
            'comments:like_thread',
            kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.likes_count, 1)

        self.client.post(reverse(
            'comments:dislike_thread',
            kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.likes_count, 0)
        self.assertEqual(thread.dislikes_count, 1)

    def test_dislike_liked_thread_undoes_like_increments_thread_dislikes_logged_in_user(self):
        self.client.login(email='a@b.com', password='pass')

        self.client.post(reverse(
            'comments:like_thread',
            kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.likes_count, 1)

        self.client.post(reverse(
            'comments:dislike_thread',
            kwargs={'thread_id': self.test_thread.id})
        )

        thread = Thread.objects.get(id=self.test_thread.id)
        self.assertEqual(thread.likes_count, 0)
        self.assertEqual(thread.dislikes_count, 1)

    def test_dislike_thread_returns_iframe_id_if_provided(self):
        iframeId = 'some_donald_duck_id_123'

        r = self.client.post(
            reverse('comments:dislike_thread', kwargs={'thread_id': self.test_thread.id}),
            data={ "iframeId": iframeId }
        )

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        self.assertTrue('iframeId' in data)
        self.assertEqual(data['iframeId'], iframeId)


class GetThreadInfoTestCase(BaseTestCase):

    def setUp(self):
        self.test_site = Site.objects.create(
            domain='testdomain.com',
        )
        self.test_thread = Thread.objects.create(
            site=self.test_site,
            url='test_url'
        )

    def test_get_thread_info_thread_exists_returns_thread_id(self):
        r = self.client.get(
            reverse('comments:thread_info'),
            data={
                "domain": self.test_site.domain,
                "thread": self.test_thread.url,
            }
        )

        self.assertEqual(r.status_code, 200)

    def test_get_thread_info_thread_does_not_exist_returns_thread_id(self):
        r = self.client.get(
            reverse('comments:thread_info'),
            data={
                "domain": self.test_site.domain,
                "thread": "donald/duck",
            }
        )

        self.assertEqual(r.status_code, 200)

    def test_get_thread_info_if_site_not_registered_fails(self):
        r = self.client.get(
            reverse('comments:thread_info'),
            data={
                "domain": "unregistereddomain.com",
                "thread": "donald/duck",
            }
        )

        self.assertEqual(r.status_code, 400)
