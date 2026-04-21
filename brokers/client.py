import logging
import requests
from django.conf import settings
from .exceptions import VWorldAPIException, parse_vworld_error

logger = logging.getLogger(__name__)


class VWorldSearchClient:
    def __init__(self):
        self.api_key = settings.VWORLD_API_KEY
        self.timeout = getattr(settings, "VWORLD_TIMEOUT", 10)

    def search(self, query, type="PLACE", category="",
               size=10, page=1, bbox="", crs=""):
        params = {
            "service": "search", "version": "2.0", "request": "search",
            "key": self.api_key, "format": "json",
            "query": query, "type": type,
            "size": min(size, 1000), "page": page,
        }
        if category: params["category"] = category
        if bbox:     params["bbox"]     = bbox
        if crs:      params["crs"]      = crs

        resp = requests.get(
            "https://api.vworld.kr/req/search",
            params=params,
            timeout=self.timeout
        )
        resp.raise_for_status()
        data = resp.json()

        err = parse_vworld_error(data)
        if err:
            raise VWorldAPIException(err, raw=data)

        response = data.get("response", {})
        result   = response.get("result", {})
        items    = result.get("items", [])
        return {
            "status": response.get("status", "OK"),
            "total":  int(result.get("totalCount", len(items))),
            "page":   page,
            "items":  items,
        }


class VWorldDataClient:
    def __init__(self):
        self.api_key    = settings.VWORLD_API_KEY
        self.timeout    = getattr(settings, "VWORLD_TIMEOUT", 10)
        self.office_url = getattr(settings, "VWORLD_URL_OFFICE",
                          "https://api.vworld.kr/ned/data/getEBOfficeInfo")
        self.broker_url = getattr(settings, "VWORLD_URL_BROKER",
                          "https://api.vworld.kr/ned/data/getEBBrokerInfo")
    def _call(self, url, params):
        params["key"]    = self.api_key
        params["format"] = "json"
        params["numOfRows"] = params.pop("size", 10)
        params["pageNo"]    = params.pop("page", 1)

        resp = requests.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        # ned API 응답 구조 파싱
        # {"result": {"totalCount": N, "field": [...], "row": [...]}}
        result   = data.get("result", {})
        rows     = result.get("row", [])
        total    = int(result.get("totalCount", len(rows)))

        return {"total": total, "features": rows}

    def get_offices(self, bsnm_cmpnm="", ld_code="",
                    jurirno="", sttus_code="", page=1, size=10):
        """부동산중개업사무소정보조회"""
        params = {"page": page, "size": size}
        if ld_code:    params["ldCode"]      = ld_code
        if jurirno:    params["jurirno"]     = jurirno
        if bsnm_cmpnm: params["bsnmCmpnm"]  = bsnm_cmpnm
        if sttus_code: params["sttusSeCode"] = sttus_code
        return self._call(self.office_url, params)

    def get_brokers(self, brkr_nm="", ld_code="",
                    jurirno="", ofcps_code="", page=1, size=10):
        """부동산중개업자정보조회"""
        params = {"page": page, "size": size}
        if ld_code:    params["ldCode"]      = ld_code
        if jurirno:    params["jurirno"]     = jurirno
        if brkr_nm:    params["brkrNm"]      = brkr_nm
        if ofcps_code: params["ofcpsSeCode"] = ofcps_code
        return self._call(self.broker_url, params)