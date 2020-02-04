from rest_framework import serializers

from company.models import Config, Rating, Company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        exclude = ("created_by", )


class CompanyConfigSerializer(serializers.ModelSerializer):
    company = CompanySerializer()

    class Meta:
        model = Config
        exclude = ("date_created", "date_updated")


class CompanyRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ("id", "name", )
