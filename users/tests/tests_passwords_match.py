from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient

from users.libraries.do_passwords_match import passwords_match


class UserTests(APITestCase):
    def test_passwords_match_function(self):
        self.assertEqual(passwords_match('password123', 'password123'), True)
        self.assertEqual(passwords_match('password',''), False)