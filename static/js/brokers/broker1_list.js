/* ══════════════════════════════════════════════════════════════
   broker1_list.js  —  부동산 중개업사무소 목록 페이지 로직
   경로: static/js/broker1_list.js
   
   기능:
   - Kakao Maps 초기화 및 마커 렌더링
   - 주소 기반 지오코딩 큐
   - 드롭다운/행 선택 및 프리뷰
   - 검색 필터링
   ══════════════════════════════════════════════════════════════ */

// ─────────────────────────────────────
// 전역 변수
// ─────────────────────────────────────
var detailBaseUrl  = "/brokers/detail1/";  // 상세 페이지 URL 베이스
var mapAgents      = null;         // 지도용 마커 데이터
var mapAgentsAddr  = null;         // 주소 기반 마커 데이터
var mapInstance    = null;         // Kakao Maps 인스턴스
var mapInitialized = false;        // 지도 초기화 여부
var markerMap      = {};           // 마커 ID 매핑
var openInfoWindow = null;         // 열린 정보 윈도우
var tempMarker     = null;         // 임시 마커


// ─────────────────────────────────────
// DOM 로드 완료 후 실행
// ─────────────────────────────────────
document.addEventListener("DOMContentLoaded", function () {
  // map-data 스크립트 파싱
  var mapDataEl = document.getElementById("map-data");
  if (mapDataEl) {
    mapAgents = JSON.parse(mapDataEl.textContent);
  }

  // map-addr-data 스크립트 파싱
  var mapAddrDataEl = document.getElementById("map-addr-data");
  if (mapAddrDataEl) {
    mapAgentsAddr = JSON.parse(mapAddrDataEl.textContent);
  }

  // 행 클릭 이벤트 등록
  document.querySelectorAll(".al-tr[data-id]").forEach(function (row) {
    var singleClickTimer = null;
    var clickCount = 0;

    function handleClick() {
      clickCount++;
      if (clickCount === 1) {
        singleClickTimer = setTimeout(function () {
          // 단일 클릭: 행 선택
          document.querySelectorAll(".al-tr.selected").forEach(function (r) { r.classList.remove("selected"); });
          row.classList.add("selected");

          // 프리뷰 바 표시
          var previewBar = document.getElementById("preview-bar");
          previewBar.innerHTML = '<div class="pb-inner">' +
            '<span class="pb-title">' + row.querySelector(".al-agent-name").textContent + '</span>' +
            '<span class="pb-addr">' + (row.querySelector(".al-agent-addr")?.textContent || "주소 없음") + '</span>' +
            '<span class="pb-hint">더블클릭으로 상세보기</span>' +
            '</div>';
          previewBar.style.display = "block";

          // 클릭한 행에 포커스
          focusSingleMarker(
            row.dataset.id,
            row.querySelector(".al-agent-addr")?.textContent,
            row.querySelector(".al-agent-name").textContent,
            row.dataset.sttus
          );

          clickCount = 0;
        }, 220);
      } else if (clickCount === 2) {
        clearTimeout(singleClickTimer);
        // 더블 클릭: 상세 페이지로 이동
        window.location.href = detailBaseUrl + row.dataset.id + "/";
        clickCount = 0;
      }
    }

    row.addEventListener("click", handleClick);
  });

  // 드롭다운 선택 이벤트
  document.querySelectorAll(".al-dropdown-item").forEach(function (link) {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      document.getElementById("ldcode").value = this.dataset.code;
      document.getElementById("districtLabel").textContent =
        this.dataset.code ? this.textContent.trim() : "구 선택";
    });
  });

  // URL에 ld_code_nm이 있으면 지도 자동 로드
  if (new URLSearchParams(window.location.search).get("ld_code_nm")) {
    kakao.maps.load(function () { ensureMap(); });
  }
});


// ─────────────────────────────────────
// 지도 표시/숨김 토글
// ─────────────────────────────────────
function toggleMap() {
  var mapDiv = document.getElementById("map");
  if (mapDiv.style.display === "none") {
    mapDiv.style.display = "block";
    if (!mapInitialized) kakao.maps.load(function () { initMap(); });
  } else {
    mapDiv.style.display = "none";
  }
}


// ─────────────────────────────────────
// 지도 보장 초기화
// ─────────────────────────────────────
function ensureMap() {
  document.getElementById("map").style.display = "block";
  if (!mapInitialized) initMap();
}


// ─────────────────────────────────────
// 지도 초기화
// ─────────────────────────────────────
function initMap() {
  mapInstance = new kakao.maps.Map(document.getElementById("map"), {
    center: new kakao.maps.LatLng(37.5665, 126.9780),
    level: 8,
  });
  mapInitialized = true;
  renderAllMarkers();
  if (mapAgentsAddr && mapAgentsAddr.length > 0) geocodeQueue(mapAgentsAddr.slice());
}


// ─────────────────────────────────────
// 정보 윈도우 HTML 생성
// ─────────────────────────────────────
function makeInfoContent(agent) {
  var url    = detailBaseUrl + agent.id + "/";
  var status = agent.sttus_se_code === "1"
    ? '<span style="color:#1A7C5E;font-weight:700;">● 영업중</span>'
    : '<span style="color:#94A3B8;">● 폐업</span>';
  return '<div style="padding:14px 16px;font-family:Pretendard,Noto Sans KR,sans-serif;min-width:220px;">'
    + '<div style="font-size:14px;font-weight:700;color:#0B1D3A;margin-bottom:4px;">' + agent.bsnm_cmpnm + '</div>'
    + '<div style="font-size:12px;color:#7090B8;margin-bottom:6px;">' + (agent.rdnmadr || '주소 없음') + '</div>'
    + '<div style="font-size:12px;margin-bottom:10px;">' + status + '</div>'
    + '<a href="' + url + '" style="display:block;text-align:center;background:#C9952A;color:#fff;'
    + 'border-radius:6px;padding:7px 0;font-size:13px;font-weight:700;text-decoration:none;">상세보기 →</a>'
    + '</div>';
}


// ─────────────────────────────────────
// 마커 생성
// ─────────────────────────────────────
function createMarker(lat, lng, agent) {
  var position = new kakao.maps.LatLng(lat, lng);
  var marker   = new kakao.maps.Marker({ map: mapInstance, position: position, title: agent.bsnm_cmpnm || "" });
  var iw       = new kakao.maps.InfoWindow({ content: makeInfoContent(agent), removable: true });
  kakao.maps.event.addListener(marker, "click", function () {
    if (openInfoWindow) openInfoWindow.close();
    iw.open(mapInstance, marker);
    openInfoWindow = iw;
  });
  markerMap[String(agent.id)] = { agent: agent, marker: marker, iw: iw, position: position };
}


// ─────────────────────────────────────
// 모든 마커 렌더링
// ─────────────────────────────────────
function renderAllMarkers() {
  if (!mapAgents || !mapAgents.length) return;
  var bounds = new kakao.maps.LatLngBounds();
  mapAgents.forEach(function (agent) {
    if (!agent.lat || !agent.lng) return;
    if (!markerMap[String(agent.id)]) createMarker(agent.lat, agent.lng, agent);
    else markerMap[String(agent.id)].marker.setMap(mapInstance);
    bounds.extend(new kakao.maps.LatLng(agent.lat, agent.lng));
  });
  Object.keys(markerMap).forEach(function (id) { markerMap[id].marker.setMap(mapInstance); });
  if (Object.keys(markerMap).length > 0) mapInstance.setBounds(bounds);
}


// ─────────────────────────────────────
// 단일 마커에 포커스
// ─────────────────────────────────────
function focusSingleMarker(agentId, addr, name, sttus) {
  if (openInfoWindow) { openInfoWindow.close(); openInfoWindow = null; }
  if (tempMarker)     { tempMarker.setMap(null); tempMarker = null; }
  Object.keys(markerMap).forEach(function (id) { markerMap[id].marker.setMap(null); });

  if (markerMap[String(agentId)]) {
    var entry = markerMap[String(agentId)];
    entry.marker.setMap(mapInstance);
    mapInstance.setCenter(entry.position);
    mapInstance.setLevel(3);
    entry.iw.open(mapInstance, entry.marker);
    openInfoWindow = entry.iw;
    document.getElementById("pb-finding").style.display = "none";
    return;
  }

  if (!addr || addr === "주소 없음") return;
  document.getElementById("pb-finding").style.display = "inline";
  var statusHtml = sttus === "1"
    ? '<span style="color:#1A7C5E;font-weight:700;">● 영업중</span>'
    : '<span style="color:#94A3B8;">● 폐업</span>';
  var geocoder = new kakao.maps.services.Geocoder();
  geocoder.addressSearch(addr, function (result, status) {
    document.getElementById("pb-finding").style.display = "none";
    if (status !== kakao.maps.services.Status.OK || !result.length) return;
    var pos = new kakao.maps.LatLng(parseFloat(result[0].y), parseFloat(result[0].x));
    mapInstance.setCenter(pos);
    mapInstance.setLevel(3);
    tempMarker = new kakao.maps.Marker({ map: mapInstance, position: pos, title: name });
    var tmpIw = new kakao.maps.InfoWindow({
      content: '<div style="padding:14px 16px;font-family:Pretendard,Noto Sans KR,sans-serif;min-width:200px;">'
             + '<div style="font-size:14px;font-weight:700;color:#0B1D3A;margin-bottom:4px;">' + name + '</div>'
             + '<div style="font-size:12px;color:#7090B8;margin-bottom:6px;">' + addr + '</div>'
             + '<div style="font-size:12px;">' + statusHtml + '</div></div>',
      removable: true,
    });
    tmpIw.open(mapInstance, tempMarker);
    openInfoWindow = tmpIw;
  });
}


// ─────────────────────────────────────
// 모든 마커 표시
// ─────────────────────────────────────
function showAllMarkers() {
  if (!mapInitialized) return;
  if (openInfoWindow) { openInfoWindow.close(); openInfoWindow = null; }
  if (tempMarker) { tempMarker.setMap(null); tempMarker = null; }
  renderAllMarkers();
  document.getElementById("btn-show-all").style.display = "none";
}


// ─────────────────────────────────────
// 프리뷰 닫기
// ─────────────────────────────────────
function closePreview() {
  document.getElementById("preview-bar").style.display = "none";
  document.getElementById("btn-show-all").style.display = "none";
  document.getElementById("map").classList.remove("map-expanded");
  document.querySelectorAll(".al-tr.selected").forEach(function (r) { r.classList.remove("selected"); });
  if (openInfoWindow) { openInfoWindow.close(); openInfoWindow = null; }
  if (tempMarker) { tempMarker.setMap(null); tempMarker = null; }
  if (mapInitialized) renderAllMarkers();
}


// ─────────────────────────────────────
// 주소 기반 지오코딩 큐
// ─────────────────────────────────────
function geocodeQueue(queue) {
  var total      = queue.length;
  var statusDiv  = document.getElementById("geocode-status");
  var progressEl = document.getElementById("geocode-progress");
  statusDiv.style.display = "flex";
  function processBatch(remaining) {
    if (!remaining || remaining.length === 0) { statusDiv.style.display = "none"; return; }
    var batch    = remaining.splice(0, 5);
    var geocoder = new kakao.maps.services.Geocoder();
    var done     = 0;
    batch.forEach(function (agent) {
      if (!agent.rdnmadr) { done++; return; }
      geocoder.addressSearch(agent.rdnmadr, function (result, status) {
        if (status === kakao.maps.services.Status.OK && result.length > 0) {
          createMarker(parseFloat(result[0].y), parseFloat(result[0].x), agent);
        }
        done++;
        if (done === batch.length) {
          progressEl.textContent = "(" + (total - remaining.length) + " / " + total + ")";
          setTimeout(function () { processBatch(remaining); }, 400);
        }
      });
    });
  }
  processBatch(queue);
}
