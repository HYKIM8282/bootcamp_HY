/**
 * broker_detail.js
 * 경로: static/js/brokers/broker_detail.js
 *
 * 이미지 업로드  →  axios.post  +  FormData  (multipart)
 * 이미지 삭제    →  apiClient   (axios instance, JSON DELETE)
 * 리뷰 삭제      →  apiClient   (axios instance, JSON DELETE)
 */

/* ----------------------------------------------------------------
   0. 설정값 로드
   broker_detail.html 이 <script id="pageConfig" type="application/json">
   으로 주입한 값을 JSON.parse 로 읽어옴
   → JS 파일에 Django 템플릿 태그 없이 완전 분리 가능
   ---------------------------------------------------------------- */
const _cfg = JSON.parse(document.getElementById("pageConfig").textContent);

const CSRF = _cfg.csrfToken;
const URLS = {
  upload      : _cfg.uploadUrl,       // POST   이미지 업로드
  imgDelete   : _cfg.imageDeleteBase, // DELETE /brokers/images/0/delete/ → 0 을 pk 로 교체
  reviewDelete: _cfg.reviewDeleteBase,// DELETE /reviews/0/delete/        → 0 을 pk 로 교체
};

/* ----------------------------------------------------------------
   1. axios instance  — JSON 요청 전용 (DELETE)
      Content-Type: application/json 고정
      이미지 업로드(multipart)는 이 인스턴스 사용 안 함
   ---------------------------------------------------------------- */
const apiClient = axios.create({
  headers: {
    "Content-Type"    : "application/json",
    "Accept"          : "application/json",
    "X-CSRFToken"     : CSRF,
    "X-Requested-With": "XMLHttpRequest",
  },
});

/* 응답 인터셉터: success:false 를 200 으로 내려도 에러로 전환 */
apiClient.interceptors.response.use(
  function (res) {
    if (res.data && res.data.success === false) {
      return Promise.reject(new Error(res.data.error || "서버 오류"));
    }
    return res;
  },
  function (err) {
    const msg =
      (err.response && err.response.data && err.response.data.error) ||
      err.message ||
      "알 수 없는 오류";
    return Promise.reject(new Error(msg));
  }
);

/* ----------------------------------------------------------------
   2. 이미지 업로드 함수 — FormData + axios.post
      ★ Content-Type 직접 지정 금지
        axios 가 FormData 감지 시 자동으로
        'multipart/form-data; boundary=...' 를 설정함
   ---------------------------------------------------------------- */
function uploadImageRequest(file, caption, isPrimary, onProgress) {
  const fd = new FormData();
  fd.append("image",               file);
  fd.append("caption",             caption || "");
  fd.append("is_primary",          isPrimary ? "true" : "false");
  fd.append("csrfmiddlewaretoken", CSRF);

  return axios.post(URLS.upload, fd, {
    headers: {
      "X-CSRFToken"     : CSRF,
      "X-Requested-With": "XMLHttpRequest",
      "Accept"          : "application/json",
      /* Content-Type 지정 금지 — FormData 일 때 axios 가 자동 설정 */
    },
    onUploadProgress: function (evt) {
      if (evt.total && typeof onProgress === "function") {
        onProgress(Math.round((evt.loaded / evt.total) * 100));
      }
    },
  });
}

/* 이미지 삭제 — apiClient JSON DELETE */
function deleteImageRequest(imgPk) {
  const url = URLS.imgDelete.replace("/0/", "/" + imgPk + "/");
  return apiClient.delete(url);
}

/* 리뷰 삭제 — apiClient JSON DELETE */
function deleteReviewRequest(reviewPk) {
  const url = URLS.reviewDelete.replace("/0/", "/" + reviewPk + "/");
  return apiClient.delete(url);
}

/* ----------------------------------------------------------------
   3. UI 유틸
   ---------------------------------------------------------------- */
var UI = {
  /** 피드백 메시지 표시 */
  feedback: function (el, msg, type) {
    if (!el) return;
    el.textContent = msg;
    el.className   = "upload-feedback " + (type === "error" ? "is-error" : "is-success");
  },
  /** 피드백 초기화 */
  clearFeedback: function (el) {
    if (!el) return;
    el.textContent = "";
    el.className   = "upload-feedback";
  },
  /** 진행 바 업데이트 */
  setProgress: function (barEl, textEl, pct) {
    if (barEl)  barEl.style.width  = pct + "%";
    if (textEl) textEl.textContent = pct + "%";
  },
  /** 버튼 로딩 상태 */
  setLoading: function (btn, isLoading, label) {
    if (!btn) return;
    label = label || "업로드";
    btn.disabled    = isLoading;
    btn.textContent = isLoading ? "처리 중..." : label;
  },
  /** 파일 유효성 검사 */
  validateFile: function (file) {
    var ALLOWED = ["image/jpeg", "image/png", "image/webp", "image/gif"];
    if (ALLOWED.indexOf(file.type) === -1) return "JPG·PNG·WEBP·GIF 형식만 업로드 가능합니다.";
    if (file.size > 5 * 1024 * 1024)       return "파일 크기는 5 MB 이하여야 합니다.";
    return null;
  },
};

/* ----------------------------------------------------------------
   4. [이미지 없을 때] 신규 업로드 패널
   ---------------------------------------------------------------- */
(function initNewUpload() {
  var fileInput  = document.getElementById("newFileInput");
  if (!fileInput) return; // 이미지 있는 페이지엔 이 요소가 없음

  var trigger    = document.getElementById("newUploadTrigger");
  var panel      = document.getElementById("newUploadPanel");
  var previewEl  = document.getElementById("newPreviewImg");
  var fileNameEl = document.getElementById("newFileName");
  var progressWr = document.getElementById("newProgressWrap");
  var progressBr = document.getElementById("newProgressBar");
  var progressTx = document.getElementById("newProgressText");
  var captionEl  = document.getElementById("newCaptionInput");
  var submitBtn  = document.getElementById("btnSubmitNew");
  var cancelBtn  = document.getElementById("btnCancelNew");
  var feedbackEl = document.getElementById("newFeedback");

  /* 초기 상태 숨김 */
  panel.style.display      = "none";
  progressWr.style.display = "none";

  /* 파일 선택 */
  fileInput.addEventListener("change", function () {
    if (!this.files.length) return;
    var err = UI.validateFile(this.files[0]);
    if (err) {
      UI.feedback(feedbackEl, "❌ " + err, "error");
      this.value = "";
      return;
    }
    UI.clearFeedback(feedbackEl);
    if (previewEl) {
      if (previewEl.src && previewEl.src.indexOf("blob:") === 0) URL.revokeObjectURL(previewEl.src);
      previewEl.src = URL.createObjectURL(this.files[0]);
      previewEl.classList.add("is-visible");
    }
    fileNameEl.textContent = "📄 " + this.files[0].name;
    trigger.style.display  = "none";
    panel.style.display    = "flex";
  });

  /* 취소 */
  if (cancelBtn) {
    cancelBtn.addEventListener("click", function () {
      panel.style.display      = "none";
      trigger.style.display    = "";
      fileInput.value          = "";
      captionEl.value          = "";
      progressWr.style.display = "none";
      UI.setProgress(progressBr, progressTx, 0);
      UI.clearFeedback(feedbackEl);
      if (previewEl) {
        if (previewEl.src && previewEl.src.indexOf("blob:") === 0) URL.revokeObjectURL(previewEl.src);
        previewEl.removeAttribute("src");
        previewEl.classList.remove("is-visible");
      }
    });
  }

  /* 업로드 */
  if (submitBtn) {
    submitBtn.addEventListener("click", function () {
      if (!fileInput.files.length) return;

      UI.setLoading(submitBtn, true);
      UI.clearFeedback(feedbackEl);
      progressWr.style.display = "block";
      UI.setProgress(progressBr, progressTx, 0);

      uploadImageRequest(
        fileInput.files[0],
        captionEl.value,
        true,
        function (pct) { UI.setProgress(progressBr, progressTx, pct); }
      )
        .then(function (res) {
          if (res.data && res.data.success) {
            window.location.reload();
          } else {
            throw new Error((res.data && res.data.error) || "업로드 실패");
          }
        })
        .catch(function (err) {
          UI.setLoading(submitBtn, false);
          UI.feedback(feedbackEl, "❌ " + err.message, "error");
          progressWr.style.display = "none";
        });
    });
  }
})();

/* ----------------------------------------------------------------
   5. [이미지 있을 때] 사진 변경 패널
   ---------------------------------------------------------------- */
(function initChangeUpload() {
  var showBtn = document.getElementById("btnShowChangePanel");
  if (!showBtn) return; // 이미지 없는 페이지엔 이 요소가 없음

  var closeBtn   = document.getElementById("btnCloseChangePanel");
  var panel      = document.getElementById("changePanel");
  var fileInput  = document.getElementById("changeFileInput");
  var previewEl  = document.getElementById("changePreviewImg");
  var fileNameEl = document.getElementById("changeFileName");
  var captionEl  = document.getElementById("changeCaptionInput");
  var submitBtn  = document.getElementById("btnSubmitChange");
  var feedbackEl = document.getElementById("changeFeedback");

  panel.style.display = "none";

  /* 패널 열기 */
  showBtn.addEventListener("click", function () {
    panel.style.display = "flex";
  });

  /* 패널 닫기 */
  if (closeBtn) {
    closeBtn.addEventListener("click", function () {
      panel.style.display    = "none";
      fileInput.value        = "";
      fileNameEl.textContent = "";
      captionEl.value        = "";
      UI.clearFeedback(feedbackEl);
      UI.setLoading(submitBtn, false);
      if (previewEl) {
        if (previewEl.src && previewEl.src.indexOf("blob:") === 0) URL.revokeObjectURL(previewEl.src);
        previewEl.removeAttribute("src");
        previewEl.classList.remove("is-visible");
      }
    });
  }

  /* 파일 선택 */
  if (fileInput) {
    fileInput.addEventListener("change", function () {
      if (!this.files.length) return;
      var err = UI.validateFile(this.files[0]);
      if (err) {
        UI.feedback(feedbackEl, "❌ " + err, "error");
        this.value = "";
        return;
      }
      if (previewEl) {
        if (previewEl.src && previewEl.src.indexOf("blob:") === 0) URL.revokeObjectURL(previewEl.src);
        previewEl.src = URL.createObjectURL(this.files[0]);
        previewEl.classList.add("is-visible");
      }
      fileNameEl.textContent = "📄 " + this.files[0].name;
      UI.clearFeedback(feedbackEl);
    });
  }

  /* 업로드 */
  if (submitBtn) {
    submitBtn.addEventListener("click", function () {
      if (!fileInput || !fileInput.files.length) {
        UI.feedback(feedbackEl, "❌ 파일을 선택해주세요.", "error");
        return;
      }
      UI.setLoading(submitBtn, true);
      UI.clearFeedback(feedbackEl);

      uploadImageRequest(fileInput.files[0], captionEl.value, true, null)
        .then(function (res) {
          if (res.data && res.data.success) {
            window.location.reload();
          } else {
            throw new Error((res.data && res.data.error) || "업로드 실패");
          }
        })
        .catch(function (err) {
          UI.setLoading(submitBtn, false);
          UI.feedback(feedbackEl, "❌ " + err.message, "error");
        });
    });
  }
})();

/* ----------------------------------------------------------------
   6. 이미지 삭제 — apiClient JSON DELETE
   ---------------------------------------------------------------- */
document.querySelectorAll(".btn-img-delete").forEach(function (btn) {
  btn.addEventListener("click", function () {
    var pk = this.dataset.imgPk;
    if (!pk || !confirm("이 사진을 삭제할까요?")) return;

    this.disabled = true;
    var self = this;

    deleteImageRequest(pk)
      .then(function () {
        window.location.reload();
      })
      .catch(function (err) {
        alert("❌ " + err.message);
        self.disabled = false;
      });
  });
});

/* ----------------------------------------------------------------
   7. 리뷰 삭제 — apiClient JSON DELETE
      성공 시 해당 카드만 DOM 에서 fade-out 후 제거
      (페이지 새로고침 없음)
   ---------------------------------------------------------------- */
document.querySelectorAll(".btn-review-delete").forEach(function (btn) {
  btn.addEventListener("click", function () {
    var pk = this.dataset.reviewPk;
    if (!pk || !confirm("리뷰를 삭제하시겠습니까?")) return;

    this.disabled = true;
    var self = this;

    deleteReviewRequest(pk)
      .then(function () {
        var card = document.getElementById("review-" + pk);
        if (!card) return;

        /* fade-out 애니메이션 후 카드 제거 */
        card.style.transition = "opacity .3s, transform .3s";
        card.style.opacity    = "0";
        card.style.transform  = "translateY(-6px)";

        setTimeout(function () {
          card.remove();

          /* 리뷰 카운트 칩 숫자 갱신 */
          var chip = document.getElementById("reviewCountChip");
          if (!chip) return;
          var n = Math.max(0, parseInt(chip.textContent) - 1);
          chip.textContent = n + "건";

          /* 남은 리뷰 0개 → 빈 안내 박스 표시 */
          if (n === 0) {
            var list = document.getElementById("reviewList");
            if (list) {
              list.innerHTML =
                '<div class="no-review" id="noReviewBox">' +
                '<span class="icon">💬</span>' +
                '<p class="mb-0 fw-semibold">아직 등록된 후기가 없습니다</p>' +
                '<p class="small mt-1">첫 번째 후기를 작성해보세요!</p>' +
                '</div>';
            }
          }
        }, 320);
      })
      .catch(function (err) {
        alert("❌ " + err.message);
        self.disabled = false;
      });
  });
});
