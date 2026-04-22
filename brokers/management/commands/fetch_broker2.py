import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

VWORLD_BROKER_URL = settings.BASE_URLS2


# ── 요청 파라미터 ──────────────────────────────────────────────
@dataclass
class EBBrokerRequestParams:
    key: str = field(default_factory=lambda: settings.VWORLD_API_KEY)
    domain: str = field(default_factory=lambda: settings.VWORLD_DOMAIN)  # ✅ 추가
    ld_code: Optional[str] = None
    bsnm_cmpnm: Optional[str] = None
    brkr_nm: Optional[str] = None
    jurirno: Optional[str] = None
    format: str = "json"
    num_of_rows: int = 10
    page_no: int = 1

    def to_query_params(self) -> dict:
        params = {
            "key": self.key,
            "domain": self.domain,     # ✅ 추가
            "format": self.format,
            "numOfRows": self.num_of_rows,
            "pageNo": self.page_no,
        }
        if self.ld_code:
            params["ldCode"] = self.ld_code
        if self.bsnm_cmpnm:
            params["bsnmCmpnm"] = self.bsnm_cmpnm
        if self.brkr_nm:
            params["brkrNm"] = self.brkr_nm
        if self.jurirno:
            params["jurirno"] = self.jurirno
        return params


# ── 응답 데이터 ────────────────────────────────────────────────
@dataclass
class EBBrokerItem:
    """API 응답 단건 항목"""

    ld_code: str = ""
    ld_code_nm: str = ""
    jurirno: str = ""
    bsnm_cmpnm: str = ""
    brkr_nm: str = ""
    brkr_asort_code: str = ""
    brkr_asort_code_nm: str = ""
    crqfc_no: str = ""
    crqfc_acqdt: Optional[date] = None
    ofcps_se_code: str = ""
    ofcps_se_code_nm: str = ""
    last_updt_dt: Optional[date] = None

    @classmethod
    def from_api_dict(cls, data: dict) -> "EBBrokerItem":
        def parse_date(val: Optional[str]) -> Optional[date]:
            if not val:
                return None
            try:
                return date.fromisoformat(val)
            except ValueError:
                logger.warning("날짜 파싱 실패: %s", val)
                return None

        return cls(
            ld_code=data.get("ldCode", ""),
            ld_code_nm=data.get("ldCodeNm", ""),
            jurirno=data.get("jurirno", ""),
            bsnm_cmpnm=data.get("bsnmCmpnm", ""),
            brkr_nm=data.get("brkrNm", ""),
            brkr_asort_code=data.get("brkrAsortCode", ""),
            brkr_asort_code_nm=data.get("brkrAsortCodeNm", ""),
            crqfc_no=data.get("crqfcNo", ""),
            crqfc_acqdt=parse_date(data.get("crqfcAcqdt")),
            ofcps_se_code=data.get("ofcpsSecode", ""),
            ofcps_se_code_nm=data.get("ofcpsSeCodeNm", ""),
            last_updt_dt=parse_date(data.get("lastUpdtDt")),
        )


@dataclass
class EBBrokerResponse:
    """API 전체 응답"""

    total_count: int = 0
    page_no: int = 1
    num_of_rows: int = 10
    items: list[EBBrokerItem] = field(default_factory=list)
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def has_error(self) -> bool:
        return self.error_code is not None


# ── API 클라이언트 ─────────────────────────────────────────────
class EBBrokerAPIClient:
    BASE_URL = VWORLD_BROKER_URL
    TIMEOUT = 10

    def fetch(self, params: EBBrokerRequestParams) -> EBBrokerResponse:
        try:
            resp = requests.get(
                self.BASE_URL,
                params=params.to_query_params(),
                timeout=self.TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error("V-World API 요청 실패: %s", exc)
            return EBBrokerResponse(error_code="REQUEST_FAILED", error_message=str(exc))
        return self._parse(resp.json())  # ← _parse가 같은 클래스 안에 있어야 함

    def fetch_all(self, params: EBBrokerRequestParams) -> list:
        params.page_no = 1
        first = self.fetch(params)
        if first.has_error:
            return []

        all_items = list(first.items)
        total_pages = -(-first.total_count // params.num_of_rows)

        for page in range(2, total_pages + 1):
            params.page_no = page
            result = self.fetch(params)
            if result.has_error:
                break
            all_items.extend(result.items)

        return all_items

    def _parse(self, data: dict) -> EBBrokerResponse:  # ← 들여쓰기 4칸 (클래스 안)
        root = data.get("EDBrokers", {})

        result_code = root.get("resultCode", "")
        if result_code not in ("", "OK"):
            logger.warning("API 에러 응답 [%s]: %s", result_code, root.get("resultMsg"))
            return EBBrokerResponse(
                error_code=result_code,
                error_message=root.get("resultMsg", "알 수 없는 오류"),
            )

        raw_items = root.get("field", [])

        if isinstance(raw_items, dict):
            raw_items = [raw_items]

        items = [EBBrokerItem.from_api_dict(item) for item in raw_items]

        return EBBrokerResponse(
            total_count=int(root.get("totalCount", 0)),
            page_no=int(root.get("pageNo", 1)),
            num_of_rows=int(root.get("numOfRows", 10)),
            items=items,
        )