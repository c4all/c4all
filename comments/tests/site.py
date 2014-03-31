from django.test import TestCase

from comments.forms import SiteForm

class SiteTestCase(TestCase):
    pass

class SiteFormTestCase(TestCase):

    def test_form_validation_success(self):
        domain = 'www.google.com'

        form = SiteForm(data={'domain': domain})
        if form.is_valid():
            site = form.save()

        self.assertEqual(site.domain, domain)

    def test_url_contains_protocol_success(self):
        domain = 'https://www.google.com'

        form = SiteForm(data={'domain': domain})
        if form.is_valid():
            site = form.save()

        self.assertEqual(site.domain, "www.google.com")

    def test_wrong_url_no_success(self):
        domain = 'mailto:foc@example.com?subjects=pajcek.lala.net'

        form = SiteForm(data={'domain': domain})
        self.assertFalse(form.is_valid())
