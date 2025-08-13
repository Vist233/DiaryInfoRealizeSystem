from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db import OperationalError, ProgrammingError

from .models import Note


class NoteListView(LoginRequiredMixin, ListView):
    model = Note
    context_object_name = "notes"

    def get_queryset(self):
        return Note.objects.filter(owner=self.request.user)


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


class NoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Note
    fields = ["title", "content"]
    success_url = reverse_lazy("notes:list")

    def get_queryset(self):
        return Note.objects.filter(owner=self.request.user)


class NoteDeleteView(LoginRequiredMixin, DeleteView):
    model = Note
    success_url = reverse_lazy("notes:list")

    def get_queryset(self):
        return Note.objects.filter(owner=self.request.user)
