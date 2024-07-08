from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.users.serializers import UserSerializer


class ParamSerializer(serializers.Serializer):
    q = serializers.CharField()
    limit = serializers.IntegerField(required=False)


class SearchUserEndpoint(Endpoint):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id="Search a User",
        operation_description=(
            """
            Search a user by username, name, or email.
            """
        ),
        tags=["Account"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", UserSerializer(many=True)),
        },
        manual_parameters=[
            openapi.Parameter(
                "q",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="The keyword to search.",
                required=True,
            ),
            openapi.Parameter(
                "limit",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Limit the number of results",
                required=False,
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        serializer = ParamSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data["q"]
        limit = serializer.validated_data.get("limit", 15)
        User = get_user_model()
        queryset = User.objects.filter(
            Q(username__icontains=query)
            | Q(name__icontains=query)
            | Q(email__icontains=query)
        ).order_by("username")[:limit]
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
