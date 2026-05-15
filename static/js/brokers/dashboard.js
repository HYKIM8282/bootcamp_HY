
// /**
//  * dashboard.js
//  * 서울시 지도 인터랙션
//  * - SVG 구(district) 클릭 시 broker1_list로 이동
//  * - 해당 구의 중개업소 목록만 필터링
//  */

// document.addEventListener('DOMContentLoaded', function () {

//   var badge      = document.getElementById('selected-badge');
//   var badgeText  = document.getElementById('selected-name');
//   var badgeClose = document.getElementById('badge-close');

//   // ── 뱃지 표시/숨김 ──────────────────────────────────────────
//   function showBadge(name) {
//     if (!badge || !badgeText) return;
//     badgeText.textContent = name;
//     badge.style.visibility = 'visible';
//     badge.style.opacity    = '1';
//   }

//   function hideBadge() {
//     if (!badge) return;
//     badge.style.visibility = 'hidden';
//     badge.style.opacity    = '0';
//     document.querySelectorAll('.district.active').forEach(function (p) {
//       p.classList.remove('active');
//     });
//     var sel = document.getElementById('district-select');
//     if (sel) sel.value = '';
//   }

//   if (badge) {
//     badge.style.visibility = 'hidden';
//     badge.style.opacity    = '0';
//     badge.style.transition = 'opacity .2s';
//   }

//   if (badgeClose) {
//     badgeClose.addEventListener('click', hideBadge);
//   }

//   // ── SVG 구(district) 클릭 ────────────────────────────────────
//   document.querySelectorAll('.district').forEach(function (path) {
//     path.addEventListener('click', function () {
//       var name = this.dataset.name;
//       var code = this.dataset.code;
//       if (!name) return;

//       // 이전 active 제거 후 현재 경로에 active 추가
//       document.querySelectorAll('.district.active').forEach(function (p) {
//         p.classList.remove('active');
//       });
//       this.classList.add('active');

//       // 드롭다운 동기화
//       var sel = document.getElementById('district-select');
//       if (sel) {
//         for (var i = 0; i < sel.options.length; i++) {
//           if (sel.options[i].value === name) { sel.selectedIndex = i; break; }
//         }
//       }

//       showBadge(name);

//       // broker1 목록으로 이동 — ld_code_nm 파라미터로 필터링
//       setTimeout(function () {
//         window.location.href = '/brokers/broker1/?ld_code_nm=' + encodeURIComponent(name);
//       }, 180);
//     });
//   });

//   // ── 드롭다운 "해당 지역 조회" 버튼 ──────────────────────────
//   var goBtn = document.getElementById('select-go-btn');
//   if (goBtn) {
//     goBtn.addEventListener('click', function () {
//       var sel  = document.getElementById('district-select');
//       var name = sel && sel.value;
//       if (!name) return;

//       // SVG 동기화
//       document.querySelectorAll('.district').forEach(function (p) {
//         p.classList.toggle('active', p.dataset.name === name);
//       });
//       showBadge(name);

//       setTimeout(function () {
//         window.location.href = '/brokers/broker1/?ld_code_nm=' + encodeURIComponent(name);
//       }, 180);
//     });
//   }

// });



/**
 * dashboard.js
 * 서울시 지도 인터랙션
 * - SVG 구(district) 클릭 시 broker1_list로 이동
 * - 해당 구의 중개업소 목록만 필터링
 */

document.addEventListener('DOMContentLoaded', function () {
  var badge       = document.getElementById('selected-badge');
  var badgeText   = document.getElementById('selected-name');
  var badgeClose  = document.getElementById('badge-close');
  var dongPanel   = document.getElementById('dongPanel');
  var dongGuName  = document.getElementById('dongPanelGuName');
  var dongBtnWrap = document.getElementById('dongPanelButtons');

  // 매핑 JSON 한 번에 로드 — { "송파구": { "code": "11710", "dongs": [...] }, ... }
  var INFO_BY_GU = {};
  try {
    var dataEl = document.getElementById('info-by-gu');
    if (dataEl) INFO_BY_GU = JSON.parse(dataEl.textContent);
  } catch (e) { /* noop */ }

  function showBadge(name) {
    if (!badge || !badgeText) return;
    badgeText.textContent  = name;
    badge.style.visibility = 'visible';
    badge.style.opacity    = '1';
  }

  function hideBadge() {
    if (!badge) return;
    badge.style.visibility = 'hidden';
    badge.style.opacity    = '0';
    document.querySelectorAll('.district.active').forEach(function (p) {
      p.classList.remove('active');
    });
    if (dongPanel) dongPanel.style.display = 'none';
  }

  if (badge) {
    badge.style.visibility = 'hidden';
    badge.style.opacity    = '0';
    badge.style.transition = 'opacity .2s';
  }
  if (badgeClose) badgeClose.addEventListener('click', hideBadge);

  /* broker1 목록으로 이동
     code  : 시군구코드 (예 "11710") — view 의 `?ldcode=` 와 일치
     gu    : 구 이름 (예 "송파구")
     dong  : 동 이름 (없으면 전체) */
  function moveToBrokerList(code, gu, dong) {
    var params = [];
    if (code) params.push('ldcode=' + encodeURIComponent(code));
    if (gu)   params.push('ld_code_nm=' + encodeURIComponent(gu));
    if (dong) params.push('dong=' + encodeURIComponent(dong));
    window.location.href = '/brokers/broker1/?' + params.join('&');
  }

  /* 구 클릭/선택 시 동 패널 렌더 */
  function showDongPanel(guName) {
    if (!dongPanel || !dongBtnWrap) return;
    var info  = INFO_BY_GU[guName] || { code: '', dongs: [] };
    var dongs = info.dongs || [];
    var code  = info.code  || '';

    dongGuName.textContent = guName;
    dongBtnWrap.innerHTML  = '';

    // "전체" 버튼 — 동 필터 없이 해당 구만
    var allBtn = document.createElement('a');
    allBtn.href        = 'javascript:void(0)';
    allBtn.className   = 'db-dong-btn db-dong-btn--all';
    allBtn.textContent = '전체';
    allBtn.addEventListener('click', function () {
      moveToBrokerList(code, guName, '');
    });
    dongBtnWrap.appendChild(allBtn);

    // 개별 동 버튼들
    dongs.forEach(function (dong) {
      var btn = document.createElement('a');
      btn.href        = 'javascript:void(0)';
      btn.className   = 'db-dong-btn';
      btn.textContent = dong;
      btn.addEventListener('click', function () {
        moveToBrokerList(code, guName, dong);
      });
      dongBtnWrap.appendChild(btn);
    });

    if (dongs.length === 0) {
      var empty = document.createElement('span');
      empty.className   = 'db-dong-empty';
      empty.textContent = '등록된 데이터가 없습니다';
      dongBtnWrap.appendChild(empty);
    }

    dongPanel.style.display = 'block';
  }

  /* SVG 구 클릭 — 이동하지 않고 동 패널만 표시 */
  document.querySelectorAll('.district').forEach(function (path) {
    path.addEventListener('click', function () {
      var name = this.dataset.name;
      if (!name) return;

      document.querySelectorAll('.district.active').forEach(function (p) {
        p.classList.remove('active');
      });
      this.classList.add('active');

      var sel = document.getElementById('district-select');
      if (sel) {
        for (var i = 0; i < sel.options.length; i++) {
          if (sel.options[i].value === name) { sel.selectedIndex = i; break; }
        }
      }

      showBadge(name);
      showDongPanel(name);

      // 패널이 화면 밖이면 자연스럽게 스크롤
      if (dongPanel) dongPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
  });

  /* 드롭다운 버튼 — 동일하게 동 패널 표시 */
  var goBtn = document.getElementById('select-go-btn');
  if (goBtn) {
    goBtn.addEventListener('click', function () {
      var sel  = document.getElementById('district-select');
      var name = sel && sel.value;
      if (!name) return;

      document.querySelectorAll('.district').forEach(function (p) {
        p.classList.toggle('active', p.dataset.name === name);
      });
      showBadge(name);
      showDongPanel(name);
    });
  }
});