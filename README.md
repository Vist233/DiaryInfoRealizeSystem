DiaryInfoRealizeSystem (Simplified Notes)

Overview
- Single-app Django project focused on notes with wikilinks ([[Title]]), minimal UI, and inline editing on the detail page.
- Uses SQLite for development, custom `users.User`, and a small JSON API merged into `notes` routes.

Quickstart
1) Create venv and install Django 4.2+
2) Migrate and runserver

```
python -m venv venv
venv\Scripts\activate  # Windows
pip install django==4.2.*
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Optional: Safer Markdown Rendering
- If you install `markdown` and `bleach`, note rendering will use them to sanitize HTML.

```
pip install markdown bleach
```

Key URLs
- Page list: `/`
- Create: `/create/`
- Detail: `/<id>/`
- API: `api/notes/` (GET/POST), `api/notes/<id>/` (GET/PATCH/DELETE)

Inline Editing
- On detail page, click title or content to edit. Ctrl/Cmd+S to save, Esc to cancel.

Search & Quick Create
- List page provides a search box (title/content) and a quick-create box to add a note instantly.

Notes
- Channels/websocket, capture, and AI integration were removed to keep the stack minimal.
- Unique constraint per owner+title is enforced. A migration gently deduplicates existing duplicates.

