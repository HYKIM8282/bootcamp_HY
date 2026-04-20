from rest_framework import viewsets
from rest_framework.response import Response


class WorldAPIViewSet(viewsets.ViewSet):
    def list(self, request):
        return Response({
            "message": "VWorld API 테스트용 ViewSet 입니다."
        })