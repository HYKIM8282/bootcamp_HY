from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings                        # ← 추가
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include(("brokers.urls", "brokers"), namespace="brokers")),
    path("", include(("interactions.urls", "interactions"), namespace="interactions")),
    path("", RedirectView.as_view(url="/login/", permanent=False)),
    # path("", include("brokers.urls", namespace="dashboard")),# 내가추가

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




#path("실제 브라우저 주소창에 찍히는 경로입니다",이 주소로 들어오면 실행될 View 함수(또는 클래스)의 이름, name = 장고 내부(HTML 등)에서 이 주소를 부를 때 쓰는 별명),


#HTML구조: {% url '네임스페이스:URL이름' %}

#1단계: config/urls.py (전체 지도의 시작점),가장 먼저 프로젝트의 메인 설정 폴더(config)에서 각 앱의 URL이 어떻게 포함되어 있는지 확인합니다.
    #파일 경로: 프로젝트폴더/config/urls.py
    #가장 먼저 프로젝트의 메인 설정 폴더(config)에서 각 앱의 URL이 어떻게 포함되어 있는지 확인합니다.
    #의미: "주소창에 아무것도 안 쓰면(root), brokers 폴더 안의 urls.py 파일을 참고해라"라는 뜻입니다.
    #네임스페이스: namespace="brokers"가 설정되어 있어야 나중에 템플릿에서 brokers:이름 형태로 호출 가능합니다.

#2단계: brokers/urls.py (앱 내부의 상세 주소) 실제 각 기능(페이지)의 주소와 이름이 정의된 곳입니다.
    #파일 경로: 프로젝트폴더/brokers/urls.py
    #path("dashboard/", views.dashboard, name="dashboard"),
    #첫 번째 인자 ("dashboard/"): 실제 브라우저 주소창에 찍히는 경로입니다 (/dashboard/).
    #두 번째 인자 (views.dashboard): 이 주소로 들어오면 실행될 View 함수(또는 클래스)의 이름입니다.
    #세 번째 인자 (name="dashboard"): 장고 내부(HTML 등)에서 이 주소를 부를 때 쓰는 별명입니다

    #html파일에서의 경로 확인? 4단계에서  #확인 예시: <a href="{% url 'brokers:dashboard' %}">

#3단계: brokers/views.py (실행되는 로직) , URL에서 지정한 이름이 실제 views.py에 존재하는지 확인합니다.
    #파일 경로: 프로젝트폴더/brokers/views.py
    #함수형 뷰: def dashboard(request):라는 함수가 정의되어 있는가?
    #클래스형 뷰: class BrokerListView(ListView): 등의 클래스가 정의되어 있는가?
    #연결 확인: urls.py에서 views.dashboard라고 썼다면, 여기서 함수명이 정확히 dashboard여야 합니다.

#4단계: templates/*.html (최종 호출 주소) , 화면에서 버튼이나 링크를 눌렀을 때의 경로가 urls.py의 name과 일치하는지 확인합니다.
    #확인 예시: <a href="{% url 'brokers:dashboard' %}">
    #구조: {% url '네임스페이스:URL이름' %}
        #brokers는 config/urls.py에서 정한 namespace 이름입니다.
        #dashboard는 brokers/urls.py에서 정한 name 값입니다.

#요약 체크리스트 (확인 순서)
    #[config/urls.py] brokers.urls를 include 했는가? (앱 연결 확인)
    #[brokers/urls.py] path의 name을 무엇으로 지었는가? (별명 확인)
    #[brokers/urls.py] views.xxx라고 적은 부분이 views.py의 함수명과 똑같은가? (함수 연결 확인)
    #[brokers/views.py] 해당 함수가 마지막에 어떤 HTML을 render 하는가? (화면 연결 확인)
    
