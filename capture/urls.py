from django.urls import path

from .views import CaptureNoteView


urlpatterns = [
    path("api/capture/", CaptureNoteView.as_view(), name="capture_note"),
]

