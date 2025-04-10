from django.urls import path
from .views import DiagnosticView, ImageDiagnosticListView,UpdateDiagnosticView,DeleteDiagnosticView

urlpatterns = [
    path('diagnostic/', DiagnosticView.as_view(), name='diagnostic'),
    path('images/', ImageDiagnosticListView.as_view(), name='image-list'),

    # 🔁 Ajout de update et delete
    path('diagnostic/update/<int:id>/', UpdateDiagnosticView.as_view(), name='update-diagnostic'),
    path('diagnostic/delete/<int:id>/', DeleteDiagnosticView.as_view(), name='delete-diagnostic'),
]
