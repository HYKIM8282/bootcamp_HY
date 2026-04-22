import os
import time
import requests

from django.core.management.base import BaseCommand
from django.db import transaction
from dotenv import load_dotenv

from brokers.models import RealEstateAgent

load_dotenv()

BASE_URLS = "https://api.vworld.kr/ned/data/getEBOfficeInfo"



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

    def handle(self, *args, **options):
        api_key = os.getenv("VWORLD_API_KEY")
        domain  = os.getenv("VWORLD_DOMAIN", "http://localhost:8000")

        if not api_key:
            self.stdout.write(self.style.ERROR("VWORLD_API_KEY가 .env에 없습니다."))
            return

        ldcode    = options["ldcode"]
        page      = options["page"]
        size      = options["size"]
        all_pages = options["all_pages"]

        self.stdout.write(
            f"[설정] ldcode={ldcode}, page={page}, size={size}, all_pages={all_pages}"
        )

        total_created = 0
        total_updated = 0
        total_skipped = 0

        while True:
            self.stdout.write(f"\n[요청] page={page}")

            # NED API 파라미터 (현재 모델과 1:1 대응)
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

            if isinstance(fields, dict):   # 1건이면 dict → list 통일
                fields = [fields]

            if not fields:
                self.stdout.write(self.style.WARNING("데이터 없음. 수집 종료."))
                break

            self.stdout.write(f"  수신: {len(fields)}건 / 전체: {total_count}건")

            # ── DB 저장 ───────────────────────────────────────────
            created_count = updated_count = skipped_count = 0

            with transaction.atomic():
                for props in fields:
                    jurirno = props.get("jurirno", "").strip()

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
                            "regist_de":        props.get("registDe")     or None,
                            "estbs_begin_de":   props.get("estbsBeginDe") or None,
                            "estbs_end_de":     props.get("estbsEndDe")   or None,
                            "last_updt_dt":     props.get("lastUpdtDt")   or None,
                            "mnnmadr":          props.get("mnnmadr", ""),
                            "rdnmadr":          props.get("rdnmadr", ""),
                            "rdnmadr_code": props.get("rdnmadrcode", ""),# 양쪽 키 이름 모두 대응 (API 실제 응답 확인 전까지)
                            
                        },
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

            total_created += created_count
            total_updated += updated_count
            total_skipped += skipped_count

            self.stdout.write(
                self.style.SUCCESS(
                    f"  page {page} 완료 - "
                    f"생성:{created_count} 수정:{updated_count} 건너뜀:{skipped_count}"
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
        self.stdout.write(
            self.style.SUCCESS(
                f"\n[완료] 전체 - "
                f"생성:{total_created} 수정:{total_updated} 건너뜀:{total_skipped}"
            )
        )