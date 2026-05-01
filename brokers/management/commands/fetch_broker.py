import os
import time
import requests

from django.core.management.base import BaseCommand
from django.db import transaction
from dotenv import load_dotenv

from brokers.models import RealEstateAgent

load_dotenv()

BASE_URLS = "https://api.vworld.kr/ned/data/getEBOfficeInfo"

# ─────────────────────────────────────────────────────────────────
# [추가] Kakao 주소검색 REST API URL
# JavaScript 키(지도 표시용)와 다른 별도의 REST API 키가 필요합니다
# 카카오 개발자 콘솔 → 내 애플리케이션 → 앱 키 → REST API 키
# ─────────────────────────────────────────────────────────────────
KAKAO_GEOCODE_URL = "https://dapi.kakao.com/v2/local/search/address.json"


class Command(BaseCommand):
    help = "VWorld NED API로 부동산 중개업소 데이터를 가져와 DB에 저장합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--ldcode",
            type=str,
            default="11110",
            help="시군구코드 (예: 11110 종로구, 11680 강남구)",
        )
        parser.add_argument(
            "--page",
            type=int,
            default=1,
            help="시작 페이지 번호",
        )
        parser.add_argument(
            "--size",
            type=int,
            default=100,
            help="한 번에 가져올 개수 (최대 1000)",
        )
        parser.add_argument(
            "--all-pages",
            action="store_true",
            help="전체 페이지 자동 수집",
        )
        # ─────────────────────────────────────────────────────────
        # [추가] --no-geocode 옵션
        # 지오코딩 없이 빠르게 데이터만 수집하고 싶을 때 사용
        # 예: python manage.py fetch_broker --no-geocode
        # ─────────────────────────────────────────────────────────
        parser.add_argument(
            "--no-geocode",
            action="store_true",
            help="지오코딩 생략 (좌표 저장 없이 빠르게 데이터만 수집)",
        )

    def handle(self, *args, **options):
        api_key = os.getenv("VWORLD_API_KEY")
        domain  = os.getenv("VWORLD_DOMAIN", "http://localhost:8000")

        # ─────────────────────────────────────────────────────────
        # [추가] .env 에서 KAKAO_REST_KEY 읽기
        # .env 파일에 아래 줄 추가 필요:
        #   KAKAO_REST_KEY=카카오_REST_API_키_값
        # ─────────────────────────────────────────────────────────
        kakao_key  = os.getenv("KAKAO_REST_KEY")
        no_geocode = options["no_geocode"]

        if not api_key:
            self.stdout.write(self.style.ERROR("VWORLD_API_KEY가 .env에 없습니다."))
            return

        # [추가] 지오코딩 활성화 여부 판단
        # --no-geocode 옵션이 있거나 KAKAO_REST_KEY 가 없으면 지오코딩 생략
        do_geocode = (not no_geocode) and bool(kakao_key)
        if not do_geocode:
            if no_geocode:
                self.stdout.write(self.style.WARNING("지오코딩 생략 (--no-geocode)"))
            else:
                self.stdout.write(self.style.WARNING(
                    "KAKAO_REST_KEY 없음 → 지오코딩 생략 "
                    "(.env에 KAKAO_REST_KEY 추가 시 자동 활성화)"
                ))

        ldcode    = options["ldcode"]
        page      = options["page"]
        size      = options["size"]
        all_pages = options["all_pages"]

        self.stdout.write(
            f"[설정] ldcode={ldcode}, page={page}, size={size}, "
            f"all_pages={all_pages}, 지오코딩={'ON' if do_geocode else 'OFF'}"
        )

        total_created  = 0
        total_updated  = 0
        total_skipped  = 0
        # [추가] 지오코딩 결과 카운터
        total_geocoded = 0
        total_geo_fail = 0

        while True:
            self.stdout.write(f"\n[요청] page={page}")

            params = {
                "key":       api_key,
                "domain":    domain,
                "format":    "json",
                "numOfRows": size,
                "pageNo":    page,
                "ldCode":    ldcode,
            }

            # ── API 호출 ──────────────────────────────────────────
            try:
                response = requests.get(BASE_URLS, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"API 요청 실패: {e}"))
                break
            except ValueError:
                self.stdout.write(self.style.ERROR("JSON 파싱 실패"))
                break

            # ── 에러 응답 체크 ────────────────────────────────────
            if "error" in data:
                err = data["error"]
                self.stdout.write(
                    self.style.ERROR(
                        f"API 에러: [{err.get('code')}] {err.get('text')}"
                    )
                )
                break

            # ── 응답 파싱 ─────────────────────────────────────────
            fields_wrap = data.get("EDOffices", {})
            fields      = fields_wrap.get("field", [])
            total_count = int(fields_wrap.get("totalCount", 0))

            if isinstance(fields, dict):
                fields = [fields]

            if not fields:
                self.stdout.write(self.style.WARNING("데이터 없음. 수집 종료."))
                break

            self.stdout.write(f"  수신: {len(fields)}건 / 전체: {total_count}건")

            # ── DB 저장 ───────────────────────────────────────────
            created_count = updated_count = skipped_count = 0
            # [추가] 페이지별 지오코딩 카운터
            geo_ok = geo_ng = 0

            with transaction.atomic():
                for props in fields:
                    jurirno = props.get("jurirno", "").strip()

                    if not jurirno:
                        skipped_count += 1
                        continue

                    rdnmadr = props.get("rdnmadr", "")  # [추가] 주소 미리 추출

                    obj, created = RealEstateAgent.objects.update_or_create(
                        jurirno=jurirno,
                        defaults={
                            "ld_code":          props.get("ldCode", ""),
                            "ld_code_nm":       props.get("ldCodeNm", ""),
                            "bsnm_cmpnm":       props.get("bsnmCmpnm", ""),
                            "brkr_nm":          props.get("brkrNm", ""),
                            "sttus_se_code":    props.get("sttusSeCode", ""),
                            "sttus_se_code_nm": props.get("sttusSeCodeNm", ""),
                            "regist_de":        props.get("registDe")     or None,
                            "estbs_begin_de":   props.get("estbsBeginDe") or None,
                            "estbs_end_de":     props.get("estbsEndDe")   or None,
                            "last_updt_dt":     props.get("lastUpdtDt")   or None,
                            "mnnmadr":          props.get("mnnmadr", ""),
                            "rdnmadr":          rdnmadr,
                            "rdnmadr_code":     props.get("rdnmadrcode", ""),
                        },
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                    # ─────────────────────────────────────────────
                    # [추가] 지오코딩: 저장 직후 좌표가 없으면 Kakao API로 변환
                    #
                    # 조건 1: do_geocode=True (키 있고 --no-geocode 아닐 때)
                    # 조건 2: obj.lat is None → 이미 좌표 있으면 API 재호출 안 함
                    # 조건 3: rdnmadr 주소가 있어야 지오코딩 가능
                    #
                    # update_or_create 밖(transaction 안)에서 좌표만 별도 저장:
                    #   → 지오코딩 실패해도 나머지 데이터는 정상 저장됨
                    # ─────────────────────────────────────────────
                    if do_geocode and obj.lat is None and rdnmadr:
                        lat, lng = self._geocode(kakao_key, rdnmadr)
                        if lat and lng:
                            # update_fields 사용: lat/lng 컬럼만 UPDATE
                            # → 불필요한 전체 row UPDATE 방지
                            obj.lat = lat
                            obj.lng = lng
                            obj.save(update_fields=["lat", "lng"])
                            geo_ok += 1
                        else:
                            geo_ng += 1

                        # [추가] Kakao API 호출 간격 (0.15초)
                        # 너무 빠르면 429 Too Many Requests 발생
                        time.sleep(0.15)

            total_created  += created_count
            total_updated  += updated_count
            total_skipped  += skipped_count
            total_geocoded += geo_ok       # [추가]
            total_geo_fail += geo_ng       # [추가]

            # [수정] 지오코딩 결과도 함께 출력
            geo_msg = f" | 지오코딩 성공:{geo_ok} 실패:{geo_ng}" if do_geocode else ""
            self.stdout.write(
                self.style.SUCCESS(
                    f"  page {page} 완료 - "
                    f"생성:{created_count} 수정:{updated_count} "
                    f"건너뜀:{skipped_count}{geo_msg}"
                )
            )

            # ── 다음 페이지 판단 ──────────────────────────────────
            if not all_pages:
                break

            if page * size >= total_count:
                self.stdout.write("  마지막 페이지 도달. 완료.")
                break

            page += 1
            time.sleep(0.3)

        # ── 최종 요약 ─────────────────────────────────────────────
        # [수정] 지오코딩 결과도 최종 요약에 포함
        geo_summary = (
            f" | 좌표저장:{total_geocoded} 지오코딩실패:{total_geo_fail}"
            if do_geocode else ""
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"\n[완료] 전체 - "
                f"생성:{total_created} 수정:{total_updated} "
                f"건너뜀:{total_skipped}{geo_summary}"
            )
        )

    # ─────────────────────────────────────────────────────────────
    # [추가] _geocode 메서드
    #
    # 역할: 도로명 주소 1건을 Kakao 주소검색 API로 좌표 변환
    # 반환: (위도, 경도) 또는 (None, None)
    #
    # Kakao 주소검색 API 응답 구조:
    #   documents[0].y → 위도(lat)
    #   documents[0].x → 경도(lng)
    # ─────────────────────────────────────────────────────────────
    def _geocode(self, kakao_key: str, address: str) -> tuple:
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
            # 개별 주소 오류는 경고만 출력하고 계속 진행
            self.stderr.write(f"    지오코딩 오류: {address} → {e}")
        return None, None
