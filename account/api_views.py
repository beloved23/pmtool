from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from HRTool import utils
from account.serializers import LoginSerializer, ProfileSerializer, ChangePasswordSerializer

# This text is the description for this API.
#     ---
#         ...
#             - name: username
#               description: Foobar long description goes here
#               required: true
#               type: string
#               paramType: form
#             - name: password
#               paramType: form
#               required: true
#               type: string
#         ...
from kra.models import Message
from kra.serializers import KraSerializer, KraMessagesSerializer
from p_i_p.serializers import PipSerializer
from task.serializers import TaskSerializer


class LoginView(APIView):
    """
    API Endpoint for login.
    ---
    Sample:
    {
        "auuid": "(username)",
        "password": "",
        "company_identity: ""
    }

    """
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            log_user = serializer.get_user()
            token, created = Token.objects.get_or_create(user=log_user)
            return Response(utils.build_response(True, None, {"token": token.key}))
        return Response(utils.build_response(False, None, serializer.errors), status=status.HTTP_400_BAD_REQUEST)


class DashboardView(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        descendants = user.profile.directing_department.members.all().exclude(id=user.profile.id) if hasattr(user.profile, "directing_department") else user.profile.child_members.all()
        data = {
            "descendants": ProfileSerializer(descendants, many=True).data,
            "profile": ProfileSerializer(user.profile).data,
            "ancestor": ProfileSerializer(user.profile.manager).data,
            "tasks": TaskSerializer(user.profile.tasks, many=True).data,
            "pips": PipSerializer(user.pips.all(), many=True).data if hasattr(user, "pips") else [],
            "raised_pips": PipSerializer(user.raised_pips.all(), many=True).data if hasattr(user, "raised_pips") else [],
            "pending_tasks": TaskSerializer(user.profile.pending_tasks, many=True).data,
            "kras": KraSerializer(user.kras.all(), many=True).data if hasattr(user, "kras") else []
        }
        return Response(utils.build_response(True, None, data))


class NotificationsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        messages = Message.objects.filter(kra__in=request.user.kras.all(), read=False).exclude(user=request.user)
        serializer = KraMessagesSerializer(messages, many=True, context={"request": request})
        data = {"messages": serializer.data}
        tasks = request.user.profile.unseen_tasks
        serializer = TaskSerializer(tasks, many=True)
        data["tasks"] = serializer.data
        messages.update(read=True)
        tasks.update(seen=True)
        return Response(utils.build_response(True, None, data))


class ViewMemberProfile(APIView):

    def get(self, request, *args, **kwargs):
        try:
            data = {}
            profile = request.user.profile.directing_department.members.get(id=kwargs['id'])
            kras = profile.user.kras.filter(is_draft=False)
            data["profile"] = ProfileSerializer(profile).data
            data["kras"] = KraSerializer(kras, many=True).data
            return Response(utils.build_response(True, None, data))
        except:
            return Response(utils.build_response(False, "Invalid user", None))


class ChangePasswordView(APIView):
    """
    old_password: string
    new_password: string
    """
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            validated_data = serializer.validated_data
            password = validated_data['new_password']
            user = request.user
            user.set_password(password)
            user.save()
            user.profile.password_changed = True
            return Response(utils.build_response(True, "Password changed successfully", None))
        return Response(utils.build_response(False, None, serializer.errors), status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):

    def get(self, request, *args, **kwargs):
        try:
            request.user.auth_token.delete()
        except:
            pass
        return Response(utils.build_response(True, "Account logged out successfully", None))
