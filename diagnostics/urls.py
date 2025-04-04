from django.urls import path
from .views import DiagnosticView, ImageDiagnosticListView

urlpatterns = [
    path('diagnostic/', DiagnosticView.as_view(), name='diagnostic'),
    path('images/', ImageDiagnosticListView.as_view(), name='image-list'),
]
