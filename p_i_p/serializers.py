from rest_framework import serializers

from p_i_p.models import Pip, Issue, Expectation


class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = ("description", )


class ExpectationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expectation
        fields = ("description", )


class PipSerializer(serializers.ModelSerializer):
    manager = serializers.StringRelatedField()
    issues = IssueSerializer(many=True)
    expectations = ExpectationSerializer(many=True)

    class Meta:
        model = Pip
        fields = "__all__"


class PipCreateSerializer(serializers.ModelSerializer):
    issues = IssueSerializer(many=True, allow_empty=False)
    expectations = ExpectationSerializer(many=True, allow_empty=False)

    class Meta:
        model = Pip
        fields = ("staff", "description", "issues", "expectations")

    def create(self, validated_data):
        issues = validated_data.pop("issues")
        expectations = validated_data.pop("expectations")
        pip = Pip.objects.create(line_manager=self.context["request"].user, **validated_data)
        _issues = [Issue(pip=pip, **issue) for issue in issues]
        _expectations = [Expectation(pip=pip, **expectation) for expectation in expectations]
        Issue.objects.bulk_create(_issues)
        Expectation.objects.bulk_create(_expectations)
        return pip
