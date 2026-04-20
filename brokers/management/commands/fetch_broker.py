import os
import time
import requests

from django.core.management.base import BaseCommand
from django.db import transaction
from dotenv import load_dotenv

from brokers.models import RealEstateAgent


load_dotenv()


class Command(BaseCommand):
    help = "VWorld 부동산중개업 데이터를 가져와 DB에 저장합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sigungu",
            type=str,
            required=False,
            help="예: 강남구, 관악구, 서초구"
        )
        parser.add_argument(
            "--page",
            type=int,
            default=1,
            help="가져올 페이지 번호"
        )
        parser.add_argument(
            "--size",
            type=int,
            default=10,
            help="한 번에 가져올 개수"
        )

    def handle(self, *args, **options):
        api_key = os.getenv("VWORLD_API_KEY")
        domain = os.getenv("VWORLD_DOMAIN")

        if not api_key:
            self.stdout.write(self.style.ERROR("VWORLD_API_KEY가 .env에 없습니다."))
            return

        if not domain:
            self.stdout.write(self.style.WARNING("VWORLD_DOMAIN이 없어 기본값(http://localhost:8000)을 사용합니다."))
            domain = "http://localhost:8000"

        sigungu = options.get("sigungu")
        page = options.get("page")
        size = options.get("size")

        self.stdout.write(f"api_key exists: {bool(api_key)}")
        self.stdout.write(f"domain: {domain}")
        self.stdout.write(f"sigungu: {sigungu}")
        self.stdout.write(f"page: {page}, size: {size}")

        url = "https://api.vworld.kr/req/data"

        params = {
            "service": "data",
            "request": "GetFeature",
            "data": "EV_BSC_BDONGUPSO_INFO",
            "key": api_key,
            "domain": domain,
            "format": "json",
            "geometry": "false",
            "size": size,
            "page": page,
        }

        # 인증키부터 먼저 확인하려면 attrFilter는 잠시 주석 처리해도 됩니다.
        # 아래 필드명 sigungu 는 실제 VWorld 응답 속성명과 다를 수 있습니다.
        if sigungu:
            params["attrFilter"] = f"sigungu:like:{sigungu}"

        self.stdout.write(self.style.WARNING(f"요청 파라미터: {params}"))

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"API 요청 실패: {e}"))
            return
        except ValueError:
            self.stdout.write(self.style.ERROR("JSON 파싱 실패"))
            return

        self.stdout.write(self.style.SUCCESS("API 응답 수신 성공"))
        self.stdout.write(str(data)[:3000])

        response_body = data.get("response", {})
        status = response_body.get("status")

        if status == "ERROR":
            error_info = response_body.get("error", {})
            self.stdout.write(self.style.ERROR(f"VWorld 오류: {error_info}"))
            return

        features = (
            response_body.get("result", {})
            .get("featureCollection", {})
            .get("features", [])
        )

        if not features:
            self.stdout.write(self.style.WARNING("저장할 데이터가 없습니다."))
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for feature in features:
                props = feature.get("properties", {})

                # -----------------------------
                # VWorld 응답 필드명 후보들
                # 실제 응답 보고 필요시 수정하세요.
                # -----------------------------
                office_name = (
                    props.get("bsnm")
                    or props.get("office_name")
                    or props.get("BSNM")
                    or ""
                )

                broker_name = (
                    props.get("rprsntvNm")
                    or props.get("broker_name")
                    or props.get("RPRSNTVNM")
                    or ""
                )

                road_addr = (
                    props.get("rdnmadr")
                    or props.get("road_addr")
                    or props.get("RDNMADR")
                    or ""
                )

                jibun_addr = (
                    props.get("lnmadr")
                    or props.get("jibun_addr")
                    or props.get("LNMADR")
                    or ""
                )

                tel = (
                    props.get("telno")
                    or props.get("phone")
                    or props.get("TELNO")
                    or ""
                )

                sigungu_name = (
                    props.get("sigungu")
                    or props.get("SIGUNGU")
                    or ""
                )

                license_no = (
                    props.get("regno")
                    or props.get("bsnmCode")
                    or props.get("REGNO")
                    or props.get("BSNMCODE")
                    or None
                )

                if not office_name:
                    skipped_count += 1
                    continue

                unique_value = license_no if license_no else office_name

                # -----------------------------
                # 여기서 RealEstateAgent 모델 필드명과 맞춰야 합니다.
                # 아래 필드명이 models.py와 다르면 수정하세요.
                # -----------------------------
                obj, created = RealEstateAgent.objects.update_or_create(
                    license_no=unique_value,
                    defaults={
                        "office_name": office_name,
                        "broker_name": broker_name,
                        "road_address": road_addr,
                        "jibun_address": jibun_addr,
                        "phone_number": tel,
                        "sigungu_name": sigungu_name,
                        "raw_json": props,
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"저장 완료 - 생성: {created_count}개, 수정: {updated_count}개, 건너뜀: {skipped_count}개"
            )
        )

        time.sleep(0.3)