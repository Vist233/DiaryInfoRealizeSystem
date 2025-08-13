from django.contrib.auth import get_user_model
from django.test import TestCase

from notes.models import Note


User = get_user_model()


class CaptureApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="capuser", password="pw")

    def test_auth_required(self):
        resp = self.client.post("/api/capture/", data={"title": "X"})
        self.assertEqual(resp.status_code, 401)

    def test_create_note(self):
        self.client.login(username="capuser", password="pw")
        resp = self.client.post("/api/capture/", data={"title": "Cap", "content": "Body"})
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Note.objects.filter(owner=self.user, title="Cap").exists())

