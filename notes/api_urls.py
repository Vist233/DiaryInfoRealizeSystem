from django.urls import path

from .api import NotesListCreate, NotesDetail


urlpatterns = [
    path("api/notes/", NotesListCreate.as_view(), name="api_notes_list_create"),
    path("api/notes/<int:pk>/", NotesDetail.as_view(), name="api_notes_detail"),
]

