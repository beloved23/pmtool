from rest_framework.generics import RetrieveAPIView, CreateAPIView, ListAPIView, get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from HRTool import utils
from company.models import Config
from company.serializers import CompanyConfigSerializer, CompanyRatingSerializer


class CompanyConfigView(RetrieveAPIView):
    lookup_url_kwarg = "identifier"
    lookup_field = "company__identifier"
    serializer_class = CompanyConfigSerializer
    permission_classes = (AllowAny, )
    queryset = Config.objects.all()

    def retrieve(self, request, *args, **kwargs):
        serializer = self.serializer_class(self.get_object())
        return Response(utils.build_response(True, None, serializer.data))


class CompanyRatingList(ListAPIView):
    serializer_class = CompanyRatingSerializer
    pagination_class = None

    def get_queryset(self):
        return self.request.user.profile.company.config.ratings.all()

    def list(self, request, *args, **kwargs):
        return Response(utils.build_response(True, None, self.get_serializer(self.get_queryset(), many=True).data))


class AddTaskView(CreateAPIView):
    serializer_class = None
