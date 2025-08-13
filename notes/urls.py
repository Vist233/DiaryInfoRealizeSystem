from django.urls import path

from . import views


app_name = "notes"

urlpatterns = [
    path("", views.NoteListView.as_view(), name="list"),
    path("create/", views.NoteCreateView.as_view(), name="create"),
    path("<int:pk>/", views.NoteDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.NoteUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.NoteDeleteView.as_view(), name="delete"),
    # API endpoints (merged for simplicity)
    path("api/notes/", views.NotesListCreate.as_view(), name="api_notes_list_create"),
    path("api/notes/<int:pk>/", views.NotesDetail.as_view(), name="api_notes_detail"),
    path("api/notes/preview/", views.NotesPreview.as_view(), name="api_notes_preview"),
]
