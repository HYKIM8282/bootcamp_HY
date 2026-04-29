import os
import time
import requests

from django.core.management.base import BaseCommand
from dotenv import load_dotenv

from brokers.models import RealEstateAgent

load_dotenv()


class Command(BaseCommand):
    help = "DB의 주소를 카카오 API로 좌표(lat/lng)로 변환해 저장합니다."

    def handle(self, *args, **kwargs):
        kakao_rest_key = os.getenv("KAKAO_REST_KEY")

        if not kakao_rest_key:
            self.stdout.write(self.style.ERROR("KAKAO_REST_KEY가 .env에 없습니다."))
            return

        # lat/lng 없는 것만 대상
        agents = RealEstateAgent.objects.filter(lat__isnull=True, rdnmadr__gt="")
        total = agents.count()
        self.stdout.write(f"변환 대상: {total}건")

        success = 0
        fail = 0

        for agent in agents:
            try:
                url = "https://dapi.kakao.com/v2/local/search/address.json"
                headers = {"Authorization": f"KakaoAK {kakao_rest_key}"}
                res = requests.get(url, headers=headers, params={"query": agent.rdnmadr}, timeout=5)
                data = res.json()

                if data.get("documents"):
                    agent.lat = float(data["documents"][0]["y"])
                    agent.lng = float(data["documents"][0]["x"])
                    agent.save(update_fields=["lat", "lng"])
                    success += 1
                    self.stdout.write(self.style.SUCCESS(f"✅ {agent.bsnm_cmpnm}"))
                else:
                    fail += 1
                    self.stdout.write(self.style.WARNING(f"⚠️ 주소 없음: {agent.rdnmadr}"))

            except Exception as e:
                fail += 1
                self.stdout.write(self.style.ERROR(f"❌ 오류: {agent.bsnm_cmpnm} - {e}"))

            time.sleep(0.1)  # API 과호출 방지

        self.stdout.write(self.style.SUCCESS(f"\n[완료] 성공:{success} 실패:{fail}"))