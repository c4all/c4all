from django.test import TestCase

import re
import json


class BaseTestCase(TestCase):

    def get_data_from_response(self, resp):
        result = re.search('{.*}', resp)

        if not result:
            self.fail('could not get data from response')

        return json.loads(result.group(0))
