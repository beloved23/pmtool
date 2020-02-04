from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers


def login_validation(username, password, company_identity, is_api):
    username += "_"+company_identity
    try:
        username = User.objects.get(username=username,
                                    profile__company__identifier__iexact=company_identity,
                                    profile__company__is_active=True)
    except User.DoesNotExist:
        if is_api:
            raise serializers.ValidationError("Invalid login details")
        else:
            raise forms.ValidationError("Invalid login details")
    user_cache = authenticate(username=username, password=password)
    if user_cache is None:
        if is_api:
            raise serializers.ValidationError("Invalid login details")
        else:
            raise forms.ValidationError("Invalid login details")
    elif user_cache is not None and not user_cache.is_active:
        if is_api:
            raise serializers.ValidationError('Your Account has not Activated yet.')
        else:
            raise forms.ValidationError('Your Account has not Activated yet.')
    return user_cache
