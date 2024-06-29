from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint


class CatchallEndpoint(Endpoint):
    permission_classes = []

    @csrf_exempt
    def dispatch(self, request: Request, *args, **kwargs) -> Response:
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)
