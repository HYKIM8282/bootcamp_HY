
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
  var badge = document.getElementById('selected-badge');
  var badgeText = document.getElementById('selected-name');
  var badgeClose = document.getElementById('badge-close');

  function showBadge(name) {
    if (!badge || !badgeText) return;
    badgeText.textContent = name;
    badge.style.visibility = 'visible';
    badge.style.opacity = '1';
  }

  function hideBadge() {
    if (!badge) return;
    badge.style.visibility = 'hidden';
    badge.style.opacity = '0';

    document.querySelectorAll('.district.active').forEach(function (p) {
      p.classList.remove('active');
    });

    var sel = document.getElementById('district-select');
    if (sel) sel.value = '';
  }

  if (badge) {
    badge.style.visibility = 'hidden';
    badge.style.opacity = '0';
    badge.style.transition = 'opacity .2s';
  }

  if (badgeClose) {
    badgeClose.addEventListener('click', hideBadge);
  }

  function moveToBrokerList(regionName) {
    var url = '/brokers/broker1/?ld_code_nm=' + encodeURIComponent(regionName);
    window.location.href = url;
  }

  // SVG 클릭
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
          if (sel.options[i].value === name) {
            sel.selectedIndex = i;
            break;
          }
        }
      }

      showBadge(name);

      setTimeout(function () {
        moveToBrokerList(name);
      }, 180);
    });
  });

  // 드롭다운 버튼
  var goBtn = document.getElementById('select-go-btn');
  if (goBtn) {
    goBtn.addEventListener('click', function () {
      var sel = document.getElementById('district-select');
      var name = sel && sel.value;
      if (!name) return;

      document.querySelectorAll('.district').forEach(function (p) {
        p.classList.toggle('active', p.dataset.name === name);
      });

      showBadge(name);

      setTimeout(function () {
        moveToBrokerList(name);
      }, 180);
    });
  }
});