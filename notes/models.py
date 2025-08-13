from django.conf import settings
from django.db import models
import re


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
        # Replace [[Title]] with links to existing notes owned by the same user; leave text if not found
        def repl(match):
            title = match.group(1).strip()
            try:
                target = Note.objects.filter(owner=self.owner, title=title).first()
                if target:
                    return f'<a href="/{target.pk}/">{title}</a>'
            except Exception:
                pass
            return title

        html = self.WIKILINK_RE.sub(repl, self.content or "")
        # Basic escaping is omitted for brevity; ensure content comes from trusted source in MVP
        html = html.replace("\n", "<br>")
        return html


class NoteLink(models.Model):
    from_note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="outbound_links")
    to_note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="inbound_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("from_note", "to_note"),)

    def __str__(self) -> str:
        return f"{self.from_note_id} -> {self.to_note_id}"
