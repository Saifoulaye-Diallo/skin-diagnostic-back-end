class ImageDiagnosticSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source='date_diagnostic', read_only=True)  # 👈 Ajouté ici

    class Meta:
        model = ImageDiagnostic
        fields = [
            'id',
            'nom',
            'prenom',
            'date_naissance',
            'diagnostic_result',
            'created_at',       
            'image',
            'image_url'
        ]
        extra_kwargs = {
            'image': {'max_length': 255}
        }

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url
