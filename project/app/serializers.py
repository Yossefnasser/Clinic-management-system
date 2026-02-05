from .models import Patient , Branch
from rest_framework import serializers
class PatientSerializer(serializers.ModelSerializer):
  branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=False, allow_null=True)
  class Meta:
    model = Patient
    fields = '__all__'
    read_only_fields = ['id','added_date', 'created_at', 'updated_at']