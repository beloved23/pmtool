from rest_framework import serializers

from account import logic
from account.models import Profile


class LoginSerializer(serializers.Serializer):
    auuid = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    company_identity = serializers.CharField(required=True)

    def validate(self, attrs):
        cd = attrs
        username = cd.get('auuid')
        password = cd.get('password')
        company_identity = cd.get('company_identity')
        if username and password and company_identity:
            self.user_cache = logic.login_validation(username, password, company_identity, True)
        return cd

    def get_user(self):
        return self.user_cache


class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    department = serializers.StringRelatedField()
    role = serializers.StringRelatedField()
    manager = serializers.StringRelatedField()
    is_hod = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        exclude = ("user", "company")

    def get_is_hod(self, instance):
        return hasattr(instance, "directing_department")

    def get_email(self, instance):
        return instance.user.email

    def get_user_id(self, instance):
        return instance.user.id


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=12, min_length=6, required=True, )
    new_password = serializers.CharField(max_length=12, min_length=6, required=True, )

    def validate(self, cd):
        user = self.context.get('request').user
        if not user.check_password(cd.get("old_password")):
            raise serializers.ValidationError("Incorrect Old password")
        return cd
