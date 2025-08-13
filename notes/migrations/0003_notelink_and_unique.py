# Generated manually to add NoteLink and unique_together on Note
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0002_initial'),
    ]

    operations = [
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

