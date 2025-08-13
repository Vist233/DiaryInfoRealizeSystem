from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

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


class NoteCreateView(LoginRequiredMixin, CreateView):
    model = Note
    fields = ["title", "content"]
    success_url = reverse_lazy("notes:list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


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
