# Generated manually to add NoteLink and unique_together on Note
from django.db import migrations, models
from django.db.models import Count


def dedupe_titles(apps, schema_editor):
    Note = apps.get_model('notes', 'Note')
    # Find duplicates per (owner, title)
    dup_groups = (
        Note.objects.values('owner_id', 'title')
        .annotate(c=Count('id'))
        .filter(c__gt=1)
    )
    for grp in dup_groups:
        owner_id = grp['owner_id']
        title = grp['title'] or ''
        # Fetch all notes with this (owner, title), order stable by created time/id
        rows = list(Note.objects.filter(owner_id=owner_id, title=title).order_by('created_at', 'id'))
        if not rows or len(rows) == 1:
            continue
        # Keep the first unchanged; rename subsequent with suffixes (2..n), avoid collisions
        existing = set(
            Note.objects.filter(owner_id=owner_id).values_list('title', flat=True)
        )
        # Remove current title once so we can reuse the set for collision checks
        # (we'll add new titles as we go)
        # First item kept
        kept = rows[0]
        # Ensure we don't double-count kept title
        # Append suffixes to the rest
        for idx, note in enumerate(rows[1:], start=2):
            base = title
            suffix = f" ({idx})"
            # Trim to fit max_length 200
            max_len = 200
            cut = max_len - len(suffix)
            if len(base) > cut:
                base = base[:cut]
            new_title = f"{base}{suffix}"
            # Ensure unique within this owner
            n = idx
            while new_title in existing:
                n += 1
                suffix = f" ({n})"
                cut = max_len - len(suffix)
                b = title
                if len(b) > cut:
                    b = b[:cut]
                new_title = f"{b}{suffix}"
            note.title = new_title
            note.save(update_fields=['title'])
            existing.add(new_title)
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(dedupe_titles, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='note',
            unique_together={("owner", "title")},
        ),
        migrations.CreateModel(
            name='NoteLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('from_note', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outbound_links', to='notes.note')),
                ('to_note', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inbound_links', to='notes.note')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='notelink',
            unique_together={("from_note", "to_note")},
        ),
    ]
