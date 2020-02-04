from django.db import transaction
from rest_framework import serializers

from HRTool import constants
from account.serializers import ProfileSerializer
from kra.models import Kra, KraBucket, KraItem, Message, CompanyKra, CompanyKraItem


class KraBucketSerializer(serializers.ModelSerializer):
    class Meta:
        model = KraBucket
        fields = ("id", "title", "status", "reference")


class KraItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = KraItem
        exclude = ("kra", )


class CompanyKraItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyKraItem
        exclude = ("kra", )


class KraSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    items = KraItemSerializer(many=True)
    bucket = serializers.CharField(source="bucket_title")
    rating = serializers.StringRelatedField()
    hod_rating = serializers.StringRelatedField()

    class Meta:
        model = Kra
        fields = "__all__"


class CompanyKraSerializer(serializers.ModelSerializer):
    items = CompanyKraItemSerializer(many=True)

    class Meta:
        model = CompanyKra
        exclude = ("created_by", "company")


class KraMessagesSerializer(serializers.ModelSerializer):
    user = ProfileSerializer(source="profile")
    kra = KraSerializer()
    is_sender = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = "__all__"

    def get_is_sender(self, instance):
        return instance.user == self.context['request'].user


class KraCreateMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("file", "text")

    def validate(self, attrs):
        attrs = super(KraCreateMessageSerializer, self).validate(attrs)
        if not attrs.get("file") and not attrs.get("text"):
            raise serializers.ValidationError("No message content")
        return attrs


class KraItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = KraItem
        fields = ("name", "weight", "target", "description")


class KraItemUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = KraItem
        fields = ("id", "name", "weight", "target", "description")


class KraCreateSerializer(serializers.ModelSerializer):
    items = KraItemCreateSerializer(many=True, allow_empty=False)
    reference = serializers.ReadOnlyField()

    class Meta:
        model = Kra
        fields = ("bucket", 'reference', "is_draft", "items")
        # depth = 1

    def validate(self, attrs):
        attrs = super(KraCreateSerializer, self).validate(attrs)
        if len(attrs["items"]) < 4:
            raise serializers.ValidationError("Sorry, minimum of 4 KRA items must be set")
        total_weight = sum([float(item["weight"]) for item in attrs["items"]])
        if total_weight != 100:
            raise serializers.ValidationError("KRA weight must sum up to 100, you have %s" % total_weight)
        try:
            bucket = attrs.get("bucket")
            if bucket.status != constants.KRA_BUCKET_OPEN_STATUS:
                raise serializers.ValidationError("Sorry, the KRA bucket is currently closed")
            try:
                has_kra_already = bucket.kras.filter(user=self.context["request"].user, status__in=[constants.KRA_OPEN_STATUS,
                                                                                         constants.KRA_LOCKED_STATUS,
                                                                                         constants.KRA_CLOSED_STATUS], is_draft=False).exists()
            except:
                has_kra_already = False
            if has_kra_already:
                raise serializers.ValidationError("Sorry, you already have a KRA setting for '" + bucket.title + "'")
        except KraBucket.DoesNotExist:
            raise serializers.ValidationError("Sorry, the KRA bucket could not be found")
        return attrs

    def create(self, validated_data):
        items = validated_data.pop("items")
        kra = Kra.objects.create(user=self.context["request"].user, **validated_data)
        kra.status = constants.KRA_OPEN_STATUS if validated_data.get("is_draft", False) else constants.KRA_LOCKED_STATUS
        kra.save()
        _items = [KraItem(kra=kra, **item) for item in items]
        KraItem.objects.bulk_create(_items)
        return kra


class KraUpdateSerializer(serializers.ModelSerializer):
    items = KraItemUpdateSerializer(many=True, allow_empty=False)
    reference = serializers.ReadOnlyField()

    class Meta:
        model = Kra
        fields = ("is_draft", "items", "reference")

    def validate(self, attrs):
        attrs = super(KraUpdateSerializer, self).validate(attrs)
        total_weight = sum([float(item["weight"]) for item in attrs["items"]])
        if len(attrs["items"]) < 4:
            raise serializers.ValidationError("Sorry, minimum of 4 KRA items must be set")
        if total_weight != 100:
            raise serializers.ValidationError("KRA weight must sum up to 100, you have %s" % total_weight)
        try:
            bucket = self.instance.bucket
            if bucket.status != constants.KRA_BUCKET_OPEN_STATUS:
                raise serializers.ValidationError("Sorry, the KRA bucket is currently closed")
            try:
                has_kra_already = bucket.kras.filter(user=self.context["request"].user, status__in=[constants.KRA_OPEN_STATUS,
                                                                                         constants.KRA_LOCKED_STATUS,
                                                                                         constants.KRA_CLOSED_STATUS], is_draft=False).exists()
            except:
                has_kra_already = False
            if has_kra_already:
                raise serializers.ValidationError("Sorry, you already have a KRA setting for '" + bucket.title + "'")
        except KraBucket.DoesNotExist:
            raise serializers.ValidationError("Sorry, the KRA bucket could not be found")
        return attrs

    def update(self, instance, validated_data):
        with transaction.atomic():
            items = validated_data.pop("items")
            instance.is_draft = validated_data.get("is_draft", False)
            instance.status = constants.KRA_OPEN_STATUS if validated_data.get("is_draft", False) else constants.KRA_LOCKED_STATUS
            instance.save()
            not_deleted = []
            new_items = []
            for item in items:
                if "id" in item:
                    not_deleted.append(int(item["id"]))
                else:
                    new_items.append(KraItem(kra=instance, **item))
            instance.items.all().exclude(pk__in=not_deleted).delete()
            KraItem.objects.bulk_create(new_items)
        return instance


class KraToggleSerializer(serializers.ModelSerializer):
    status = serializers.CharField(required=False)
    is_accepted = serializers.BooleanField(required=False)

    class Meta:
        model = Kra
        fields = ("status", "is_accepted")


class KraItemSelfAssessmentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)
    actual = serializers.FloatField(min_value=1, max_value=100, required=True)
    achievement = serializers.FloatField(min_value=1, max_value=100, required=True)
    comment = serializers.CharField(required=True)

    class Meta:
        model = KraItem
        fields = ("id", "actual", "achievement", "comment")


class KraSelfAssessmentSerializer(serializers.ModelSerializer):
    items = KraItemSelfAssessmentSerializer(many=True, allow_empty=False)
    reference = serializers.ReadOnlyField()

    class Meta:
        model = Kra
        fields = ("items", "reference")

    def update(self, instance, validated_data):
        with transaction.atomic():
            items = validated_data.pop("items")
            for item in items:
                kraitem = KraItem.objects.get(id=item['id'])
                kraitem.comment = item['comment']
                kraitem.achievement = item['achievement']
                kraitem.actual = item['actual']
                kraitem.save()
            instance.self_assessed = True
            instance.save()
        return instance


class KraItemFinalAssessmentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)
    manager_achievement = serializers.FloatField(min_value=1, max_value=100, required=True)
    manager_comment = serializers.CharField(required=True)

    class Meta:
        model = KraItem
        fields = ("id", "manager_achievement", "manager_comment")


class KraFinalAssessmentSerializer(serializers.ModelSerializer):
    items = KraItemFinalAssessmentSerializer(many=True, allow_empty=False)
    reference = serializers.ReadOnlyField()

    class Meta:
        model = Kra
        fields = ("items", "reference", "rating")

    def update(self, instance, validated_data):
        with transaction.atomic():
            items = validated_data.pop("items")
            for item in items:
                kraitem = KraItem.objects.get(id=item['id'])
                kraitem.manager_achievement = item['manager_achievement']
                kraitem.manager_comment = item['manager_comment']
                kraitem.save()
            instance.status = constants.KRA_CLOSED_STATUS
            instance.rating = validated_data['rating']
            instance.save()
        return instance


class KraHodRatingSerializer(serializers.ModelSerializer):
    reference = serializers.ReadOnlyField()

    class Meta:
        model = Kra
        fields = ("reference", "hod_rating")
