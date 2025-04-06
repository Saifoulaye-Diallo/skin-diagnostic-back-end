from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics, status
from .models import ImageDiagnostic
from .serializers import ImageDiagnosticSerializer
from datetime import datetime
from datetime import datetime
import os
from django.core.files.uploadedfile import SimpleUploadedFile 
from django.utils.text import slugify 

class DiagnosticView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        data = request.data.copy()
        data['nom'] = data.get('lastName', '')
        data['prenom'] = data.get('firstName', '')
        
        # Validation de la date
        try:
            birth_date_str = data.get('birthDate')
            if birth_date_str:  # Vérification supplémentaire
                data['date_naissance'] = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError) as e:
            print(f"Erreur de date: {str(e)}")
            return Response(
                {"error": "Format de date invalide. Format attendu : AAAA-MM-JJ"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Génération du résultat de diagnostic (simplifié pour l'exemple)
        diagnostic_result = "Lesion_benigne"  # Version sans accents ni espaces
        data['diagnostic_result'] = diagnostic_result
        
        # Traitement du fichier image
        if 'image' in request.FILES:
            uploaded_file = request.FILES['image']
            now = datetime.now()
            
            # Formatage du nom de fichier
            timestamp = now.strftime("%Y%m%d_%H%M%S%f")[:-3]  # Format: 20250405_143022456
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()  # Extension en minuscules
            
            # Création d'un nom de fichier sécurisé
            original_name = os.path.splitext(uploaded_file.name)[0]
            safe_name = slugify(f"{original_name[:20]}_{timestamp}")  # Tronqué à 20 caractères
            new_filename = f"{diagnostic_result}_{safe_name}{file_ext}"
            
            try:
                data['image'] = SimpleUploadedFile(
                    name=new_filename,
                    content=uploaded_file.read(),
                    content_type=uploaded_file.content_type
                )
            except Exception as e:
                print(f"Erreur de lecture du fichier: {str(e)}")
                return Response(
                    {"error": "Erreur de traitement du fichier image"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validation et sauvegarde
        serializer = ImageDiagnosticSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            try:
                diagnostic = serializer.save(user=request.user)
                print(f"✅ Fichier uploadé: {new_filename}")
                print(f"🔗 URL Cloudinary: {diagnostic.image.url}")
                
                # Retourne une réponse enrichie
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
