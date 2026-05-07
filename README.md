## 부동산 관련 사이트 제작중

```python


🏠 부동산 관련 사이트 (Real Estate Website)
현재 제작 중인 부동산 관련 웹 서비스 프로젝트입니다
.
🛠 기술 스택 (Tech Stack)
이 프로젝트는 다음과 같은 주요 파이썬 라이브러리와 프레임워크를 기반으로 구축되었습니다.
Backend Framework: Django 4.2.11
ASGI Server: Uvicorn 0.27.1, uvloop 0.19.0
Template Engine: Jinja2 3.1.2
Security & Authentication: bcrypt 3.2.2
, PyJWT 2.7.0, oauthlib 3.2.2
Environment Management: python-dotenv 1.0.1
Code Quality & Formatting: pre-commit 3.6.2
Utilities: requests 2.31.0
, rich 13.7.1
, click 8.1.6
⚙️ 설치 및 실행 방법 (Installation & Usage)
1. 저장소 복제 및 가상환경 설정
먼저 프로젝트를 로컬에 클론한 후, 독립적인 파이썬 가상환경을 생성하고 활성화합니다.
git clone <repository-url>
cd <project-directory>
python -m venv venv
source venv/bin/activate  # Windows의 경우: venv\Scripts\activate
2. 의존성 패키지 설치
requirements.txt에 명시된 패키지들을 설치합니다
.
pip install -r requirements.txt
3. 환경 변수 설정
본 프로젝트는 python-dotenv를 활용하여 환경 변수를 관리합니다
. 프로젝트 루트 디렉토리에 .env 파일을 생성하고 데이터베이스 및 시크릿 키 등의 설정값을 입력해 주세요.
4. 서버 실행
개발 서버를 실행합니다. Uvicorn이 설치되어 있으므로 ASGI 기반의 비동기 서버로도 실행할 수 있습니다
.
# 기본 Django 개발 서버 실행
python manage.py runserver

# 또는 Uvicorn을 이용한 ASGI 서버 실행
uvicorn <프로젝트명>.asgi:application --reload
📌 개발자 참고 사항 (Notes)
코드 품질 관리: 이 프로젝트는 일관된 코드 스타일 유지를 위해 **pre-commit**을 도입했습니다
. 코드를 수정하고 커밋하기 전에 반드시 pre-commit install 명령어를 실행하여 Git 훅을 적용해 주시기 바랍니다.
본 서비스는 현재 초기 제작 단계에 있습니다
.


```