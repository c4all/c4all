from django.db import IntegrityError
from django.test import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist

from base import BaseTestCase

import json

from comments.models import Comment, CustomUser, Site, Thread


class CommentManagerTestCase(BaseTestCase):
    def setUp(self):
        self.user = CustomUser.objects.create(email="a@b.com", password="pass")
        self.site = Site.objects.create()
        self.thread = Thread.objects.create(site=self.site)


    def test_bulk_delete_successfully_deletes_comments(self):
        Comment.objects.bulk_create([
            Comment(user=self.user, thread=self.thread),
            Comment(user=self.user, thread=self.thread),
        ])

        comments = Comment.objects.all()
        Comment.objects.bulk_delete(comments)

        self.assertEqual(Comment.objects.count(), 0)


class CommentTestCase(BaseTestCase):

    def setUp(self):
        # create users
        self.user_foo = CustomUser.objects.create()

        # create site
        self.site = Site.objects.create()

        # create threads
        self.thread = Thread.objects.create(site=self.site)

    def test_create_comment_without_thread_fails(self):
        with self.assertRaises(IntegrityError):
            Comment.objects.create(user=self.user_foo)

    def test_create_comment(self):
        Comment.objects.create(
            user=self.user_foo,
            thread=self.thread,
        )

        comments = Comment.objects.all()

        self.assertEqual(comments.count(), 1)
        comment = comments[0]
        self.assertEqual(comment.user, self.user_foo)
        self.assertEqual(comment.thread, self.thread)

    def test_likes_count_property(self):
        comment = Comment.objects.create(thread=self.thread)
        comment.liked_by_count += 1
        comment.save()

        self.assertEqual(comment.likes_count, 1)

        user = CustomUser.objects.create_user(email="a@b.com", password="pass")
        comment.liked_by.add(user)

        self.assertEqual(comment.likes_count, 2)

    def test_dislikes_count_property(self):
        comment = Comment.objects.create(thread=self.thread)
        comment.disliked_by_count += 1
        comment.save()

        self.assertEqual(comment.dislikes_count, 1)

        user = CustomUser.objects.create_user(email="a@b.com", password="pass")
        comment.disliked_by.add(user)

        self.assertEqual(comment.dislikes_count, 2)

    def test_like(self):
        comment = Comment.objects.create(thread=self.thread)

        user = CustomUser.objects.create_user(email="a@b.com", password="pass")
        comment.like(user)
        self.assertEqual(comment.likes_count, 1)

        anon = AnonymousUser()
        comment.like(anon)
        self.assertEqual(comment.likes_count, 2)

    def test_undo_like(self):
        comment = Comment.objects.create(thread=self.thread)

        user = CustomUser.objects.create_user(email="a@b.com", password="pass")
        comment.like(user)
        self.assertEqual(comment.likes_count, 1)

        comment.undo_like(user)
        self.assertEqual(comment.likes_count, 0)

    def test_dislike(self):
        comment = Comment.objects.create(thread=self.thread)

        user = CustomUser.objects.create_user(email="a@b.com", password="pass")
        comment.dislike(user)
        self.assertEqual(comment.dislikes_count, 1)

        anon = AnonymousUser()
        comment.dislike(anon)
        self.assertEqual(comment.dislikes_count, 2)

    def test_undo_dislike(self):
        comment = Comment.objects.create(thread=self.thread)

        user = CustomUser.objects.create_user(email="a@b.com", password="pass")
        comment.dislike(user)
        self.assertEqual(comment.dislikes_count, 1)

        comment.undo_dislike(user)
        self.assertEqual(comment.dislikes_count, 0)

    def test_anon_user_undo_like_succeeds(self):
        comment = Comment.objects.create(thread=self.thread)

        anon = AnonymousUser()
        comment.like(anon)
        self.assertEqual(comment.likes_count, 1)

        comment.undo_like(anon)
        self.assertEqual(comment.likes_count, 0)

    def test_anon_user_undo_dislike_succeeds(self):
        comment = Comment.objects.create(thread=self.thread)

        anon = AnonymousUser()
        comment.dislike(anon)
        self.assertEqual(comment.dislikes_count, 1)

        comment.undo_dislike(anon)
        self.assertEqual(comment.dislikes_count, 0)

    def test_non_staff_user_cannot_delete_comment_from_db(self):
        comment = Comment.objects.create(thread=self.thread)

        user = CustomUser.objects.create_user(email="a@b.com", password="pass")
        comment.delete(user)

        comments = Comment.objects.all()
        self.assertEqual(comments.count(), 1)
        c = comments[0]
        self.assertEqual(c.id, comment.id)

    def test_admin_user_deletes_comment_successfully(self):
        comment = Comment.objects.create(thread=self.thread)

        user = CustomUser.objects.create_superuser(
            email="a@b.com",
            password="pass"
        )
        comment.delete(user)

        comments = Comment.objects.all()
        self.assertEqual(comments.count(), 0)

        with self.assertRaises(ObjectDoesNotExist):
            Comment.objects.get(id=comment.id)


class PostCommentEndpointTestCase(BaseTestCase):

    def setUp(self):
        self.email = "a@b.com"
        password = "pass"
        self.test_user = CustomUser.objects.create_user(self.email, password)
        self.test_user.full_name = 'test name'
        self.test_user.save()

        self.test_site = Site.objects.create(
            domain='testdomain.com',
            anonymous_allowed=True,
        )
        self.test_thread = Thread.objects.create(
            site=self.test_site,
            url='test_url'
        )

        self.client = Client()
        self.endpoint_url = reverse('comments:comment')

    def test_post_comment_user_logged_in_succeeds(self):
        text = 'some_text'

        self.client.login(email=self.email, password='pass')

        r = self.client.post(self.endpoint_url, data={
            'text': text,
            'thread': self.test_thread.id,
            'domain': self.test_thread.site.domain,
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.all()[0]
        self.assertEqual(comment.poster_name, self.test_user.full_name)
        self.assertEqual(comment.text, text)

    def test_post_comment_anonymous_user_succeeds(self):
        text = 'some_text'
        name = 'Donald Duck'

        r = self.client.post(self.endpoint_url, data={
            'poster_name': name,
            'text': text,
            'thread': self.test_thread.id,
            'domain': self.test_thread.site.domain,
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.all()[0]
        self.assertEqual(comment.poster_name, name)
        self.assertEqual(comment.text, text)

    def test_post_comment_user_ip_address_is_correct(self):
        text = 'some_text'
        name = 'Donald Duck'
        ip = "200.100.102.100"

        r = self.client.post(self.endpoint_url, data={
            'poster_name': name,
            'text': text,
            'thread': self.test_thread.id,
            'domain': self.test_thread.site.domain,
            'ip_address': ip
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.all()[0]
        self.assertEqual(comment.ip_address, ip)

    def test_post_comment_without_name_fails(self):
        r = self.client.post(self.endpoint_url, data={
            'text': 'some text',
            'thread': self.test_thread.id,
            'domain': self.test_thread.site.domain,
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']
        self.assertEqual(status_code, 400)

    def test_post_comment_without_text_fails(self):
        r = self.client.post(self.endpoint_url, data={
            'poster_name': 'Donald Duck',
            'thread': self.test_thread.id,
            'domain': self.test_thread.site.domain,
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']
        self.assertEqual(status_code, 400)

    def test_post_comment_without_thread_fails(self):
        r = self.client.post(self.endpoint_url, data={
            'poster_name': 'Donald Duck',
            'text': 'some text',
            'domain': self.test_thread.site.domain,
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']
        self.assertEqual(status_code, 400)

    def test_post_comment_without_site_fails(self):
        r = self.client.post(self.endpoint_url, data={
            'poster_name': 'Donald Duck',
            'text': 'some text',
            'thread': self.test_thread.id,
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']
        self.assertEqual(status_code, 400)

    def test_post_comment_with_unknown_thread_fails(self):
        r = self.client.post(self.endpoint_url, data={
            'poster_name': 'Donald Duck',
            'text': 'some text',
            'thread': 9999,
            'domain': self.test_thread.site.domain,
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']
        self.assertEqual(status_code, 400)

    def test_post_comment_with_unknown_site_fails(self):
        r = self.client.post(self.endpoint_url, data={
            'poster_name': 'Donald Duck',
            'text': 'some text',
            'thread': self.test_thread.id,
            'domain': 'donald_ducks_site.com',
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']
        self.assertEqual(status_code, 400)

    def test_post_comment_returns_iframe_id_if_provided(self):
        text = 'some_text'
        name = 'Donald Duck'
        iframeId = 'some_donald_duck_id_123'

        r = self.client.post(self.endpoint_url, data={
            'poster_name': name,
            'text': text,
            'thread': self.test_thread.id,
            'domain': self.test_thread.site.domain,
            'iframeId': iframeId,
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        self.assertTrue('iframeId' in data)
        self.assertEqual(data['iframeId'], iframeId)


class GetCommentsCountTestCase(BaseTestCase):
    def setUp(self):
        self.test_site = Site.objects.create(
            domain='example.com',
        )
        self.test_thread = Thread.objects.create(
            site=self.test_site,
            url='test_url'
        )
        self.test_comment_1 = Comment.objects.create(
            poster_name='Precise Pangolin',
            thread=self.test_thread,
            text='Pangolins are always precise!'
        )

        self.test_comment_2 = Comment.objects.create(
            poster_name='Curious Benjamin',
            thread=self.test_thread,
            text='Growing in reverse!'
        )

        self.test_comment_3 = Comment.objects.create(
            poster_name='Slow Loris',
            thread=self.test_thread,
            text='Real life Slowpoke!',
            hidden=True
        )

        self.endpoint_url = reverse('comments:comment_count')

    def test_comment_count_returns_correct_count(self):
        r = self.client.get(self.endpoint_url, data={
            'thread_url': self.test_thread.url,
            'domain': self.test_thread.site.domain,
        })

        self.assertEqual(r.status_code, 200)

        resp = json.loads(r.content)
        self.assertEqual(2, resp['comment_count'])

class GetCommentsEndpointTestCase(BaseTestCase):

    def setUp(self):
        self.test_site = Site.objects.create(
            domain='testdomain.com',
        )
        self.test_thread = Thread.objects.create(
            site=self.test_site,
            url='test_url'
        )
        self.test_comment_1 = Comment.objects.create(
            poster_name='Donald Duck',
            thread=self.test_thread,
            text='test text 1'
        )

        self.test_comment_2 = Comment.objects.create(
            poster_name='Donald Duck',
            thread=self.test_thread,
            text='test text 2'
        )

        self.endpoint_url = reverse('comments:get_comments')

    def test_get_comments_successfully_returns_comments(self):
        r = self.client.get(self.endpoint_url, data={
            'thread': self.test_thread.id,
            'domain': self.test_thread.site.domain,
        })

        self.assertEqual(r.status_code, 200)
        resp = json.loads(r.content)
        self.assertTrue('html' in resp)
        html = resp['html']
        # don't know how to check html (or if it has any sense to check it), so
        # just checking that response html contains smth
        self.assertNotEqual(html, "")
        self.assertTrue('html_container_name' in resp)
        html_container_name = resp['html_container_name']
        self.assertEqual(html_container_name, 'comments_container')

    def test_get_comments_thread_not_provided_fails(self):
        r = self.client.get(self.endpoint_url, data={
            'domain': self.test_thread.site.domain,
        })

        self.assertEqual(r.status_code, 400)

    def test_get_comments_domain_not_provided_fails(self):
        r = self.client.get(self.endpoint_url, data={
            'thread': self.test_thread.url,
        })

        self.assertEqual(r.status_code, 400)

    def test_get_comments_domain_doesnt_exist_fails(self):
        r = self.client.get(self.endpoint_url, data={
            'thread': self.test_thread.url,
            'domain': 'donald_ducks_site.com',
        })

        self.assertEqual(r.status_code, 400)


class LikeCommentEndpointTestCase(BaseTestCase):

    def setUp(self):
        self.email = "a@b.com"
        password = "pass"
        self.test_user = CustomUser.objects.create_user(self.email, password)
        self.test_user.full_name = 'test name'
        self.test_user.save()

        self.test_site = Site.objects.create(
            domain='testdomain.com',
            anonymous_allowed=True,
        )
        self.test_thread = Thread.objects.create(
            site=self.test_site,
            url='test_url'
        )

        self.test_comment = Comment.objects.create(
            poster_name='Donald Duck',
            thread=self.test_thread,
            text='quack!',
        )

    def test_like_comment_suceeds(self):
        r = self.client.post(reverse(
            'comments:like_comment',
            kwargs={'comment_id': self.test_comment.id}
        ), data={'domain': self.test_site.domain})

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.liked_by_count, 1)

    def test_like_nonexisting_comment_fails(self):
        r = self.client.post(reverse(
            'comments:like_comment',
            kwargs={'comment_id': 9999}
        ), data={'domain': self.test_site.domain})

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 404)
        comments = Comment.objects.filter(liked_by_count__gt=0)
        self.assertEqual(comments.count(), 0)

    def test_like_comment_twice_does_not_undo_like(self):
        self.assertEqual(self.test_comment.likes_count, 0)

        self.client.post(reverse(
            'comments:like_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={'domain': self.test_site.domain}
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.likes_count, 1)

        self.client.post(reverse(
            'comments:like_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={'domain': self.test_site.domain}
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.likes_count, 1)

    def test_like_comment_twice_does_not_undo_like_logged_in_user(self):
        self.client.login(email='a@b.com', password='pass')

        self.client.post(reverse(
            'comments:like_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={'domain': self.test_site.domain}
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.likes_count, 1)

        self.client.post(reverse(
            'comments:like_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={'domain': self.test_site.domain}
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.likes_count, 1)

    def test_like_disliked_comment_undoes_dislike_and_incerements_comment_likes(self):
        self.client.post(reverse(
            'comments:dislike_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={'domain': self.test_site.domain}
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.dislikes_count, 1)

        self.client.post(reverse(
            'comments:like_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={'domain': self.test_site.domain}
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.dislikes_count, 0)
        self.assertEqual(comment.likes_count, 1)

    def test_like_disliked_comment_undoes_dislike_and_incerements_comment_likes_logged_in_user(self):
        self.client.login(email='a@b.com', password='pass')

        self.client.post(reverse(
            'comments:dislike_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={
                'domain': self.test_site.domain
            }
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.dislikes_count, 1)

        self.client.post(reverse(
            'comments:like_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={
                'domain': self.test_site.domain
            }
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.dislikes_count, 0)
        self.assertEqual(comment.likes_count, 1)

    def test_like_comment_returns_iframe_id_if_provided(self):
        iframeId = 'some_donald_duck_id_123'
        r = self.client.post(reverse(
            'comments:like_comment',
            kwargs={'comment_id': self.test_comment.id}
        ),
            data={
                "iframeId": iframeId,
                'domain': self.test_site.domain
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        self.assertTrue('iframeId' in data)
        self.assertEqual(data['iframeId'], iframeId)


class DislikeCommentEndpointTestCase(BaseTestCase):

    def setUp(self):
        self.email = "a@b.com"
        password = "pass"
        self.test_user = CustomUser.objects.create_user(self.email, password)
        self.test_user.full_name = 'test name'
        self.test_user.save()

        self.test_site = Site.objects.create(
            domain='testdomain.com',
            anonymous_allowed=True,
        )
        self.test_thread = Thread.objects.create(
            site=self.test_site,
            url='test_url'
        )

        self.test_comment = Comment.objects.create(
            poster_name='Donald Duck',
            thread=self.test_thread,
            text='quack!',
        )

        self.client = Client()

    def test_dislike_comment_suceeds(self):
        r = self.client.post(reverse(
            'comments:dislike_comment',
            kwargs={'comment_id': self.test_comment.id}
        ), data={'domain': self.test_site.domain})

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.disliked_by_count, 1)

    def test_dislike_nonexisting_comment_fails(self):
        r = self.client.post(reverse(
            'comments:dislike_comment',
            kwargs={'comment_id': 9999}
        ), data={'domain': self.test_site.domain})

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 404)
        comments = Comment.objects.filter(disliked_by_count__gt=0)
        self.assertEqual(comments.count(), 0)

    def test_dislike_comment_twice_does_not_undo_dislike(self):
        self.assertEqual(self.test_comment.likes_count, 0)

        self.client.post(reverse(
            'comments:dislike_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={'domain': self.test_site.domain}
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.dislikes_count, 1)

        self.client.post(reverse(
            'comments:dislike_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={'domain': self.test_site.domain}
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.dislikes_count, 1)

    def test_dislike_comment_twice_does_not_undo_dislike_logged_in_user(self):
        self.client.login(email='a@b.com', password='pass')

        self.client.post(reverse(
            'comments:dislike_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={'domain': self.test_site.domain}
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.dislikes_count, 1)

        self.client.post(reverse(
            'comments:dislike_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={'domain': self.test_site.domain}
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.dislikes_count, 1)

    def test_dislike_liked_comment_undoes_like_and_incerements_comment_dislikes(self):
        self.client.post(reverse(
            'comments:like_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={'domain': self.test_site.domain}
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.likes_count, 1)

        self.client.post(reverse(
            'comments:dislike_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={'domain': self.test_site.domain}
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.likes_count, 0)
        self.assertEqual(comment.dislikes_count, 1)

    def test_dislike_liked_comment_undoes_like_and_incerements_comment_dislikes_logged_in_user(self):
        self.client.login(email='a@b.com', password='pass')

        self.client.post(reverse(
            'comments:like_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={'domain': self.test_site.domain}
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.likes_count, 1)

        self.client.post(reverse(
            'comments:dislike_comment',
            kwargs={'comment_id': self.test_comment.id}),
            data={'domain': self.test_site.domain}
        )

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertEqual(comment.likes_count, 0)
        self.assertEqual(comment.dislikes_count, 1)

    def test_dislike_comment_returns_iframe_id_if_provided(self):
        iframeId = 'some_donald_duck_id_123'
        r = self.client.post(reverse(
            'comments:dislike_comment',
            kwargs={'comment_id': self.test_comment.id}
        ),
            data={
                "iframeId": iframeId,
                'domain': self.test_site.domain
            },
        )

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        self.assertTrue('iframeId' in data)
        self.assertEqual(data['iframeId'], iframeId)


class HideCommentEndpointTestCase(BaseTestCase):

    def setUp(self):
        self.email = "a@b.com"
        password = "pass"
        self.test_user = CustomUser.objects.create_user(self.email, password)
        self.test_user.full_name = 'test name'
        self.test_user.save()

        self.test_admin = CustomUser.objects.create_superuser(
            email="admin@b.org",
            password="pass"
        )

        self.test_site = Site.objects.create(
            domain='testdomain.com',
            anonymous_allowed=True,
        )
        self.test_thread = Thread.objects.create(
            site=self.test_site,
            url='test_url'
        )

        self.test_comment = Comment.objects.create(
            poster_name='Donald Duck',
            thread=self.test_thread,
            text='quack!',
        )

    def test_hide_comment_suceeds(self):
        self.client.login(email="admin@b.org", password='pass')

        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertFalse(comment.hidden)

        r = self.client.post(reverse(
            'comments:hide_comment',
            kwargs={'comment_id': self.test_comment.id}
        ))

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertTrue(comment.hidden)

    def test_hide_comment_not_admin_fails(self):
        self.client.login(email="a@b.org", password='pass')

        r = self.client.post(reverse(
            'comments:hide_comment',
            kwargs={'comment_id': self.test_comment.id}
        ))

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 403)

    def test_hide_comment_anon_user_fails(self):
        r = self.client.post(reverse(
            'comments:hide_comment',
            kwargs={'comment_id': self.test_comment.id}
        ))

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 403)

    def test_hide_nonexisting_comment_fails(self):
        self.client.login(email="admin@b.org", password='pass')

        r = self.client.post(reverse(
            'comments:hide_comment',
            kwargs={'comment_id': 9999}
        ))

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 404)

    def test_hide_comment_returns_iframe_id_if_provided(self):
        self.client.login(email="admin@b.org", password='pass')

        iframeId = 'some_donald_duck_id_123'
        r = self.client.post(reverse(
            'comments:hide_comment',
            kwargs={'comment_id': self.test_comment.id}
        ), data={"iframeId": iframeId})

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        self.assertTrue('iframeId' in data)
        self.assertEqual(data['iframeId'], iframeId)


class UnhideCommentEndpointTestCase(BaseTestCase):

    def setUp(self):
        self.email = "a@b.com"
        password = "pass"
        self.test_user = CustomUser.objects.create_user(self.email, password)
        self.test_user.full_name = 'test name'
        self.test_user.save()

        self.test_admin = CustomUser.objects.create_superuser(
            email="admin@b.org",
            password="pass"
        )

        self.test_site = Site.objects.create(
            domain='testdomain.com',
            anonymous_allowed=True,
        )
        self.test_thread = Thread.objects.create(
            site=self.test_site,
            url='test_url'
        )

        self.test_comment = Comment.objects.create(
            poster_name='Donald Duck',
            thread=self.test_thread,
            text='quack!',
        )

    def test_unhide_comment_suceeds(self):
        self.client.login(email="admin@b.org", password='pass')

        comment = Comment.objects.get(id=self.test_comment.id)
        comment.hidden = True
        comment.save()

        r = self.client.post(reverse(
            'comments:unhide_comment',
            kwargs={'comment_id': self.test_comment.id}
        ))

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        comment = Comment.objects.get(id=self.test_comment.id)
        self.assertFalse(comment.hidden)

    def test_unhide_comment_not_admin_fails(self):
        self.client.login(email="a@b.org", password='pass')

        r = self.client.post(reverse(
            'comments:unhide_comment',
            kwargs={'comment_id': self.test_comment.id}
        ))

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 403)

    def test_unhide_comment_anon_user_fails(self):
        r = self.client.post(reverse(
            'comments:unhide_comment',
            kwargs={'comment_id': self.test_comment.id}
        ))

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 403)

    def test_unhide_nonexisting_comment_fails(self):
        self.client.login(email="admin@b.org", password='pass')

        r = self.client.post(reverse(
            'comments:unhide_comment',
            kwargs={'comment_id': 9999}
        ))

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 404)

    def test_unhide_comment_returns_iframe_id_if_provided(self):
        self.client.login(email="admin@b.org", password='pass')

        comment = Comment.objects.get(id=self.test_comment.id)
        comment.hidden = True
        comment.save()

        iframeId = 'some_donald_duck_id_123'
        r = self.client.post(reverse(
            'comments:unhide_comment',
            kwargs={'comment_id': self.test_comment.id}
        ), data={"iframeId": iframeId})

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        self.assertTrue('iframeId' in data)
        self.assertEqual(data['iframeId'], iframeId)
