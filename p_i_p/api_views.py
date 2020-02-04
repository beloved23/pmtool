from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from HRTool import utils
from HRTool.notifications import NotificationManager
from p_i_p.serializers import PipCreateSerializer, PipSerializer


class PipCreateAPIView(CreateAPIView):
    serializer_class = PipCreateSerializer

    def create(self, request, *args, **kwargs):
        super(PipCreateAPIView, self).create(request, *args, **kwargs)
        NotificationManager.pip_notification(self.request, self.object.staff, self.object)
        return Response(utils.build_response(True, "PIP created successfully", PipSerializer(self.object).data))

    def perform_create(self, serializer):
        self.object = serializer.save()
