from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from comments.models import (Site, Thread, Comment)


User = get_user_model()


class AdminCommentTestCases(TestCase):

    def setUp(self):
        site = Site.objects.create()
        self.thread = Thread.objects.create(site=site)

        self.admin = User.objects.create_superuser(
            "donald@duck.com",
            "password"
        )

        self.client = Client()
        self.client.login(email="donald@duck.com", password="password")

    def test_comment_hide_not_ajax_call_fails(self):
        """
        Tests endpoint's response to non-ajax call. Endpoint should return
        a 400 response.
        """
        c = Comment.objects.create(thread=self.thread)
        r = self.client.post(
            reverse('c4all_admin:hide_comment', args=(c.id, )),
        )
        self.assertEqual(r.status_code, 400)

    def test_comment_hide_succeeds(self):
        c = Comment.objects.create(thread=self.thread)
        r = self.client.post(
            reverse('c4all_admin:hide_comment', args=(c.id, )),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(r.status_code, 200)
        comm = Comment.objects.get(id=c.id)
        self.assertTrue(comm.hidden)

    def test_comment_hide_returns_404_for_nonexisting_comment(self):
        r = self.client.post(
            reverse('c4all_admin:hide_comment', args=(9999, )),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(r.status_code, 404)

    def test_comment_unhide_not_ajax_call_fails(self):
        """
        Tests endpoint's response to non-ajax call. Endpoint should return
        a 400 response.
        """
        c = Comment.objects.create(thread=self.thread)
        r = self.client.post(
            reverse('c4all_admin:unhide_comment', args=(c.id, )),
        )
        self.assertEqual(r.status_code, 400)

    def test_comment_unhide_succeeds(self):
        c = Comment.objects.create(thread=self.thread, hidden=True)
        r = self.client.post(
            reverse('c4all_admin:unhide_comment', args=(c.id, )),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(r.status_code, 200)
        comm = Comment.objects.get(id=c.id)
        self.assertFalse(comm.hidden)

    def test_comment_unhide_returns_404_for_nonexisting_comment(self):
        r = self.client.post(
            reverse('c4all_admin:unhide_comment', args=(9999, )),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(r.status_code, 404)

    def test_delete_comment_successfully_deletes_comment(self):
        c = Comment.objects.create(thread=self.thread, hidden=True)
        r = self.client.get(reverse('c4all_admin:delete_comment', args=(c.id, )))
        self.assertEqual(r.status_code, 302)

        with self.assertRaises(ObjectDoesNotExist):
            Comment.objects.get(id=c.id)

    def test_delete_comment_returns_404_for_nonexisting_comment(self):
        r = self.client.get(reverse('c4all_admin:delete_comment', args=(9999, )))

        self.assertEqual(r.status_code, 404)

    def test_get_comments_returns_all_comments(self):
        c1 = Comment.objects.create(thread=self.thread, text="comment 1 text")
        c2 = Comment.objects.create(
            thread=self.thread,
            hidden=True,
            text="comment 2 text"
        )

        r = self.client.get(
            reverse('c4all_admin:get_thread_comments', args=(self.thread.id, )))

        self.assertEqual(r.status_code, 200)

        comments = r.context['comments'].object_list

        self.assertTrue(c1 in comments)
        self.assertTrue(c2 in comments)

    def test_get_hidden_comments_returns_only_hidden_comments(self):
        c1 = Comment.objects.create(thread=self.thread, text="comment 1 text")
        c2 = Comment.objects.create(
            thread=self.thread,
            hidden=True,
            text="comment 2 text"
        )

        r = self.client.get(
            reverse('c4all_admin:get_thread_comments', args=(self.thread.id, )),
            {"hidden": True}
        )

        comments = r.context['comments'].object_list

        self.assertEqual(r.status_code, 200)
        self.assertFalse(c1 in comments)
        self.assertTrue(c2 in comments)

    def test_comment_bulk_actions_delete_successfully_deletes_comments(self):
        self.client.login(email="donald@duck.com", password="password")

        c1 = Comment.objects.create(thread=self.thread)
        c2 = Comment.objects.create(thread=self.thread)

        resp = self.client.post(
            reverse("c4all_admin:comment_bulk_actions", args=[self.thread.id]),
            {
                "action": ["delete"],
                "choices": [c1.id, c2.id]
            }
        )

        self.assertEqual(resp.status_code, 302)
        comments = Comment.objects.all()
        self.assertEqual(comments.count(), 0)

    def test_comment_bulk_actions_hide_successfully_hides_comments(self):
        self.client.login(email="donald@duck.com", password="password")

        c1 = Comment.objects.create(thread=self.thread)
        c2 = Comment.objects.create(thread=self.thread)

        resp = self.client.post(
            reverse("c4all_admin:comment_bulk_actions", args=[self.thread.id]),
            {
                "action": ["hide"],
                "choices": [c1.id, c2.id]
            }
        )

        self.assertEqual(resp.status_code, 302)
        comments = Comment.objects.filter(hidden=True)
        self.assertEqual(comments.count(), 2)

    def test_comment_bulk_actions_hide_hidden_comment_doesnt_change_status(self):
        self.client.login(email="donald@duck.com", password="password")

        c = Comment.objects.create(thread=self.thread, hidden=True)

        resp = self.client.post(
            reverse("c4all_admin:comment_bulk_actions", args=[self.thread.id]),
            {
                "action": ["hide"],
                "choices": [c.id]
            }
        )

        self.assertEqual(resp.status_code, 302)
        comments = Comment.objects.filter(hidden=True)
        self.assertEqual(comments.count(), 1)
        self.assertTrue(c in comments)
