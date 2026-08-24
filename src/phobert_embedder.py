import re
from typing import List
from src.models import DocumentChunk

# High-priority direct environmental & pollution keywords (weight = 3.0)
HIGH_PRIORITY_ESG_KEYWORDS = [
    "khí thải", "phát thải", "khí nhà kính", "net zero", "carbon", "dấu chân carbon",
    "xả thải", "nước thải", "tái chế", "bao bì tái chế", "rác thải", "nhựa",
    "năng lượng tái tạo", "năng lượng mặt trời", "chất thải", "iso 14001", "ô nhiễm",
    "xử lý nước thải", "giảm nhựa", "đa dạng sinh học"
]

# Medium-priority ESG keywords (weight = 1.0)
MEDIUM_PRIORITY_ESG_KEYWORDS = [
    "môi trường", "bền vững", "tiết kiệm năng lượng", "chứng nhận",
    "bảo vệ môi trường", "giảm thiểu", "nguyên liệu"
]


def calculate_keyword_relevance(text: str) -> float:
    """Calculate weighted ESG environmental relevance score."""
    text_lower = text.lower()
    score = 0.0

    # High priority matches
    for kw in HIGH_PRIORITY_ESG_KEYWORDS:
        if kw in text_lower:
            score += text_lower.count(kw) * 3.0

    # Medium priority matches
    for kw in MEDIUM_PRIORITY_ESG_KEYWORDS:
        if kw in text_lower:
            score += text_lower.count(kw) * 1.0

    # Normalize score
    words = len(text_lower.split())
    if words == 0:
        return 0.0

    normalized_score = (score / (words + 5)) * 25.0
    return min(1.0, round(normalized_score, 4))


# Noise & Junk patterns for Stage 1 Coarse Filtering
NOISE_JUNK_PATTERNS = [
    "mục lục", "danh mục", "danh mục từ viết tắt", "bảng chỉ số",
    "lời mở đầu", "thông điệp của chủ tịch", "thông điệp tổng giám đốc",
    "kính gửi quý cổ đông", "tuyên bố miễn trừ trách nhiệm", "điều khoản pháp lý",
    "lưu ý về thông tin dự báo", "bản quyền thuộc về", "trang này cố ý để trống"
]


def is_noise_or_junk_chunk(text: str) -> bool:
    """
    Stage 1 Noise Removal: Detects Table of Contents, Greetings, Legal Disclaimers, etc.
    """
    text_lower = text.lower()
    
    # Check for short metadata or table of contents headers
    for pattern in NOISE_JUNK_PATTERNS:
        if pattern in text_lower:
            # Preserve if chunk contains critical ESG quantitative metrics
            critical_metrics = ["net zero", "iso 14001", "khí nhà kính", "xả thải", "pas 2060"]
            if not any(cm in text_lower for cm in critical_metrics):
                return True
    return False


def coarse_filter_chunks(chunks: List[DocumentChunk]) -> List[DocumentChunk]:
    """
    STAGE 1: LỌC THÔ (Coarse Filtering)
    Quét qua toàn bộ ~600 chunks, loại bỏ mục lục, lời chào, điều khoản pháp lý, rác...
    """
    clean_chunks = []
    dropped_count = 0

    for chunk in chunks:
        if is_noise_or_junk_chunk(chunk.text_content):
            dropped_count += 1
            continue
        clean_chunks.append(chunk)

    print(f"🧹 [STAGE 1 - LỌC THÔ]: Đã quét {len(chunks)} chunks -> Loại bỏ {dropped_count} chunks rác (Mục lục, Lời chào, Điều khoản pháp lý) -> Giữ lại {len(clean_chunks)} chunks sạch.")
    return clean_chunks


def fine_filter_chunks(chunks: List[DocumentChunk], min_score: float = 0.05, top_k: int = 30) -> List[DocumentChunk]:
    """
    STAGE 2: LỌC TINH (Fine Filtering)
    Tính điểm liên quan ESG Việt Nam & PhoBERT embedding relevance score, chọn Top candidate chunks cho Agent 3 loop.
    """
    scored_chunks = []
    
    try:
        from pyvi import ViTokenizer
        has_pyvi = True
    except ImportError:
        has_pyvi = False

    for chunk in chunks:
        text = chunk.text_content
        if has_pyvi:
            segmented_text = ViTokenizer.tokenize(text)
        else:
            segmented_text = text
            
        score = calculate_keyword_relevance(segmented_text)
        chunk.relevance_score = score
        if score >= min_score:
            scored_chunks.append(chunk)

    # Sort by relevance score descending
    scored_chunks.sort(key=lambda x: x.relevance_score, reverse=True)
    
    effective_k = 30 if top_k <= 0 else top_k
    selected = scored_chunks[:effective_k]

    print(f"🎯 [STAGE 2 - LỌC TINH]: Đã tính điểm liên quan ESG cho {len(scored_chunks)} chunks -> Lựa chọn Top {len(selected)} Chunks có điểm tương quan cao nhất để đưa vào Vòng lặp Agent 1, 2, 3.")
    return selected


def filter_esg_relevant_chunks(chunks: List[DocumentChunk], min_score: float = 0.05, top_k: int = 30) -> List[DocumentChunk]:
    """
    Full 2-Stage Filtering Workflow: Stage 1 Coarse Filtering -> Stage 2 Fine Filtering.
    """
    stage1_clean = coarse_filter_chunks(chunks)
    stage2_selected = fine_filter_chunks(stage1_clean, min_score=min_score, top_k=top_k)
    return stage2_selected


if __name__ == "__main__":
    sample_text = "Vinamilk cam kết giảm 20% lượng phát thải khí nhà kính và 100% bao bì tái chế vào năm 2030."
    score = calculate_keyword_relevance(sample_text)
    print(f"Sample relevance score: {score}")
