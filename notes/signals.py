from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import OperationalError, ProgrammingError

from .models import Note, NoteLink
from .utils import extract_wikilinks


@receiver(post_save, sender=Note)
def rebuild_note_links(sender, instance: Note, **kwargs):
    try:
        # Remove existing outbound links
        NoteLink.objects.filter(from_note=instance).delete()
        titles = extract_wikilinks(instance.content)
        if not titles:
            return
        # Map titles to existing notes owned by same user
        targets = {n.title: n for n in Note.objects.filter(owner=instance.owner, title__in=titles)}
        for title in titles:
            target = targets.get(title)
            if target and target.pk != instance.pk:
                NoteLink.objects.get_or_create(from_note=instance, to_note=target)
    except (OperationalError, ProgrammingError):
        # Tables may not exist yet (before migrations) — fail quietly
        return
