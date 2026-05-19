/**
 * pocket_menu.js
 * 경로 : static/js/community/pocket_menu.js
 *
 * - 데이터 송수신 : JSON 전용 (form 태그 사용 X)
 * - 통신 : axios 인스턴스 (apiClient) — Content-Type: application/json
 *
 * 엔드포인트
 *   GET    /community/posts/                  → 목록
 *   POST   /community/posts/                  → 작성
 *   DELETE /community/posts/<pk>/delete/      → 삭제
 */
(function () {
  "use strict";

  /* ── 0. 설정값 로드 ────────────────────────────────── */
  var _cfgEl = document.getElementById("pktConfig");
  if (!_cfgEl) return;
  var CFG;
  try { CFG = JSON.parse(_cfgEl.textContent); }
  catch (e) { console.error("[pkt] pktConfig parse 실패", e); return; }

  /* ── 1. axios 인스턴스 ─────────────────────────────── */
  if (typeof axios === "undefined") {
    console.error("[pkt] axios 미로드 — broker1_list.html 의 extra_js 에 axios 가 포함됐는지 확인");
    return;
  }
  var apiClient = axios.create({
    headers: {
      "Content-Type":     "application/json",
      "Accept":           "application/json",
      "X-CSRFToken":      CFG.csrfToken,
      "X-Requested-With": "XMLHttpRequest",
    },
  });

  // 응답 인터셉터 — success:false 200 응답도 에러로 변환
  apiClient.interceptors.response.use(
    function (res) {
      if (res.data && res.data.success === false) {
        return Promise.reject(new Error(res.data.error || "서버 오류"));
      }
      return res;
    },
    function (err) {
      var msg =
        (err.response && err.response.data && err.response.data.error) ||
        err.message || "알 수 없는 오류";
      return Promise.reject(new Error(msg));
    }
  );

  /* ── 2. DOM 캐시 ──────────────────────────────────── */
  function $(id) { return document.getElementById(id); }

  var handle    = $("pktHandle");
  var panel     = $("pktPanel");
  var closeBtn  = $("pktClose");
  var listEl    = $("pktList");
  var loadingEl = $("pktLoading");
  var moreBtn   = $("pktMoreBtn");
  var writeBtn  = $("pktWriteBtn");
  var modal     = $("pktModal");
  var submitBtn = $("pktSubmitBtn");
  var inputTitle    = $("pktInputTitle");
  var inputCategory = $("pktInputCategory");
  var inputContent  = $("pktInputContent");
  var feedbackEl    = $("pktFeedback");
  var searchInput   = $("pktSearchInput");
  var searchBtn     = $("pktSearchBtn");

  if (!panel || !handle) return;

  /* ── 3. 상태 ─────────────────────────────────────── */
  var state = {
    page:     1,
    category: "",
    keyword:  "",
    loaded:   false,
  };

  /* ── 4. 패널 / 모달 열고 닫기 ─────────────────────── */
  function openPanel() {
    panel.classList.add("is-open");
    panel.setAttribute("aria-hidden", "false");
    handle.setAttribute("aria-expanded", "true");
    document.body.classList.add("pkt-open");
    if (!state.loaded) { fetchPosts(true); }   // 첫 오픈 시 1회 로드
  }
  function closePanel() {
    panel.classList.remove("is-open");
    panel.setAttribute("aria-hidden", "true");
    handle.setAttribute("aria-expanded", "false");
    document.body.classList.remove("pkt-open");
  }
  function togglePanel() {
    panel.classList.contains("is-open") ? closePanel() : openPanel();
  }

  function openModal() {
    if (!CFG.isAuthenticated) {
      alert("로그인 후 글을 작성할 수 있습니다.");
      window.location.href = "/accounts/login/?next=" + encodeURIComponent(window.location.pathname);
      return;
    }
    if (!modal) return;
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    if (feedbackEl) { feedbackEl.textContent = ""; feedbackEl.className = "pkt-feedback"; }
    setTimeout(function () { inputTitle && inputTitle.focus(); }, 50);
  }
  function closeModal() {
    if (!modal) return;
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    if (inputTitle)    inputTitle.value = "";
    if (inputContent)  inputContent.value = "";
    if (inputCategory) inputCategory.value = "latest";
  }

  handle.addEventListener("click", togglePanel);
  if (closeBtn) closeBtn.addEventListener("click", closePanel);
  if (writeBtn) writeBtn.addEventListener("click", openModal);
  if (modal) {
    modal.querySelectorAll("[data-pkt-close]").forEach(function (el) {
      el.addEventListener("click", closeModal);
    });
  }
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    if (modal && modal.classList.contains("is-open"))      closeModal();
    else if (panel.classList.contains("is-open"))          closePanel();
  });

  /* ── 5. 탭 / 검색 ─────────────────────────────────── */
  document.querySelectorAll(".pkt-tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      document.querySelectorAll(".pkt-tab").forEach(function (t) { t.classList.remove("is-active"); });
      tab.classList.add("is-active");
      state.category = tab.dataset.category || "";
      state.page     = 1;
      fetchPosts(true);
    });
  });
  if (searchBtn) {
    searchBtn.addEventListener("click", function () {
      state.keyword = (searchInput && searchInput.value || "").trim();
      state.page    = 1;
      fetchPosts(true);
    });
  }
  if (searchInput) {
    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); searchBtn.click(); }
    });
  }

  /* ── 6. 카드 한 개 렌더 ──────────────────────────── */
  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function renderPost(p) {
    var canDelete = CFG.currentUser && (CFG.currentUser === p.author_name);
    var html = ''
      + '<article class="pkt-post" data-id="' + p.id + '">'
      +   '<header class="pkt-post__head">'
      +     '<span class="pkt-post__cat">'  + escapeHtml(p.category_display) + ' · ' + escapeHtml(p.author_name) + '</span>'
      +     '<span class="pkt-post__time">' + escapeHtml(p.time_ago)         + '</span>'
      +   '</header>'
      +   '<h3 class="pkt-post__title">'    + escapeHtml(p.title)            + '</h3>'
      +   '<p class="pkt-post__body">'      + escapeHtml(p.content)          + '</p>'
      +   '<footer class="pkt-post__foot">'
      +     '<span class="pkt-post__stat">❤ ' + p.like_count + '</span>'
      +     '<span class="pkt-post__stat">👁 ' + p.view_count + '</span>'
      +     (canDelete
            ? '<button type="button" class="pkt-post__delete" data-id="' + p.id + '">삭제</button>'
            : '')
      +   '</footer>'
      + '</article>';
    return html;
  }

  function bindDeleteButtons() {
    listEl.querySelectorAll(".pkt-post__delete").forEach(function (btn) {
      if (btn.dataset.bound === "1") return;
      btn.dataset.bound = "1";
      btn.addEventListener("click", function () {
        if (!confirm("이 글을 삭제할까요?")) return;
        var pk = this.dataset.id;
        var url = CFG.deleteUrlBase.replace("/0/", "/" + pk + "/");
        apiClient.delete(url)
          .then(function () {
            var card = listEl.querySelector('.pkt-post[data-id="' + pk + '"]');
            if (card) card.remove();
          })
          .catch(function (err) {
            alert("❌ " + err.message);
          });
      });
    });
  }

  /* ── 7. 목록 fetch ────────────────────────────────── */
  function fetchPosts(replace) {
    if (replace) {
      listEl.innerHTML = '<div class="pkt-empty">불러오는 중…</div>';
    }

    var params = { page: state.page };
    if (state.category) params.category = state.category;

    apiClient.get(CFG.listUrl, { params: params })
      .then(function (res) {
        var d = res.data || {};
        // PostViewSet 응답 형식: { success, data: [...], meta: { total, page, page_size, has_next } }
        // 옛 호환(results / has_next) 도 fallback 으로 받음
        var rows    = d.data || d.results || [];
        var hasNext = (d.meta && d.meta.has_next) || d.has_next || false;

        var items = rows.filter(function (p) {
          if (!state.keyword) return true;
          var kw = state.keyword.toLowerCase();
          return (p.title || "").toLowerCase().indexOf(kw)   !== -1
              || (p.content || "").toLowerCase().indexOf(kw) !== -1;
        });

        var html = items.map(renderPost).join("");
        if (replace) {
          listEl.innerHTML = html || '<div class="pkt-empty">등록된 글이 없습니다.</div>';
        } else {
          // 첫 페이지 placeholder 가 있다면 제거
          var loading = listEl.querySelector(".pkt-empty");
          if (loading) loading.remove();
          listEl.insertAdjacentHTML("beforeend", html);
        }
        bindDeleteButtons();

        if (moreBtn) moreBtn.style.display = hasNext ? "" : "none";
        state.loaded = true;
      })
      .catch(function (err) {
        listEl.innerHTML = '<div class="pkt-empty pkt-empty--error">❌ ' + escapeHtml(err.message) + '</div>';
      });
  }

  /* ── 8. 더보기 ────────────────────────────────────── */
  if (moreBtn) {
    moreBtn.addEventListener("click", function () {
      state.page += 1;
      fetchPosts(false);
    });
  }

  /* ── 9. 글 작성 (JSON POST) ───────────────────────── */
  function setFeedback(msg, type) {
    if (!feedbackEl) return;
    feedbackEl.textContent = msg || "";
    feedbackEl.className   = "pkt-feedback " + (type ? "pkt-feedback--" + type : "");
  }

  if (submitBtn) {
    submitBtn.addEventListener("click", function () {
      var title    = (inputTitle    && inputTitle.value    || "").trim();
      var content  = (inputContent  && inputContent.value  || "").trim();
      var category = (inputCategory && inputCategory.value || "latest").trim();

      if (!title)   { setFeedback("제목을 입력해주세요.", "error"); return; }
      if (!content) { setFeedback("내용을 입력해주세요.", "error"); return; }

      submitBtn.disabled    = true;
      submitBtn.textContent = "등록 중…";
      setFeedback("", "");

      // ★ form 태그 없이 — 순수 JSON 바디
      var payload = { title: title, content: content, category: category };

      apiClient.post(CFG.createUrl, payload)
        .then(function (res) {
          var newPost = res.data && res.data.post;
          if (newPost) {
            // 새 글이 현재 카테고리 필터와 맞으면 최상단에 즉시 추가
            if (!state.category || state.category === newPost.category) {
              // "등록된 글이 없습니다" placeholder 제거
              var empty = listEl.querySelector(".pkt-empty");
              if (empty) empty.remove();
              listEl.insertAdjacentHTML("afterbegin", renderPost(newPost));
              bindDeleteButtons();
            }
          }
          closeModal();
        })
        .catch(function (err) {
          setFeedback("❌ " + err.message, "error");
        })
        .finally(function () {
          submitBtn.disabled    = false;
          submitBtn.textContent = "등록";
        });
    });
  }
})();
