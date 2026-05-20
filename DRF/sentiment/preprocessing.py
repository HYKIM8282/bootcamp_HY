# ─────────────────────────────────────────────────────────
# preprocessing.py: 감정분석 전처리 파이프라인
# ─────────────────────────────────────────────────────────
# 역할: 원본 텍스트 → 노이즈 제거 → 슬랭 변환 → 분석 가능한 형태
# 영향: 바뀌면 sentiment/analyzers/keyword.py 의 입력이 바뀜
# 주의: stdlib 만 사용 (re). 외부 의존성(soynlp/kiwipiepy/kss)은
#       향후 advanced_preprocess() 에 분리해서 추가 예정
# ─────────────────────────────────────────────────────────

import re

from .lexicons import SLANG_MAP, ABBREV_MAP


# 공백 정리 + URL/전화번호 패턴 제거
_RE_URL = re.compile(r"https?://\S+|www\.\S+")
_RE_PHONE = re.compile(r"\d{2,3}-\d{3,4}-\d{4}")
_RE_REPEAT_CHAR = re.compile(r"(.)\1{2,}")  # 같은 글자 3번 이상 → 2번으로
_RE_MULTI_SPACE = re.compile(r"\s+")


# ─────────────────────────────────────────────────────────
# 노이즈 제거: URL/전화번호/특수문자/반복문자 정리
# ─────────────────────────────────────────────────────────
# 영향: clean_noise() 호출하는 모든 곳
# 주의: 한글/숫자/문장부호(!?.,)는 보존
def clean_noise(text: str) -> str:
    if not text:
        return ""
    text = _RE_URL.sub(" ", text)
    text = _RE_PHONE.sub(" ", text)
    # 한글, 영문, 숫자, 기본 문장부호만 남김
    text = re.sub(r"[^\w\sㄱ-ㅎㅏ-ㅣ가-힣!?.,]", " ", text)
    # "좋아아아아아아" → "좋아아"
    text = _RE_REPEAT_CHAR.sub(r"\1\1", text)
    # 다중 공백 → 단일 공백
    text = _RE_MULTI_SPACE.sub(" ", text)
    return text.strip()


# ─────────────────────────────────────────────────────────
# 슬랭/약어 풀어쓰기
# ─────────────────────────────────────────────────────────
# 영향: keyword 매칭 정확도 (특히 부동산 슬랭)
# 주의: 긴 단어부터 치환 (짧은 단어가 긴 단어 안에 있을 때 잘못 매칭 방지)
def expand_slang(text: str) -> str:
    if not text:
        return ""
    # 긴 키부터 정렬해서 치환
    for key in sorted(SLANG_MAP.keys(), key=len, reverse=True):
        if key in text:
            text = text.replace(key, SLANG_MAP[key])
    for key in sorted(ABBREV_MAP.keys(), key=len, reverse=True):
        if key in text:
            text = text.replace(key, ABBREV_MAP[key])
    return text


# ─────────────────────────────────────────────────────────
# 전체 전처리 파이프라인 (현재 버전)
# ─────────────────────────────────────────────────────────
# 역할: 원본 → 분석기로 넘기기 직전 상태로 정리
# 영향: sentiment/analyzers/keyword.py 가 이 함수를 호출
# 주의: 순서 중요 (노이즈 제거 → 슬랭 풀기). 형태소 분석은 다음 단계
def preprocess(text: str) -> str:
    text = clean_noise(text)
    text = expand_slang(text)
    return text


# ─────────────────────────────────────────────────────────
# 문장 분할 (간이 버전)
# ─────────────────────────────────────────────────────────
# 역할: 긴 글을 문장 단위로 쪼개 측면별 분석 준비
# 영향: 향후 ABSA(측면별 감정분석) 도입 시 사용
# 주의: 간이 버전 — 정교한 분할은 kss 라이브러리 도입 후 교체 예정
def split_sentences(text: str) -> list[str]:
    if not text:
        return []
    # "3.5점" 같은 케이스 보호: 숫자.숫자는 분할 X
    # 일단 간이로 ., !, ? + 공백/끝 기준 분할
    parts = re.split(r"(?<![\d])[.!?]+\s*", text)
    return [p.strip() for p in parts if p.strip()]


# ─────────────────────────────────────────────────────────
# (향후 확장 자리) advanced_preprocess
# ─────────────────────────────────────────────────────────
# soynlp 정규화 + kiwipiepy 형태소 분석 + kss 문장분할
# 라이브러리 설치 후 구현 예정 — 현재는 NotImplementedError
def advanced_preprocess(text: str) -> str:
    raise NotImplementedError(
        "advanced_preprocess: soynlp/kiwipiepy 설치 후 다음 브랜치에서 구현"
    )
