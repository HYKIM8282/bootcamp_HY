"""
python manage.py geocode_agents

역할:
  DB에 이미 저장된 RealEstateAgent 레코드 중
  lat/lng(좌표)가 없는 것을 Kakao 주소검색 REST API로
  좌표 변환하여 일괄 저장하는 1회성 명령어

사용 예시:
  python manage.py geocode_agents              # 전체 실행
  python manage.py geocode_agents --limit 100  # 100건만 테스트
  python manage.py geocode_agents --delay 0.2  # API 간격 0.2초

실행 전 .env 파일에 아래 키가 있어야 합니다:
  KAKAO_REST_KEY=카카오_REST_API_키
  (카카오 개발자 콘솔 → 내 애플리케이션 → 앱 키 → REST API 키)
"""

import os
import time
import requests

from django.core.management.base import BaseCommand
from dotenv import load_dotenv

from brokers.models import RealEstateAgent

load_dotenv()

# [설정] Kakao 주소검색 REST API 엔드포인트
KAKAO_GEOCODE_URL = "https://dapi.kakao.com/v2/local/search/address.json"


class Command(BaseCommand):
    help = "DB에 좌표 없는 중개사 레코드에 Kakao 주소검색으로 lat/lng를 일괄 저장합니다."

    def add_arguments(self, parser):
        # ─────────────────────────────────────────────────────────
        # --limit: 처리할 최대 건수
        # 전체 18,327건을 한 번에 실행하기 전에
        # --limit 100 으로 먼저 테스트하는 것을 권장
        # ─────────────────────────────────────────────────────────
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="처리할 최대 건수 (기본값: 전체, 테스트 시 100 권장)",
        )
        # ─────────────────────────────────────────────────────────
        # --delay: API 호출 간격(초)
        # Kakao API는 초당 호출 횟수에 제한이 있음
        # 너무 빠르게 보내면 429 Too Many Requests 에러 발생
        # 기본값 0.15초 ≒ 초당 약 6~7회 호출
        # ─────────────────────────────────────────────────────────
        parser.add_argument(
            "--delay",
            type=float,
            default=0.15,
            help="API 호출 간격(초), 기본값 0.15",
        )

    def handle(self, *args, **options):
        # .env 에서 KAKAO_REST_KEY 읽기
        kakao_key = os.getenv("KAKAO_REST_KEY")

        if not kakao_key:
            self.stdout.write(self.style.ERROR(
                "KAKAO_REST_KEY가 .env에 없습니다.\n"
                ".env 파일에 아래 줄을 추가하세요:\n"
                "  KAKAO_REST_KEY=카카오_REST_API_키"
            ))
            return

        limit = options["limit"]
        delay = options["delay"]

        # ─────────────────────────────────────────────────────────
        # 대상 레코드 쿼리:
        #   lat__isnull=True  → 좌표가 아직 없는 레코드만
        #   rdnmadr__gt=""    → 도로명 주소가 있어야 지오코딩 가능
        # ─────────────────────────────────────────────────────────
        qs = RealEstateAgent.objects.filter(
            lat__isnull=True
        ).exclude(
            rdnmadr__isnull=True
        ).exclude(
            rdnmadr=""
        ).order_by("id")   # id 순서로 처리 (재실행 시 일관성 유지)

        if limit:
            qs = qs[:limit]

        total = qs.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS(
                "처리할 레코드가 없습니다. 이미 모든 좌표가 저장되었습니다."
            ))
            return

        # 예상 소요 시간 안내
        estimated_sec = total * delay
        estimated_min = estimated_sec / 60
        self.stdout.write(
            f"처리 대상: {total}건 | "
            f"API 간격: {delay}초 | "
            f"예상 소요: 약 {estimated_min:.1f}분"
        )

        success = 0
        fail    = 0

        for i, agent in enumerate(qs.iterator(), start=1):

            # Kakao 주소검색 API 호출
            lat, lng = self._geocode(kakao_key, agent.rdnmadr)

            if lat and lng:
                # 좌표 변환 성공 → lat, lng 컬럼만 업데이트
                # update_fields 사용으로 불필요한 전체 row UPDATE 방지
                agent.lat = lat
                agent.lng = lng
                agent.save(update_fields=["lat", "lng"])
                success += 1
            else:
                # 변환 실패 (주소 불명확, API 오류 등)
                fail += 1

            # 100건마다 진행 상황 출력
            if i % 100 == 0 or i == total:
                self.stdout.write(
                    f"  [{i:>6}/{total}] 성공:{success}건  실패:{fail}건"
                )

            # API 호출 간격 (429 에러 방지)
            time.sleep(delay)

        # 최종 결과 출력
        self.stdout.write(self.style.SUCCESS(
            f"\n[완료] 성공:{success}건 / 실패:{fail}건 / 전체:{total}건\n"
            f"실패한 {fail}건은 주소가 불명확하거나 Kakao DB에 없는 주소입니다."
        ))

    def _geocode(self, kakao_key: str, address: str) -> tuple:
        """
        Kakao 주소검색 REST API 호출
        성공 → (위도float, 경도float)
        실패 → (None, None)

        Kakao API 응답 구조:
          documents[0].y → 위도(lat)
          documents[0].x → 경도(lng)
        """
        try:
            resp = requests.get(
                KAKAO_GEOCODE_URL,
                headers={"Authorization": f"KakaoAK {kakao_key}"},
                params={"query": address, "size": 1},
                timeout=5,
            )
            resp.raise_for_status()
            docs = resp.json().get("documents", [])
            if docs:
                return float(docs[0]["y"]), float(docs[0]["x"])
        except Exception as e:
            self.stderr.write(f"    오류: {address} → {e}")
        return None, None
