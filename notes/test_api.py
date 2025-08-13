from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Note, NoteLink


User = get_user_model()


class NotesApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="apiuser", password="pw")

    def test_requires_auth(self):
        resp = self.client.get("/api/notes/")
        self.assertEqual(resp.status_code, 401)

    def test_crud_flow(self):
        self.client.login(username="apiuser", password="pw")
        # Create
        resp = self.client.post(
            "/api/notes/",
            data={"title": "Alpha", "content": "Link to [[Beta]]"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        alpha_id = resp.json()["id"]

        # Create Beta
        resp = self.client.post(
            "/api/notes/",
            data={"title": "Beta", "content": "Back to [[Alpha]]"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        beta_id = resp.json()["id"]

        # List
        resp = self.client.get("/api/notes/?q=Alp")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(n["title"] == "Alpha" for n in resp.json()["results"]))

        # Detail
        resp = self.client.get(f"/api/notes/{alpha_id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["title"], "Alpha")

        # Update
        resp = self.client.patch(
            f"/api/notes/{alpha_id}/",
            data={"content": "Updated"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["content"], "Updated")

        # Links built
        alpha = Note.objects.get(pk=alpha_id)
        beta = Note.objects.get(pk=beta_id)
        self.assertTrue(NoteLink.objects.filter(from_note=alpha, to_note=beta).exists())
        self.assertTrue(NoteLink.objects.filter(from_note=beta, to_note=alpha).exists())

        # Delete
        resp = self.client.delete(f"/api/notes/{alpha_id}/")
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Note.objects.filter(pk=alpha_id).exists())

    def test_preview_endpoint(self):
        self.client.login(username="apiuser", password="pw")
        # Create a referenced note
        note = Note.objects.create(owner=self.user, title="Ref", content="content")
        resp = self.client.post(
            "/api/notes/preview/",
            data={"text": "See [[Ref]] and **bold**"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        html = resp.json().get("html", "")
        self.assertIn(f"/{note.pk}/", html)
        self.assertIn("<strong>", html)
