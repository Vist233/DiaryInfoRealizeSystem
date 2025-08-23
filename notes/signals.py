from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import OperationalError, ProgrammingError

from .models import Note, NoteLink
from .utils import extract_wikilinks


@receiver(post_save, sender=Note)
def rebuild_note_links(sender, instance: Note, **kwargs):
    try:
        titles = extract_wikilinks(instance.content)
        # Desired target notes
        desired = set()
        if titles:
            targets = {n.title: n for n in Note.objects.filter(owner=instance.owner, title__in=titles)}
            desired = {n.pk for t, n in targets.items() if n and n.pk != instance.pk}

        # Existing outbound target IDs
        existing = set(
            NoteLink.objects.filter(from_note=instance).values_list('to_note_id', flat=True)
        )

        to_add = desired - existing
        to_remove = existing - desired

        if to_remove:
            NoteLink.objects.filter(from_note=instance, to_note_id__in=list(to_remove)).delete()
        for tid in to_add:
            NoteLink.objects.get_or_create(from_note=instance, to_note_id=tid)
    except (OperationalError, ProgrammingError):
        # Tables may not exist yet (before migrations) — fail quietly
        return
