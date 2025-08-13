from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db import OperationalError, ProgrammingError, IntegrityError
from django.views import View
from django.http import JsonResponse, HttpRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import Note


class NoteListView(LoginRequiredMixin, ListView):
    model = Note
    context_object_name = "notes"

    def get_queryset(self):
        qs = Note.objects.filter(owner=self.request.user)
        q = (self.request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(models.Q(title__icontains=q) | models.Q(content__icontains=q))
        return qs


class NoteDetailView(LoginRequiredMixin, DetailView):
    model = Note

    def get_queryset(self):
        return Note.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rendered"] = self.object.render_content()
        try:
            ctx["outbound_links"] = list(self.object.outbound_links.select_related("to_note").all())
            ctx["inbound_links"] = list(self.object.inbound_links.select_related("from_note").all())
        except (OperationalError, ProgrammingError):
            ctx["outbound_links"] = []
            ctx["inbound_links"] = []
        # titles for client-side missing-link suggestions
        ctx["existing_titles"] = list(
            Note.objects.filter(owner=self.request.user).exclude(pk=self.object.pk).values_list("title", flat=True)
        )
        return ctx


class NoteCreateView(LoginRequiredMixin, CreateView):
    model = Note
    fields = ["title", "content"]
    success_url = reverse_lazy("notes:list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        title = self.request.GET.get("title")
        if title:
            initial["title"] = title
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["existing_titles"] = list(
            Note.objects.filter(owner=self.request.user).values_list("title", flat=True)
        )
        return ctx


class NoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Note
    fields = ["title", "content"]
    success_url = reverse_lazy("notes:list")

    def get_queryset(self):
        return Note.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["existing_titles"] = list(
            Note.objects.filter(owner=self.request.user).exclude(pk=self.object.pk).values_list("title", flat=True)
        )
        return ctx


class NoteDeleteView(LoginRequiredMixin, DeleteView):
    model = Note
    success_url = reverse_lazy("notes:list")

    def get_queryset(self):
        return Note.objects.filter(owner=self.request.user)


# -------- API (merged here for a single-app structure) --------

def _parse_json(request: HttpRequest):
    import json
    try:
        if request.body:
            return json.loads(request.body.decode("utf-8"))
    except Exception:
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
        payload = _parse_json(request) if request.content_type == "application/json" else request.POST
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
    def get_object(self, request: HttpRequest, pk: int):
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
        payload = _parse_json(request)
        title = payload.get("title")
        content = payload.get("content")
        if title is not None:
            note.title = (title or '').strip()
        if content is not None:
            note.content = content or ''
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


@method_decorator(csrf_exempt, name="dispatch")
class NotesPreview(ApiView):
    def post(self, request: HttpRequest):
        payload = _parse_json(request)
        text = payload.get('text') or ''
        # Preprocess wikilinks relative to current user
        from .models import Note
        def repl(m):
            title = (m.group(1) or '').strip()
            target = Note.objects.filter(owner=request.user, title=title).first()
            if target:
                return f'<a href="/{target.pk}/" data-wikilink="{title}">{title}</a>'
            return title
        pre = Note.WIKILINK_RE.sub(repl, text)
        from .utils import render_markdown_safe
        html = render_markdown_safe(pre)
        return JsonResponse({'html': html})
