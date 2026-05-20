from django.conf import settings

def kakao_key(request):
    return {'kakao_key': settings.KAKAO_JS_KEY}