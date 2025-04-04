from rest_framework import serializers
from .models import ImageDiagnostic

class ImageDiagnosticSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ImageDiagnostic
        fields = ['id', 'nom', 'prenom', 'date_naissance', 'diagnostic_result', 'date_diagnostic', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url)
