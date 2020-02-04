from django.template.loader import render_to_string
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView, UpdateAPIView, RetrieveAPIView, get_object_or_404, DestroyAPIView
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from HRTool import utils, constants
from HRTool.notifications import NotificationManager
from company.serializers import CompanyRatingSerializer
from kra.models import Kra
from kra.serializers import KraBucketSerializer, KraCreateSerializer, KraMessagesSerializer, KraCreateMessageSerializer, \
    KraSerializer, CompanyKraSerializer, KraUpdateSerializer, KraToggleSerializer, KraSelfAssessmentSerializer, \
    KraFinalAssessmentSerializer, KraHodRatingSerializer


class KraCreateAPIView(CreateAPIView):
    serializer_class = KraCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            kra = self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            message = "KRA setting saved as draft"
            if not validated_data.get("is_draft", False):
                message = "KRA setting submitted for assessment"
                if self.request.user.profile.manager:
                    NotificationManager.kra_setting_notification(self.request, kra)
            return Response(utils.build_response(True, message, serializer.data), headers=headers)
        return Response(utils.build_response(False, None, serializer.errors))

    def perform_create(self, serializer):
        return serializer.save()


class KraUpdateAPIView(UpdateAPIView):
    lookup_field = "identifier"
    lookup_url_kwarg = "identifier"
    serializer_class = KraUpdateSerializer

    def get_queryset(self):
        return self.request.user.kras.filter(status=constants.KRA_OPEN_STATUS)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            kra = self.perform_update(serializer)
            message = "KRA setting saved as draft"
            if not validated_data.get("is_draft", False):
                message = "KRA setting submitted for assessment"
                if self.request.user.profile.manager:
                    NotificationManager.kra_setting_notification(self.request, kra)
            return Response(utils.build_response(True, message, KraSerializer(kra).data))
        return Response(utils.build_response(False, None, serializer.errors))

    def perform_update(self, serializer):
        return serializer.save()


class KraToggleAPIView(UpdateAPIView):
    lookup_field = "identifier"
    lookup_url_kwarg = "identifier"
    serializer_class = KraToggleSerializer
    queryset = Kra.objects.filter(status=constants.KRA_LOCKED_STATUS, is_accepted=False)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            kra = self.perform_update(serializer)
            NotificationManager.kra_update_notification(self.request, kra)
            return Response(utils.build_response(True, None, KraSerializer(kra).data))
        return Response(utils.build_response(False, None, serializer.errors))

    def perform_update(self, serializer):
        return serializer.save()


class KraSelfAssessmentAPIView(UpdateAPIView):
    lookup_field = "identifier"
    lookup_url_kwarg = "identifier"
    serializer_class = KraSelfAssessmentSerializer
    queryset = Kra.objects.filter(status=constants.KRA_LOCKED_STATUS, is_accepted=True, self_assessed=False)

    def get(self, request, *args, **kwargs):
        bucket = self.get_object().bucket
        return Response(utils.build_response(bucket.allow_self_assessment, None, None))

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            # return Response(utils.build_response(False, None, serializer.validated_data))
            kra = self.perform_update(serializer)
            NotificationManager.kra_update_notification(self.request, kra)
            return Response(utils.build_response(True, "KRA Self-assessment completed successfully", KraSerializer(kra).data))
        return Response(utils.build_response(False, None, serializer.errors))

    def perform_update(self, serializer):
        return serializer.save()


class KraAssessmentAPIView(UpdateAPIView):
    lookup_field = "identifier"
    lookup_url_kwarg = "identifier"
    serializer_class = KraFinalAssessmentSerializer
    queryset = Kra.objects.filter(status=constants.KRA_LOCKED_STATUS, is_accepted=True)

    def get(self, request, *args, **kwargs):
        bucket = self.get_object().bucket
        ratings = self.request.user.profile.company.config.ratings.all()
        return Response(utils.build_response(bucket.allow_final_assessment, None, CompanyRatingSerializer(ratings, many=True).data))

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            kra = self.perform_update(serializer)
            NotificationManager.kra_update_notification(self.request, kra)
            return Response(utils.build_response(True, "KRA Assessment completed successfully", KraSerializer(kra).data))
        return Response(utils.build_response(False, None, serializer.errors))

    def perform_update(self, serializer):
        return serializer.save()


class KraHodRatingAPIView(UpdateAPIView):
    lookup_field = "identifier"
    lookup_url_kwarg = "identifier"
    serializer_class = KraHodRatingSerializer
    queryset = Kra.objects.filter(status=constants.KRA_CLOSED_STATUS, is_accepted=True, rating__isnull=False)

    def get(self, request, *args, **kwargs):
        bucket = self.get_object().bucket
        ratings = self.request.user.profile.company.config.ratings.all()
        return Response(utils.build_response(bucket.allow_final_assessment, None, CompanyRatingSerializer(ratings, many=True).data))

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            kra = self.perform_update(serializer)
            # NotificationManager.kra_update_notification(self.request, kra)
            return Response(utils.build_response(True, "KRA rated successfully", KraSerializer(kra).data))
        return Response(utils.build_response(False, None, serializer.errors))

    def perform_update(self, serializer):
        return serializer.save()


class KraMessagesAPIView(APIView):
    lookup_field = "identifier"
    lookup_url_kwarg = "identifier"
    serializer_class = KraMessagesSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser, ]

    def get(self, request, *args, **kwargs):
        kra = get_object_or_404(Kra, identifier=kwargs["identifier"])
        if kra.user != request.user and kra.user.profile.manager != request.user.profile:
            return Response(utils.build_response(False, "Invalid KRA", []))
        kra.messages.all().exclude(user=request.user).update(read=True)
        return Response(utils.build_response(True, None, KraMessagesSerializer(kra.messages.all(), many=True, context={"request": request}).data))

    def post(self, request, *args, **kwargs):
        kra = get_object_or_404(Kra, identifier=kwargs["identifier"])
        if kra.user != request.user and kra.user.profile.manager != request.user.profile:
            return Response(utils.build_response(False, "Permission denied", None))
        serializer = KraCreateMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, kra=kra,
                            file_type=serializer.validated_data["file"].content_type if "file" in serializer.validated_data and serializer.validated_data["file"] else None,
                            filename=serializer.validated_data["file"].name if "file" in serializer.validated_data and serializer.validated_data["file"] else None)
            if not kra.is_draft:
                NotificationManager.kra_update_notification(request, kra)
            return Response(utils.build_response(True, "Message sent", KraMessagesSerializer(kra.messages.all(), many=True, context={"request": request}).data))
        return Response(utils.build_response(False, None, serializer.errors))


class KraDeleteAPIView(DestroyAPIView):
    lookup_field = "identifier"
    lookup_url_kwarg = "identifier"
    # serializer_class = KraSerializer

    def get_queryset(self):
        return get_object_or_404(Kra, identifier=self.kwargs.get("identifier"), user=self.request.user, is_draft=True)

    def destroy(self, request, *args, **kwargs):
        super(KraDeleteAPIView, self).destroy(request, *args, **kwargs)
        return Response(utils.build_response(True, "KRA deleted successfully", None))


class KraBucketAPIView(APIView):
    def get(self, request, *args, **kwargs):
        if "reference" in kwargs:
            user = request.user
            buckets = user.profile.company.kra_buckets.all()
            instance = buckets.get(reference=kwargs['reference'])
            serializer = KraBucketSerializer(instance)
            data = serializer.data
            if hasattr(instance, "company_kra"):
                data["company_kra"] = CompanyKraSerializer(instance.company_kra).data
            else:
                data["company_kra"] = None
            try:
                manager_kra = Kra.objects.get(user=user.profile.manager.user, bucket=instance, status__in=[
                    constants.KRA_LOCKED_STATUS, constants.KRA_OPEN_STATUS, constants.KRA_CLOSED_STATUS],
                                              is_draft=False)
                data["manager_kra"] = KraSerializer(manager_kra).data
            except:
                data["manager_kra"] = None

            if hasattr(instance, "kras"):
                data["team_kras"] = KraSerializer(instance.kras.filter(user__profile__in=self.request.user.profile.child_members.all(), is_draft=False), many=True).data
            else:
                kwargs["team_kras"] = []
            return Response(utils.build_response(True, None, data))
        else:
            try:
                serializer = KraBucketSerializer(request.user.profile.company.kra_buckets.all(), many=True)
                return Response(utils.build_response(True, None, serializer.data))
            except:
                return Response(utils.build_response(True, None, []))
