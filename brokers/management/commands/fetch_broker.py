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
            "--ldcode",
            type=str,
            default="11110",
            help="시군구코드 (예: 11110 종로구, 11680 강남구)"
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
            default=100,
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

        ldcode = options.get("ldcode")
        page = options.get("page")
        size = options.get("size")

        self.stdout.write(f"api_key exists: {bool(api_key)}")
        self.stdout.write(f"domain: {domain}")
        self.stdout.write(f"ldcode: {ldcode}")
        self.stdout.write(f"page: {page}, size: {size}")

        url = "https://api.vworld.kr/ned/data/getEBOfficeInfo"

        params = {
            "key": api_key,
            "domain": domain,
            "format": "json",
            "numOfRows": size,
            "pageNo": page,
            "ldCode": ldcode,
        }

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

        # JSON 응답 파싱
        fields_wrap = data.get("fields", {})
        fields = fields_wrap.get("field", [])

        # 결과가 1건이면 dict로 오므로 리스트로 통일
        if isinstance(fields, dict):
            fields = [fields]

        if not fields:
            self.stdout.write(self.style.WARNING("저장할 데이터가 없습니다."))
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for props in fields:
                jurirno = props.get("jurirno", "")

                if not jurirno:
                    skipped_count += 1
                    continue

                obj, created = RealEstateAgent.objects.update_or_create(
                    jurirno=jurirno,
                    defaults={
                        "ld_code":          props.get("ldCode", ""),
                        "ld_code_nm":       props.get("ldCodeNm", ""),
                        "bsnm_cmpnm":       props.get("bsnmCmpnm", ""),
                        "brkr_nm":          props.get("brkrNm", ""),
                        "sttus_se_code":    props.get("sttusSeCode", ""),
                        "sttus_se_code_nm": props.get("sttusSeCodeNm", ""),
                        "regist_de":        props.get("registDe") or None,
                        "estbs_begin_de":   props.get("estbsBeginDe") or None,
                        "estbs_end_de":     props.get("estbsEndDe") or None,
                        "last_updt_dt":     props.get("lastUpdtDt") or None,
                        "mnnmadr":          props.get("mnnmadr", ""),
                        "rdnmadr":          props.get("rdnmadr", ""),
                        "rdnmadr_code":     props.get("rdnmadrcode", ""),
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