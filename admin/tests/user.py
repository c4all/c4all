from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse

from datetime import datetime, timedelta

import json

from comments.models import Comment, Site, Thread

User = get_user_model()


class AdminUsertestCases(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            "donald@duck.com",
            "password"
        )

        self.user = User.objects.create_user(
            "scrooge@duck.com",
            "password",
        )

        self.user_hidden = User.objects.create_user(
            "daffy@duck.com",
            "password",
        )

        self.site = Site.objects.create(domain='www.google.com')

        self.user_hidden.hidden.add(self.site)
        self.user_hidden.created = datetime.today() - timedelta(1)
        self.user_hidden.save()

        self.client = Client()
        self.client.login(email="donald@duck.com", password="password")

    def test_get_users_returns_all_users_except_admin(self):
        thread = Thread.objects.create(site=self.site)
        Comment.objects.create(thread=thread, user=self.user)
        Comment.objects.create(thread=thread, user=self.user_hidden)
        Comment.objects.create(thread=thread, user=self.admin)

        resp = self.client.get(reverse("c4all_admin:get_users",
            args=[self.site.id]))

        self.assertEqual(resp.status_code, 200)
        users = resp.context['users'].object_list

        self.assertTrue(self.user in users)
        self.assertTrue(self.user_hidden in users)
        self.assertTrue(self.admin not in users)

    def test_get_hidden_users_returns_hidden_users(self):
        thread = Thread.objects.create(site=self.site)
        Comment.objects.create(thread=thread, user=self.user)
        Comment.objects.create(thread=thread, user=self.user_hidden)

        resp = self.client.get(reverse("c4all_admin:get_users",
            args=[self.site.id]), {"hidden": True})
        self.assertTrue(resp.status_code, 200)

        users = resp.context['users'].object_list

        self.assertTrue(self.user_hidden in users)
        self.assertFalse(self.user in users)

    def test_user_bulk_actions_delete_successfully_deletes_user_comments(self):
        thread = Thread.objects.create(site=self.site)
        Comment.objects.create(thread=thread, user=self.user)
        Comment.objects.create(thread=thread, user=self.user_hidden)
        self.assertEqual(Comment.objects.count(), 2)

        resp = self.client.post(
            reverse("c4all_admin:user_bulk_actions"),
            {
                "site_id": self.site.id,
                "action": ["delete"],
                "choices": [self.user.id, self.user_hidden.id]
            }
        )

        self.assertEqual(resp.status_code, 302)
        users = User.objects.all()
        self.assertEqual(users.count(), 3)
        self.assertFalse(Comment.objects.count())

    def test_user_bulk_actions_delete_successfully_deletes_user_comments_not_admin(self):
        resp = self.client.post(
            reverse("c4all_admin:user_bulk_actions"),
            {
                "site_id": self.site.id,
                "action": ["delete"],
                "choices": [self.user.id, self.admin.id]
            }
        )

        users = User.objects.all()
        self.assertEqual(users.count(), 3)
        thread = Thread.objects.create(site=self.site)
        Comment.objects.create(thread=thread, user=self.user)
        Comment.objects.create(thread=thread, user=self.admin)
        self.assertEqual(resp.status_code, 302)
        users = User.objects.all()
        self.assertEqual(users.count(), 3)
        self.assertEqual(Comment.objects.filter(user=self.admin).count(), 1)

    def test_user_bulk_actions_hide_successfully_hides_users(self):
        users = User.objects.filter(hidden=True)
        self.assertEqual(users.count(), 1)

        resp = self.client.post(
            reverse("c4all_admin:user_bulk_actions"),
            {
                "site_id": self.site.id,
                "action": ["hide"],
                "choices": [self.user.id]
            }
        )

        self.assertEqual(resp.status_code, 302)
        users = User.objects.filter(hidden=True)
        self.assertEqual(users.count(), 2)
        self.assertTrue(self.user in users)

    def test_user_bulk_actions_hide_successfully_hides_user_not_admin(self):
        site2 = Site.objects.create(domain='www.example.com')
        users = Site.objects.get(id=site2.id).hidden_users.all()
        self.assertEqual(users.count(), 0)
        self.assertTrue(self.admin not in users)

        resp = self.client.post(
            reverse("c4all_admin:user_bulk_actions"),
            {
                "site_id": site2.id,
                "action": ["hide"],
                "choices": [self.user.id, self.admin.id]
            }
        )

        self.assertEqual(resp.status_code, 302)
        users = Site.objects.get(id=site2.id).hidden_users.all()
        self.assertEqual(users.count(), 1)
        self.assertTrue(self.admin not in users)

    def test_user_bulk_actions_hide_hidden_user_doesnt_change_status(self):
        resp = self.client.post(
            reverse("c4all_admin:user_bulk_actions"),
            {
                "site_id": self.site.id,
                "action": ["hide"],
                "choices": [self.user_hidden.id]
            }
        )

        self.assertEqual(resp.status_code, 302)
        users = User.objects.filter(hidden=True)
        self.assertEqual(users.count(), 1)
        self.assertTrue(self.user_hidden in users)

    def test_user_hide_not_ajax_call_fails(self):
        """
        Tests endpoint's response to non-ajax call. Endpoint should return
        a 400 response.
        """
        r = self.client.post(
            reverse('c4all_admin:hide_user', args=(
                self.site.id, self.user.id, )),
        )
        self.assertEqual(r.status_code, 400)

    def test_user_hide_succeeds(self):
        """
        Tests endpoint which serves for hiding users. Non hidden user's id is
        provided. After making a call to the endpoint, user's hidden state
        should change to True.
        """
        r = self.client.post(
            reverse('c4all_admin:hide_user', args=(
                self.site.id, self.user.id, )),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(r.status_code, 200)
        user = User.objects.get(id=self.user.id)
        self.assertTrue(user.hidden.filter(id=self.site.id))

    def test_user_hide_admin_fails(self):
        """
        Tests endpoint which serves for hiding users. Admin's id is
        provided. After making a call to the endpoint, endpoint should return
        404 response (admin's state should only be changed from "superadmin")
        """
        r = self.client.post(
            reverse('c4all_admin:hide_user', args=(
                self.site.id, self.admin.id, )),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(r.status_code, 404)
        user = User.objects.get(id=self.admin.id)
        self.assertFalse(user.hidden.filter(id=self.site.id))

    def test_user_hide_hidden_user_doesnt_change_state(self):
        """
        Tests endpoint which serves for hiding users. Hidden user's id is
        provided. After making a call to the endpoint, hidden users's
        state should not be changed.
        """

        r = self.client.post(
            reverse('c4all_admin:hide_user', args=(
                self.site.id, self.user_hidden.id, )),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(r.status_code, 200)
        user = User.objects.get(id=self.user_hidden.id)
        self.assertTrue(user.hidden.filter(id=self.site.id))

    def test_user_hide_returns_404_for_nonexisting_user(self):
        """
        Tests endpoint which serves for hiding users. If non existent user id
        is provided, endpoint should return 404 response.
        """
        r = self.client.post(
            reverse('c4all_admin:hide_user', args=(self.site.id, 9999, )),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(r.status_code, 404)

    def test_user_unhide_not_ajax_call_fails(self):
        """
        Tests endpoint's response to non-ajax call. Endpoint should return
        a 400 response.
        """
        r = self.client.post(
            reverse('c4all_admin:unhide_user', args=(
                self.site.id, self.user.id, )),
        )
        self.assertEqual(r.status_code, 400)

    def test_user_unhide_succeeds(self):
        """
        Tests endpoint which serves for hiding users. Hidden user's id is
        provided. After making a call to the endpoint, user's hidden state
        should change to False.
        """
        r = self.client.post(
            reverse('c4all_admin:unhide_user', args=(
                self.site.id, self.user_hidden.id, )),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(r.status_code, 200)
        user = User.objects.get(id=self.user_hidden.id)
        self.assertFalse(user.hidden.filter(id=self.site.id))

    def test_user_unhide_admin_fails(self):
        """
        Tests endpoint which serves for unhiding users. Admin's id is
        provided. After making a call to the endpoint, endpoint should return
        404 response (admin's state should only be changed from "superadmin")
        """
        r = self.client.post(
            reverse('c4all_admin:hide_user', args=(
                self.site.id, self.admin.id, )),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(r.status_code, 404)
        user = User.objects.get(id=self.admin.id)
        self.assertFalse(user.hidden.filter(id=self.site.id))

    def test_user_unhide_returns_404_for_nonexisting_user(self):
        """
        Tests endpoint which serves for unhiding users. If non existent user id
        is provided, endpoint should return 404 response.
        """
        r = self.client.post(
            reverse('c4all_admin:unhide_user', args=(self.site.id, 9999, )),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(r.status_code, 404)

    def test_admin_changes_password_successfully(self):
        """
        Tests endpoint for changing user's password. If both password and
        repeated password are provided and are the same endpoint should
        return Http200 (and change password, of course). Test also asserts
        that endpoint returns correct user's id for whom the password change
        was attempted.
        """
        pass_1 = self.user.password
        resp = self.client.post(
            reverse("c4all_admin:change_password", args=[self.user.id]),
            data={
                "password1": "pass",
                "password2": "pass"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        pass_2 = User.objects.get(id=self.user.id).password

        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(pass_1, pass_2)
        content = json.loads(resp.content)
        self.assertEqual(content['user_id'], self.user.id)

    def test_admin_changes_password_passwords_different_doesnt_change_password(self):
        """
        If provided password doesn't match repeated password, endpoint
        returns Http400. Test also asserts that endpoint returns correct
        user's id for whom the password change was attempted.
        """
        pass_1 = self.user.password
        resp = self.client.post(
            reverse("c4all_admin:change_password", args=[self.user.id]),
            data={
                "password1": "pass",
                "password2": "pass_pass"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        pass_2 = User.objects.get(id=self.user.id).password

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(pass_1, pass_2)
        content = json.loads(resp.content)
        self.assertEqual(content['user_id'], self.user.id)

    def test_admin_password_change_not_provided_password2_doesnt_change_password(self):
        """
        If repeated password not provided, endpoint returns Http200 but doesn't
        change the password. Test also asserts that endpoint returns correct
        user's id for whom the password change was attempted.
        """
        pass_1 = self.user.password
        resp = self.client.post(
            reverse("c4all_admin:change_password", args=[self.user.id]),
            data={
                "password1": "pass",
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        pass_2 = User.objects.get(id=self.user.id).password

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(pass_1, pass_2)
        content = json.loads(resp.content)
        self.assertEqual(content['user_id'], self.user.id)

    def test_admin_password_change_not_provided_password1_doesnt_change_password(self):
        """
        If password not provided, endpoint returns Http200 but doesn't
        change the password. Test also asserts that endpoint returns correct
        user's id for whom the password change was attempted.
        """
        pass_1 = self.user.password
        resp = self.client.post(
            reverse("c4all_admin:change_password", args=[self.user.id]),
            data={
                "password2": "pass"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        pass_2 = User.objects.get(id=self.user.id).password

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(pass_1, pass_2)
        content = json.loads(resp.content)
        self.assertEqual(content['user_id'], self.user.id)

    def test_admin_password_change_nonexistent_user_returns_404(self):
        """
        If user whose password admin wants to change does not exist,
        endpoint returns Http404.
        """
        pass_1 = self.user.password
        resp = self.client.post(
            reverse("c4all_admin:change_password", args=[9999]),
            data={
                "password1": "pass",
                "password2": "pass"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        pass_2 = User.objects.get(id=self.user.id).password

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(pass_1, pass_2)

    def test_change_admins_password_fails(self):
        """
        Admin's password should not be changed from c4all admin UI. Endpoint
        should return Http404.
        """
        pass_1 = self.user.password
        resp = self.client.post(
            reverse("c4all_admin:change_password", args=[self.admin.id]),
            data={
                "password1": "pass",
                "password2": "pass"
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        pass_2 = User.objects.get(id=self.user.id).password

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(pass_1, pass_2)
