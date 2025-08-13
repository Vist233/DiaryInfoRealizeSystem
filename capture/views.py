import json

from django.http import JsonResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from notes.models import Note


@method_decorator(csrf_exempt, name="dispatch")
class CaptureNoteView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required"}, status=401)
        try:
            if request.content_type == "application/json":
                payload = json.loads(request.body.decode("utf-8"))
            else:
                payload = request.POST
            title = (payload.get("title") or "Untitled").strip()
            content = payload.get("content") or ""
            note = Note.objects.create(owner=request.user, title=title, content=content)
            return JsonResponse({"id": note.id, "title": note.title}, status=201)
        except Exception as exc:
            return HttpResponseBadRequest(str(exc))
