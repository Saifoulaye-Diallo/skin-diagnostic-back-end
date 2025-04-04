from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics, status
from .models import ImageDiagnostic
from .serializers import ImageDiagnosticSerializer
from datetime import datetime

class DiagnosticView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        data = request.data
        user = request.user
        nom = data.get('lastName')
        prenom = data.get('lastName')
        try:
            date_naissance_str = data.get('birthDate')
            date_naissance = datetime.strptime(date_naissance_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return Response({"error": "Format de date invalide. Format attendu : YYYY-MM-DD"}, status=400)
        image = data.get('image')

        if not image:
            return Response({"error": "Image manquante"}, status=400)

        # ⏬ Appel modèle IA ici (à ajouter plus tard)
        diagnostic_result = "Lésion bénigne"  # temporaire

        diagnostic = ImageDiagnostic.objects.create(
            user=user,
            nom=nom,
            prenom=prenom,
            date_naissance=date_naissance,
            image=image,
            diagnostic_result=diagnostic_result
        )

        return Response({
            "id": diagnostic.id,
            "diagnostic": diagnostic_result,
            "image_url": request.build_absolute_uri(diagnostic.image.url),
            "date": diagnostic.date_diagnostic
        }, status=200)


class ImageDiagnosticListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ImageDiagnosticSerializer

    def get_queryset(self):
        return ImageDiagnostic.objects.filter(user=self.request.user).order_by('-date_diagnostic')
