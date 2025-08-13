from django.conf import settings
from django.db import models
import re
from .utils import render_markdown_safe


class Note(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes")
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = (("owner", "title"),)

    def __str__(self) -> str:
        return self.title

    WIKILINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")

    def extract_wikilinks(self):
        return list({m.group(1).strip(): None for m in self.WIKILINK_RE.finditer(self.content)}.keys())

    def render_content(self):
        """Render content to HTML with safe markdown and wikilinks.

        Strategy: pre-process wikilinks [[Title]] into <a> tags (or plain text
        if not found), then run through safe markdown renderer allowing anchors.
        """
        text = self.content or ""

        def repl(match):
            title = match.group(1).strip()
            target = Note.objects.filter(owner=self.owner, title=title).first()
            if target:
                return f'<a href="/{target.pk}/" data-wikilink="{title}">{title}</a>'
            return title

        preprocessed = self.WIKILINK_RE.sub(repl, text)
        return render_markdown_safe(preprocessed)


class NoteLink(models.Model):
    from_note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="outbound_links")
    to_note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="inbound_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("from_note", "to_note"),)

    def __str__(self) -> str:
        return f"{self.from_note_id} -> {self.to_note_id}"
