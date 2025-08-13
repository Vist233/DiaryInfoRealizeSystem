import json
from typing import Any, Dict

from django.http import JsonResponse, HttpRequest
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError

from .models import Note


def parse_json(request: HttpRequest) -> Dict[str, Any]:
    try:
        if request.body:
            return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        pass
    return {}


class ApiView(View):
    def dispatch(self, request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required"}, status=401)
        return super().dispatch(request, *args, **kwargs)


@method_decorator(csrf_exempt, name="dispatch")
class NotesListCreate(ApiView):
    def get(self, request: HttpRequest):
        qs = Note.objects.filter(owner=request.user)
        q = request.GET.get("q")
        if q:
            qs = qs.filter(title__icontains=q)
        data = [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "created_at": n.created_at.isoformat(),
                "updated_at": n.updated_at.isoformat(),
            }
            for n in qs
        ]
        return JsonResponse({"results": data}, status=200)

    def post(self, request: HttpRequest):
        payload = parse_json(request) if request.content_type == "application/json" else request.POST
        title = (payload.get("title") or "").strip()
        content = payload.get("content") or ""
        if not title:
            return JsonResponse({"detail": "title is required"}, status=400)
        try:
            note = Note.objects.create(owner=request.user, title=title, content=content)
        except IntegrityError:
            return JsonResponse({"detail": "note with same title already exists"}, status=409)
        return JsonResponse({"id": note.id, "title": note.title, "content": note.content}, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class NotesDetail(ApiView):
    def get_object(self, request: HttpRequest, pk: int) -> Note:
        return Note.objects.filter(owner=request.user, pk=pk).first()

    def get(self, request: HttpRequest, pk: int):
        note = self.get_object(request, pk)
        if not note:
            return JsonResponse({"detail": "not found"}, status=404)
        data = {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(),
        }
        return JsonResponse(data, status=200)

    def patch(self, request: HttpRequest, pk: int):
        note = self.get_object(request, pk)
        if not note:
            return JsonResponse({"detail": "not found"}, status=404)
        payload = parse_json(request)
        title = payload.get("title")
        content = payload.get("content")
        if title is not None:
            note.title = title.strip()
        if content is not None:
            note.content = content
        try:
            note.save()
        except IntegrityError:
            return JsonResponse({"detail": "note with same title already exists"}, status=409)
        return JsonResponse({"id": note.id, "title": note.title, "content": note.content}, status=200)

    put = patch

    def delete(self, request: HttpRequest, pk: int):
        note = self.get_object(request, pk)
        if not note:
            return JsonResponse({"detail": "not found"}, status=404)
        note.delete()
        return JsonResponse({}, status=204)

