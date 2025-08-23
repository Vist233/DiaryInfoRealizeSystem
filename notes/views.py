from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db import OperationalError, ProgrammingError, IntegrityError
from django.views import View
from django.http import JsonResponse, HttpRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from io import BytesIO
import zipfile
import re
from datetime import datetime

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
        qs = Note.objects.filter(owner=request.user).order_by('-updated_at')
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
        base = title
        suffix = 1
        while True:
            try:
                note = Note.objects.create(owner=request.user, title=title, content=content)
                break
            except IntegrityError:
                suffix += 1
                cut = 200 - len(f" ({suffix})")
                title = f"{base[:cut]} ({suffix})"
                if suffix > 1000:
                    return JsonResponse({"detail": "too many duplicates"}, status=409)
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
        text = (payload.get('text') or '')
        # Simple per-user rate limit: 60 requests per minute
        try:
            from django.core.cache import cache
            key = f"notes_preview_rate_{request.user.pk}"
            cnt = cache.get(key, 0)
            if cnt >= 60:
                return JsonResponse({'html': '<p class="muted">Rate limited. Try again later.</p>'}, status=429)
            cache.set(key, cnt + 1, 60)
        except Exception:
            pass
        # Protect server from excessively large previews
        if len(text) > 200_000:
            return JsonResponse({'html': '<p class="muted">Preview too large.</p>'}, status=200)

        # Preprocess wikilinks relative to current user (bulk map)
        from .models import Note
        from .utils import extract_wikilinks, render_markdown_safe

        titles = extract_wikilinks(text)
        title_map = {}
        if titles:
            title_map = {n.title: n for n in Note.objects.filter(owner=request.user, title__in=titles)}

        def repl(m):
            title = (m.group(1) or '').strip()
            target = title_map.get(title)
            if target:
                return f'<a href="/{target.pk}/" data-wikilink="{title}">{title}</a>'
            return title
        pre = Note.WIKILINK_RE.sub(repl, text)
        html = render_markdown_safe(pre)
        return JsonResponse({'html': html})


@method_decorator(csrf_exempt, name="dispatch")
class NotesImportUrl(ApiView):
    def post(self, request: HttpRequest):
        payload = _parse_json(request)
        url = (payload.get('url') or '').strip()
        summarize = bool(payload.get('summarize'))
        if not url or not re.match(r'^https?://', url):
            return JsonResponse({"detail": "valid http(s) url required"}, status=400)

        # Fetch
        html = ''
        final_url = url
        try:
            import requests
            headers = {"User-Agent": "NotesBot/1.0 (+https://example.local)"}
            resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            resp.raise_for_status()
            # Limit to 2MB
            html = resp.text[:2_000_000]
            final_url = resp.url or url
        except Exception as e:
            return JsonResponse({"detail": f"fetch failed: {e}"}, status=400)

        # Extract main content
        title = ''
        main_html = ''
        try:
            from readability import Document  # type: ignore
            doc = Document(html)
            title = (doc.short_title() or '').strip()
            main_html = (doc.summary(html_partial=True) or '')
        except Exception:
            # Fallback: naive title
            m = re.search(r'<title>(.*?)</title>', html, flags=re.I | re.S)
            if m:
                title = re.sub(r'\s+', ' ', m.group(1)).strip()
            # As last resort keep full html
            main_html = html

        if not title:
            title = 'Imported Note'

        # Convert to markdown (best-effort)
        markdown_body = ''
        try:
            import markdownify  # type: ignore
            markdown_body = markdownify.markdownify(main_html or html)
        except Exception:
            # Simple strip tags
            markdown_body = re.sub(r'<[^>]+>', '', main_html or html)

        header = f"Source: {final_url}\nFetched: {datetime.utcnow().isoformat()}Z\n\n# {title}\n\n"
        content = header + (markdown_body or '').strip()

        # Optional summarize
        if summarize:
            try:
                summary = self._summarize(markdown_body[:8000])
                if summary:
                    content += f"\n\n---\n## Summary\n\n{summary}\n"
            except Exception:
                pass

        # Create note (dedupe title if needed)
        base, t = title, title
        suffix = 1
        while True:
            try:
                note = Note.objects.create(owner=request.user, title=t[:200], content=content)
                break
            except IntegrityError:
                suffix += 1
                cut = 200 - len(f" ({suffix})")
                t = f"{base[:cut]} ({suffix})"
                if suffix > 1000:
                    return JsonResponse({"detail": "too many duplicates"}, status=409)

        return JsonResponse({"id": note.id, "title": note.title}, status=201)

    def _summarize(self, text: str) -> str:
        try:
            import os
            import openai  # type: ignore
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                raise RuntimeError('no api key')
            client = openai.OpenAI(api_key=api_key) if hasattr(openai, 'OpenAI') else openai
            prompt = (
                "请用中文给出该文章的简要摘要（150~300字），并给出5个要点。\n\n" + text
            )
            # Support both new and legacy clients
            if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                )
                return resp.choices[0].message.content.strip()
            else:
                # Legacy API (very rough fallback)
                return ""
        except Exception:
            # Fallback: naive summary
            paras = [p.strip() for p in text.split('\n') if p.strip()]
            return '\n'.join(paras[:3])


class NotesExport(ApiView):
    def get(self, request: HttpRequest):
        ids = request.GET.get('ids')
        export_all = request.GET.get('all')
        if ids:
            try:
                id_list = [int(x) for x in ids.split(',') if x.strip().isdigit()]
            except Exception:
                return JsonResponse({"detail": "invalid ids"}, status=400)
            qs = Note.objects.filter(owner=request.user, pk__in=id_list)
        elif export_all:
            qs = Note.objects.filter(owner=request.user).order_by('-updated_at')
        else:
            return JsonResponse({"detail": "specify ids or all=1"}, status=400)

        buf = BytesIO()
        with zipfile.ZipFile(buf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
            for n in qs:
                name = self._safe_filename(f"{n.pk}-{n.title}.md")
                zf.writestr(name, n.content or '')
        buf.seek(0)
        resp = HttpResponse(buf.read(), content_type='application/zip')
        resp['Content-Disposition'] = 'attachment; filename="notes_export.zip"'
        return resp

    def _safe_filename(self, s: str) -> str:
        s = re.sub(r'[\\/:*?"<>|]', '_', s)
        return s[:180]
