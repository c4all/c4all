from django.db import IntegrityError
from django.test import Client
from django.core.urlresolvers import reverse

from base import BaseTestCase

from comments.models import CustomUser, Site, Thread, Comment


class CustomUserManagerTestCase(BaseTestCase):

    def test_customusermanager_create_user_succeeds(self):
        email = 'a@b.com'
        CustomUser.objects.create_user(email, 'pass')

        self.assertEqual(CustomUser.objects.count(), 1)
        user = CustomUser.objects.all()[0]
        self.assertEqual(user.email, email)

    def test_customusermanager_user_creation_with_existing_email_fails(self):
        email = 'a@b.com'
        CustomUser.objects.create_user(email, 'pass')
        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(email, 'pass')

    def test_get_user_domain_data(self):
        email = 'a@b.com'
        u = CustomUser.objects.create_user(email, 'pass')

        site = Site.objects.create(domain='www.google.com')
        thread = Thread.objects.create(site=site, url='url')
        thread.disliked_by.add(u)

        comment = Comment.objects.create(thread=thread, user=u, text='aaa')
        comment.liked_by.add(u)

        ret = u.get_user_domain_data()

        self.assertEqual(list(ret['posted_comments']), [comment.id])
        self.assertEqual(list(ret['liked_threads']), [])
        self.assertEqual(list(ret['disliked_threads']), [thread.id])
        self.assertEqual(list(ret['liked_comments']), [comment.id])
        self.assertEqual(list(ret['disliked_comments']), [])

    def test_bulk_delete_successfully_deletes_users(self):
        CustomUser.objects.bulk_create([
            CustomUser(email='a@b.com', password='pass'),
            CustomUser(email='b@b.com', password='pass'),
        ])

        users = CustomUser.objects.all()
        CustomUser.objects.bulk_delete(users)

        self.assertEqual(CustomUser.objects.count(), 0)

    def test_bulk_delete_successfully_deletes_non_staff_users(self):
        CustomUser.objects.bulk_create([
            CustomUser(email='a@b.com', password='pass'),
            CustomUser(email='c@b.com', password='pass', is_staff=True)
        ])

        users = CustomUser.objects.all()
        CustomUser.objects.bulk_delete(users, is_staff=False)

        self.assertEqual(CustomUser.objects.count(), 1)


class CustomUserTestCase(BaseTestCase):

    def test_hide_user_is_success(self):
        """
        Tests hide class method. First user's hidden state is set to False.
        After calling hide method, user's hidden state should be True.
        """
        user = CustomUser.objects.create_user(
            email="donald@duck.com",
            password="pass",
        )
        site = Site.objects.create(domain='www.google.com')
        self.assertFalse(user.hidden.filter(id=site.id))
        user.hide(site)
        self.assertTrue(user.hidden.filter(id=site.id))

    def test_hide_admin_doesnt_change_hidden_state(self):
        """
        Tests hide class method for staff users. First user's hidden state is
        set to False. After calling hide method, user's hidden state should
        not be changed because staff should not be hidden.
        """
        user = CustomUser.objects.create_superuser(
            email="donald@duck.com",
            password="pass",
        )
        site = Site.objects.create(domain='www.google.com')
        self.assertFalse(user.hidden.filter(id=site.id))
        user.hide(site)

        self.assertFalse(user.hidden.filter(id=site.id))

    def test_unhide_user_is_success(self):
        """
        Tests unhide class method. First user's hidden state is set to True.
        After calling unhide method, user's hidden state should be False.
        """
        user = CustomUser.objects.create_user(
            email="donald@duck.com",
            password="pass",
        )
        site = Site.objects.create(domain='www.google.com')
        user.hidden.add(site)
        user.save()

        self.assertTrue(user.hidden.filter(id=site.id))
        user.unhide(site)
        self.assertFalse(user.hidden.filter(id=site.id))

    def test_unhide_admin_is_success(self):
        """
        Tests if admin's hidden flag state is changed by unhide method (though
        admins cannot be hidden by using hide method, hidden flag can be
        set to True in DB by other means)
        """
        user = CustomUser.objects.create_superuser(
            email="donald@duck.com",
            password="pass",
        )
        site = Site.objects.create(domain='www.google.com')
        user.hide(site)
        user.save()

        user.unhide(site)

        self.assertFalse(user.hidden.filter(id=site.id))

    def test_delete_method_deletes_user_comments(self):
        """
        Tests custom delete method in CustomUser model.
        """
        u1 = CustomUser.objects.create_user(
            email="donald@duck.com",
            password="pass"
        )
        CustomUser.objects.create_user(
            email="daffy@duck.com",
            password="pass"
        )

        site = Site.objects.create(domain='www.google.com')
        thread = Thread.objects.create(site=site, url='url')
        Comment.objects.create(thread=thread, user=u1, text='aaa')

        users = CustomUser.objects.all()
        self.assertEqual(users.count(), 2)
        self.assertEqual(Comment.objects.get(user=u1).user, u1)
        u1.delete()
        self.assertEqual(users.count(), 1)
        self.assertFalse(Comment.objects.exists())

    def test_delete_method_doesnt_delete_admin_user(self):
        """
        Tests custom delete method in CustomUser model. Method should not
        be able to delete user who is staff member.
        """
        u1 = CustomUser.objects.create_superuser(
            email="donald@duck.com",
            password="pass"
        )

        site = Site.objects.create(domain='www.google.com')
        thread = Thread.objects.create(site=site, url='url')
        Comment.objects.create(thread=thread, user=u1, text='aaa')

        users = CustomUser.objects.all()
        self.assertEqual(users.count(), 1)
        u1.delete()
        self.assertEqual(users.count(), 1)

    def test_delete_method_deletes_users_comments(self):
        """
        Tests custom delete method in CustomUser model. Except user's data,
        delete should also erase user made comments.
        """
        site = Site.objects.create(domain='www.donald.duck')
        thread = Thread.objects.create(site=site, url='url')

        user = CustomUser.objects.create_user(
            email="donald@duck.com",
            password="pass"
        )

        Comment.objects.create(user=user, thread=thread)
        Comment.objects.create(user=user, thread=thread)

        self.assertEqual(Comment.objects.count(), 2)

        user.delete()

        self.assertEqual(Comment.objects.count(), 0)


class RegisterEndpointTestCase(BaseTestCase):

    def setUp(self):
        self.client = Client()
        self.endpoint_url = reverse('comments:register_user')

    def test_register_user_succeeds(self):
        email = 'a@b.com'

        r = self.client.post(self.endpoint_url, data={
            'email': email,
            'password': 'pass',
            'password2': 'pass',
            'avatar_num': 1,
            'full_name': 'donald duck',
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        self.assertEqual(CustomUser.objects.count(), 1)
        user = CustomUser.objects.all()[0]
        self.assertEqual(user.email, email)

    def test_register_user_twice_with_same_email_fails(self):
        email = 'a@b.com'

        self.client.post(self.endpoint_url, data={
            'email': email,
            'password': 'pass',
            'password2': 'pass',
            'avatar_num': 1,
            'full_name': 'donald duck',
        })

        r = self.client.post(self.endpoint_url, data={
            'email': email,
            'password': 'pass',
            'password2': 'pass',
            'avatar_num': 1,
            'full_name': 'donald duck',
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 400)

    def test_register_user_with_invalid_email_fails(self):
        email = 'this is invalid email'

        r = self.client.post(self.endpoint_url, data={
            'email': email,
            'password': 'pass',
            'password2': 'pass',
            'avatar_num': 1,
            'full_name': 'donald duck',
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 400)

    def test_try_get_request_on_register_endpoint_fails(self):
        email = 'this is invalid email'

        r = self.client.get(self.endpoint_url, data={
            'email': email,
            'password': 'pass',
            'password2': 'pass',
            'avatar_num': 1,
            'full_name': 'donald duck',
        })

        self.assertEqual(r.status_code, 405)

    def test_register_user_with_nonexistent_email_fails(self):
        r = self.client.post(self.endpoint_url, data={
            'password': 'pass',
            'password2': 'pass',
            'avatar_num': 1,
            'full_name': 'donald duck',
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 400)

    def test_register_user_with_nonexistent_password_fails(self):
        email = 'a@b.com'
        r = self.client.post(self.endpoint_url, data={
            'email': email,
            'avatar_num': 1,
            'full_name': 'donald duck',
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 400)

    def test_register_user_returns_iframeId_if_provided(self):
        email = 'a@b.com'
        iframeId = 'some_donald_duck_id_123'

        r = self.client.post(self.endpoint_url, data={
            'email': email,
            'password': 'pass',
            'password2': 'pass',
            'avatar_num': 1,
            'full_name': 'donald duck',
            'iframeId': iframeId,
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        self.assertTrue('iframeId' in data)
        self.assertEqual(data['iframeId'], iframeId)


class LoginEndpointTestCase(BaseTestCase):

    def setUp(self):
        self.client = Client()
        self.endpoint_url = reverse('comments:login_user')

    def test_login_user_succeeds(self):
        email = 'a@b.com'
        password = 'pass'

        CustomUser.objects.create_user(email, password)
        site = Site.objects.create(domain='www.google.com')

        r = self.client.post(self.endpoint_url, data={
            'site_id': site.id,
            'email': email,
            'password': password,
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)

    def test_login_user_fails_no_data(self):
        r = self.client.post(self.endpoint_url, data={})

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 400)

    def test_login_user_no_password_fails(self):
        r = self.client.post(self.endpoint_url, data={
            'email': 'a@b.com',
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 400)

    def test_login_user_no_email_fails(self):
        r = self.client.post(self.endpoint_url, data={
            'password': 'pass',
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 400)

    def test_login_user_wrong_password_fails(self):
        email = 'a@b.com'
        password = 'pass'

        CustomUser.objects.create_user(email, password)

        r = self.client.post(self.endpoint_url, data={
            'email': email,
            'password': 'wrong_password',
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 400)

    def test_login_user_wrong_email_fails(self):
        r = self.client.post(self.endpoint_url, data={
            'email': 'wrong@wrongity.wrong',
            'password': 'pass',
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 400)

    def test_login_user_wrong_http_method(self):
        r = self.client.get(self.endpoint_url, data={
            'email': 'a@b.com',
            'password': 'pass',
        })

        self.assertEqual(r.status_code, 405)

    def test_login_user_returns_iframeId_if_provided(self):
        email = 'a@b.com'
        password = 'pass'

        CustomUser.objects.create_user(email, password)
        iframeId = 'some_donald_duck_id_123'
        site = Site.objects.create(domain='www.google.com')

        r = self.client.post(self.endpoint_url, data={
            'site_id': site.id,
            'email': email,
            'password': password,
            'iframeId': iframeId,
        })

        data = self.get_data_from_response(r.content)
        status_code = data['status_code']

        self.assertEqual(status_code, 200)
        self.assertTrue('iframeId' in data)
        self.assertEqual(data['iframeId'], iframeId)
