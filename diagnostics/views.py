from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics, status
from .models import ImageDiagnostic
from .serializers import ImageDiagnosticSerializer
from datetime import datetime

import os
from django.core.files.uploadedfile import SimpleUploadedFile 
from django.utils.text import slugify 
from .utils import *


class DiagnosticView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        print("📦 Données reçues :", request.data)
        print("🖼️ Fichiers reçus :", request.FILES)
        data = request.data.copy()
        data['nom'] = data.get('lastName', '')
        data['prenom'] = data.get('firstName', '')

        # Validation de la date de naissance
        try:
            birth_date_str = data.get('birthDate')
            if birth_date_str:
                data['date_naissance'] = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError) as e:
            print(f"Erreur de date: {str(e)}")
            return Response(
                {"error": "Format de date invalide. Format attendu : AAAA-MM-JJ"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        diagnostic_result = "inconnu"

        # Prédiction à partir de l'image
        if 'image' in request.FILES:
            try:
                uploaded_file = request.FILES['image']

                # Lecture du fichier pour la prédiction
                uploaded_file.seek(0)
                diagnostic_result = predict_diagnostic_from_file(uploaded_file)
                data['diagnostic_result'] = diagnostic_result
                print("🧠 Diagnostic prédit :", diagnostic_result)

                # Renommage du fichier proprement
                uploaded_file.seek(0)
                data['image'], new_filename = handle_uploaded_image(uploaded_file, diagnostic_result)

            except Exception as e:
                print(f"❌ Erreur pendant traitement ou prédiction : {str(e)}")
                return Response(
                    {"error": "Erreur de traitement ou de prédiction de l'image."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response({"error": "Aucune image envoyée."}, status=status.HTTP_400_BAD_REQUEST)

        # Validation et sauvegarde
        serializer = ImageDiagnosticSerializer(data=data, context={'request': request})

        if serializer.is_valid():
            try:
                diagnostic = serializer.save(user=request.user)
                response_data = serializer.data
                response_data['storage'] = str(type(diagnostic.image.storage))
                response_data['filename'] = new_filename
                return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(f"Erreur de sauvegarde: {str(e)}")
                return Response(
                    {"error": "Erreur lors de l'enregistrement"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        print(f"❌ Erreurs de validation: {serializer.errors}")
        return Response(
            {"errors": serializer.errors}, 
            status=status.HTTP_400_BAD_REQUEST
        )

class ImageDiagnosticListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ImageDiagnosticSerializer

    def get_queryset(self):
        return ImageDiagnostic.objects.filter(user=self.request.user).order_by('-date_diagnostic')
