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
   ---------------------------------------------------------------- */
const _cfg = JSON.parse(document.getElementById("pageConfig").textContent);

const CSRF = _cfg.csrfToken;
const URLS = {
  upload      : _cfg.uploadUrl,
  imgDelete   : _cfg.imageDeleteBase,
  reviewDelete: _cfg.reviewDeleteBase,
};

/* ----------------------------------------------------------------
   1. axios instance  — JSON 요청 전용 (DELETE)
   ---------------------------------------------------------------- */
const apiClient = axios.create({
  headers: {
    "Content-Type"    : "application/json",
    "Accept"          : "application/json",
    "X-CSRFToken"     : CSRF,
    "X-Requested-With": "XMLHttpRequest",
  },
});

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
   2. 이미지 업로드 / 삭제 요청
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

function deleteImageRequest(imgPk) {
  return apiClient.delete(URLS.imgDelete.replace("/0/", "/" + imgPk + "/"));
}

function deleteReviewRequest(reviewPk) {
  return apiClient.delete(URLS.reviewDelete.replace("/0/", "/" + reviewPk + "/"));
}

/* ----------------------------------------------------------------
   3. UI 유틸
   ---------------------------------------------------------------- */
var UI = {
  feedback: function (el, msg, type) {
    if (!el) return;
    el.textContent = msg;
    el.className   = "upload-feedback " + (type === "error" ? "is-error" : "is-success");
  },
  clearFeedback: function (el) {
    if (!el) return;
    el.textContent = "";
    el.className   = "upload-feedback";
  },
  setProgress: function (barEl, textEl, pct) {
    if (barEl)  barEl.style.width  = pct + "%";
    if (textEl) textEl.textContent = pct + "%";
  },
  setLoading: function (btn, isLoading, label) {
    if (!btn) return;
    label = label || "업로드";
    btn.disabled    = isLoading;
    btn.textContent = isLoading ? "처리 중..." : label;
  },
  validateFile: function (file) {
    var ALLOWED = ["image/jpeg", "image/png", "image/webp", "image/gif"];
    if (ALLOWED.indexOf(file.type) === -1) return "JPG·PNG·WEBP·GIF 형식만 업로드 가능합니다.";
    if (file.size > 5 * 1024 * 1024)       return "파일 크기는 5 MB 이하여야 합니다.";
    return null;
  },

  /* 미리보기 해제: blob URL 정리 + src 제거 + 숨김 */
  previewClear: function (imgEl) {
    if (!imgEl) return;
    if (imgEl.src && imgEl.src.indexOf("blob:") === 0) URL.revokeObjectURL(imgEl.src);
    imgEl.removeAttribute("src");
    imgEl.classList.remove("is-visible");
  },

  /* 미리보기 표시: 이전 blob 해제 후 새 blob 생성 + 파일명 표시 */
  previewShow: function (imgEl, file, nameEl) {
    if (imgEl) {
      if (imgEl.src && imgEl.src.indexOf("blob:") === 0) URL.revokeObjectURL(imgEl.src);
      imgEl.src = URL.createObjectURL(file);
      imgEl.classList.add("is-visible");
    }
    if (nameEl) nameEl.textContent = "📄 " + file.name;
  },
};

/* ----------------------------------------------------------------
   업로드 실행 공통: 성공 시 reload, 실패 시 feedback + 로딩 복구
   ---------------------------------------------------------------- */
function submitUpload(opts) {
  /* opts: { file, caption, submitBtn, feedbackEl, onProgress, onError } */
  UI.setLoading(opts.submitBtn, true);
  UI.clearFeedback(opts.feedbackEl);

  uploadImageRequest(opts.file, opts.caption, true, opts.onProgress)
    .then(function (res) {
      if (res.data && res.data.success) {
        window.location.reload();
      } else {
        throw new Error((res.data && res.data.error) || "업로드 실패");
      }
    })
    .catch(function (err) {
      UI.setLoading(opts.submitBtn, false);
      UI.feedback(opts.feedbackEl, "❌ " + err.message, "error");
      if (typeof opts.onError === "function") opts.onError();
    });
}

/* ----------------------------------------------------------------
   4. [이미지 없을 때] 신규 업로드 패널
   ---------------------------------------------------------------- */
(function initNewUpload() {
  var fileInput  = document.getElementById("newFileInput");
  if (!fileInput) return;

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

  panel.style.display      = "none";
  progressWr.style.display = "none";

  fileInput.addEventListener("change", function () {
    if (!this.files.length) return;
    var err = UI.validateFile(this.files[0]);
    if (err) {
      UI.feedback(feedbackEl, "❌ " + err, "error");
      this.value = "";
      return;
    }
    UI.clearFeedback(feedbackEl);
    UI.previewShow(previewEl, this.files[0], fileNameEl);
    trigger.style.display = "none";
    panel.style.display   = "flex";
  });

  if (cancelBtn) {
    cancelBtn.addEventListener("click", function () {
      panel.style.display      = "none";
      trigger.style.display    = "";
      fileInput.value          = "";
      captionEl.value          = "";
      progressWr.style.display = "none";
      UI.setProgress(progressBr, progressTx, 0);
      UI.clearFeedback(feedbackEl);
      UI.previewClear(previewEl);
    });
  }

  if (submitBtn) {
    submitBtn.addEventListener("click", function () {
      if (!fileInput.files.length) return;
      progressWr.style.display = "block";
      UI.setProgress(progressBr, progressTx, 0);

      submitUpload({
        file       : fileInput.files[0],
        caption    : captionEl.value,
        submitBtn  : submitBtn,
        feedbackEl : feedbackEl,
        onProgress : function (pct) { UI.setProgress(progressBr, progressTx, pct); },
        onError    : function () { progressWr.style.display = "none"; },
      });
    });
  }
})();

/* ----------------------------------------------------------------
   5. [이미지 있을 때] 사진 변경 패널
   ---------------------------------------------------------------- */
(function initChangeUpload() {
  var showBtn = document.getElementById("btnShowChangePanel");
  if (!showBtn) return;

  var closeBtn   = document.getElementById("btnCloseChangePanel");
  var panel      = document.getElementById("changePanel");
  var fileInput  = document.getElementById("changeFileInput");
  var previewEl  = document.getElementById("changePreviewImg");
  var fileNameEl = document.getElementById("changeFileName");
  var captionEl  = document.getElementById("changeCaptionInput");
  var submitBtn  = document.getElementById("btnSubmitChange");
  var feedbackEl = document.getElementById("changeFeedback");

  panel.style.display = "none";

  showBtn.addEventListener("click", function () {
    panel.style.display = "flex";
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", function () {
      panel.style.display    = "none";
      fileInput.value        = "";
      fileNameEl.textContent = "";
      captionEl.value        = "";
      UI.clearFeedback(feedbackEl);
      UI.setLoading(submitBtn, false);
      UI.previewClear(previewEl);
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", function () {
      if (!this.files.length) return;
      var err = UI.validateFile(this.files[0]);
      if (err) {
        UI.feedback(feedbackEl, "❌ " + err, "error");
        this.value = "";
        return;
      }
      UI.previewShow(previewEl, this.files[0], fileNameEl);
      UI.clearFeedback(feedbackEl);
    });
  }

  if (submitBtn) {
    submitBtn.addEventListener("click", function () {
      if (!fileInput || !fileInput.files.length) {
        UI.feedback(feedbackEl, "❌ 파일을 선택해주세요.", "error");
        return;
      }
      submitUpload({
        file      : fileInput.files[0],
        caption   : captionEl.value,
        submitBtn : submitBtn,
        feedbackEl: feedbackEl,
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
      .then(function () { window.location.reload(); })
      .catch(function (err) {
        alert("❌ " + err.message);
        self.disabled = false;
      });
  });
});

/* ----------------------------------------------------------------
   7. 리뷰 삭제 — fade-out 후 카드 제거 + 카운트 갱신
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

        card.style.transition = "opacity .3s, transform .3s";
        card.style.opacity    = "0";
        card.style.transform  = "translateY(-6px)";

        setTimeout(function () {
          card.remove();

          var chip = document.getElementById("reviewCountChip");
          if (!chip) return;
          var n = Math.max(0, parseInt(chip.textContent) - 1);
          chip.textContent = n + "건";

          /* 남은 리뷰 0개 → 미리 숨겨둔 빈 안내 박스 노출 */
          if (n === 0) {
            var noBox = document.getElementById("noReviewBox");
            if (noBox) noBox.hidden = false;
          }
        }, 320);
      })
      .catch(function (err) {
        alert("❌ " + err.message);
        self.disabled = false;
      });
  });
});
