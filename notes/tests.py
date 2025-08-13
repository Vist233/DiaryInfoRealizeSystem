from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Note, NoteLink
from .utils import extract_wikilinks

User = get_user_model()


class WikiLinkTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="x")

    def test_extract_wikilinks(self):
        text = "Alpha [[Beta]] and [[Gamma]] and [[Beta]] again"
        self.assertEqual(sorted(extract_wikilinks(text)), ["Beta", "Gamma"])

    def test_render_and_links(self):
        a = Note.objects.create(owner=self.user, title="Alpha", content="Link to [[Beta]]")
        b = Note.objects.create(owner=self.user, title="Beta", content="Back to [[Alpha]]")
        # Signals should create link pairs
        self.assertTrue(NoteLink.objects.filter(from_note=a, to_note=b).exists())
        self.assertTrue(NoteLink.objects.filter(from_note=b, to_note=a).exists())
        html = a.render_content()
        self.assertIn(f"/{b.pk}/", html)
