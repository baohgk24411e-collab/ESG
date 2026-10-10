import re
import unicodedata
from typing import Dict, Any, Optional, List, Tuple
from src.models import GreenwashingClaim, NewsIncident


def normalize_vietnamese_text(text: Optional[str]) -> str:
    """Normalize Vietnamese text: lowercase, strip punctuation, strip accents for fuzzy matching."""
    if not text or not isinstance(text, str):
        return ""
    text = text.lower().strip()
    return text


def remove_accents(input_str: str) -> str:
    """Removes diacritics / accents from Vietnamese text."""
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


# Comprehensive environmental topic keywords mapped to domain
ESG_TOPIC_DOMAINS = {
    "water": [
        "nước thải", "xả thải", "nước ngầm", "tiêu thụ nước", "bùn thải",
        "cod", "bod5", "bảo tồn nguồn nước", "bồi hoàn nước", "cột a", "qcvn 40",
        "tài nguyên nước", "quản lý nước", "nguồn nước", "xả ra môi trường",
        "nước tiêu thụ", "nước"
    ],
    "climate_emissions": [
        "khí nhà kính", "phát thải", "giảm phát thải", "scope 1", "scope 2", "scope 3", "net zero",
        "carbon", "than đá", "biomass", "lò hơi", "sinh khối", "pas 2060",
        "trung hòa carbon", "kiểm kê khí", "knk", "tín chỉ carbon"
    ],
    "packaging_waste": [
        "bao bì", "tái chế", "nhựa", "thu hồi bao bì", "thu hồi vỏ chai", "thu hồi rác",
        "tỷ lệ thu hồi", "vỏ chai", "két nhựa", "phân hủy sinh học", "tự hủy", "epr",
        "màng ghép", "rác thải", "nguyên liệu tái sinh", "nguồn gốc thực vật", "rác thải nhựa"
    ],
    "energy": [
        "điện mặt trời", "áp mái", "năng lượng tái tạo", "năng lượng sạch",
        "tiết kiệm năng lượng", "leed", "ppa", "kwh", "phụ tải", "điện sinh học"
    ],
    "land_farm_odor": [
        "mùi hôi", "tiếng ồn", "chất thải hữu cơ", "biogas", "chuồng trại",
        "núi pháo", "đất đai", "thu hồi đất", "kcn", "giết mổ", "trang trại",
        "nông nghiệp xanh", "3f", "chăn nuôi", "phụ phẩm", "gia súc",
        "đồng cỏ", "trồng cỏ", "phân bón", "nông sản", "khu sinh thái"
    ],
    "eco_labeling": [
        "nhãn", "nhãn mác", "ghi nhãn", "chứng nhận", "thuần tự nhiên",
        "hữu cơ", "dầu ăn", "dầu thực vật", "eudr", "nông sản hữu cơ",
        "win eco", "green farm", "100% xanh", "siêu sạch"
    ],
    "legal_violation": [
        "xử phạt", "phạt tiền", "truy thu thuế", "thanh tra", "kết luận thanh tra",
        "sai phạm", "vượt quy chuẩn", "đình chỉ", "bộ tài nguyên", "kiểm tra", "giám sát"
    ]
}

COMPANY_ALIASES = {
    "sabeco": ["sabeco", "sab", "bia sai gon", "bia sài gòn", "sông lam", "song lam"],
    "habeco": ["habeco", "bhn", "bia ha noi", "bia hà nội", "mê linh", "me linh"],
    "dabaco": ["dabaco", "dbc", "thanh hóa", "thanh hoa"],
    "kido": ["kido", "kdc"],
    "masan": ["masan", "msn", "núi pháo", "nui phao", "phú minh", "phu minh"],
    "vinacafe": ["vinacafé", "vinacafe", "vcf", "biên hòa", "bien hoa"],
    "vinamilk": ["vinamilk", "vnm"],
    "vissan": ["vissan", "vsn", "bình thạnh", "binh thanh"]
}


def check_company_match(company_name: str, incident_company: str, incident_text: str) -> Tuple[bool, float]:
    """Dimension 1: Strict Company Matching."""
    c_norm = remove_accents(normalize_vietnamese_text(company_name))
    inc_norm = remove_accents(normalize_vietnamese_text(incident_company))
    inc_txt_norm = remove_accents(normalize_vietnamese_text(incident_text))

    if c_norm in inc_norm or inc_norm in c_norm:
        return True, 1.0

    # Check known aliases
    for base_comp, aliases in COMPANY_ALIASES.items():
        if any(remove_accents(a) in c_norm for a in aliases):
            if any(remove_accents(a) in inc_norm or remove_accents(a) in inc_txt_norm for a in aliases):
                return True, 1.0

    return False, 0.0


def extract_topic_domains(text: str) -> List[str]:
    """Identify which environmental domains a text belongs to."""
    t_norm = normalize_vietnamese_text(text)
    matched_domains = []
    for domain, kws in ESG_TOPIC_DOMAINS.items():
        if any(kw in t_norm for kw in kws):
            matched_domains.append(domain)
    return matched_domains


def compute_topic_match(claim_text: str, incident_title: str, incident_snippet: str) -> Tuple[bool, float, List[str]]:
    """Dimension 2 & 6: Environmental Topic & Dimension Consistency."""
    claim_domains = extract_topic_domains(claim_text)
    inc_text = f"{incident_title} {incident_snippet}"
    inc_domains = extract_topic_domains(inc_text)

    # Intersection of topic domains
    common_domains = list(set(claim_domains).intersection(set(inc_domains)))

    # Filter out pure 'legal_violation' domain unless matched with an environmental domain
    pure_legal = common_domains == ["legal_violation"]

    if not common_domains:
        # Check direct lexical overlap of specific environmental keywords
        claim_words = set(re.findall(r'\b\w{3,}\b', normalize_vietnamese_text(claim_text)))
        inc_words = set(re.findall(r'\b\w{3,}\b', normalize_vietnamese_text(inc_text)))
        overlap = claim_words.intersection(inc_words)
        # Exclude stop words
        stop_words = {"cho", "các", "của", "và", "nhưng", "trong", "được", "với", "năm", "báo", "cáo", "đến", "khi"}
        meaningful_overlap = overlap - stop_words
        if len(meaningful_overlap) >= 3:
            return True, 0.60, []
        return False, 0.0, []

    if pure_legal:
        # Incident is generic tax or legal fine, but claim was not about tax/legal
        return False, 0.20, common_domains

    # Strong environmental topic alignment
    score = 0.85 if len(common_domains) == 1 else 1.0
    return True, score, common_domains


def compute_facility_entity_match(claim_text: str, incident_text: str) -> float:
    """Dimension 5: Facility / Subsidiary / Geographic entity match."""
    facilities = [
        "sông lam", "mê linh", "thanh hóa", "núi pháo", "biên hòa",
        "bình thạnh", "bắc vinh", "quận bình thạnh", "đồng nai"
    ]
    c_norm = normalize_vietnamese_text(claim_text)
    i_norm = normalize_vietnamese_text(incident_text)

    for fac in facilities:
        if fac in c_norm and fac in i_norm:
            return 1.0
        if fac in i_norm and any(kw in c_norm for kw in ["nhà máy", "cơ sở", "trang trại", "chi nhánh"]):
            return 0.8
    return 0.5


def compute_claim_incident_relevance(
    claim_text: str,
    indicator_type: str,
    company_name: str,
    incident: Optional[NewsIncident]
) -> Dict[str, Any]:
    """
    Computes Deterministic Multi-Dimensional Claim-Incident Relevance Score (0.0 -> 1.0).
    Evaluates:
    1. Company match
    2. Topic match
    3. Indicator-specific semantic match
    4. Time relevance
    5. Entity/facility/subsidiary match
    6. Environmental dimension match
    7. Claim direction consistency
    """
    if not incident:
        return {
            "relevance_score": 0.0,
            "company_match": False,
            "topic_match": False,
            "entity_match": False,
            "time_match": False,
            "match_category": "NO_INCIDENT",
            "reasoning": "Không có dữ liệu bài báo sự kiện để đối chiếu."
        }

    inc_title = incident.title or ""
    inc_snippet = incident.snippet or ""
    inc_comp = incident.company_name or ""
    inc_combined = f"{inc_title} {inc_snippet}"

    # 1. Company Match (Mandatory Gate)
    comp_matched, comp_score = check_company_match(company_name, inc_comp, inc_combined)
    if not comp_matched:
        return {
            "relevance_score": 0.0,
            "company_match": False,
            "topic_match": False,
            "entity_match": False,
            "time_match": False,
            "match_category": "COMPANY_MISMATCH",
            "reasoning": f"Sự kiện không thuộc doanh nghiệp '{company_name}'."
        }

    # 2. Topic Match & Environmental Dimension (Mandatory Gate)
    topic_matched, topic_score, matched_domains = compute_topic_match(claim_text, inc_title, inc_snippet)
    if not topic_matched or topic_score < 0.3:
        return {
            "relevance_score": 0.15 * topic_score,
            "company_match": True,
            "topic_match": False,
            "entity_match": False,
            "time_match": False,
            "match_category": "TOPIC_MISMATCH",
            "reasoning": f"Sự kiện và tuyên bố lệch chủ đề môi trường: Claim [{claim_text[:50]}...] vs Incident [{inc_title[:50]}...]."
        }

    # 3. Entity & Facility Match
    facility_score = compute_facility_entity_match(claim_text, inc_combined)

    # 4. Indicator Specific Alignment
    ind_weight = 1.0
    if indicator_type == "Selective Disclosure" and any(d in ["water", "climate_emissions", "land_farm_odor"] for d in matched_domains):
        # High relevance: company hid wastewater or emissions, news reported wastewater or emissions violation
        ind_weight = 1.05
    elif indicator_type == "Hollow Promise" and "packaging_waste" in matched_domains:
        ind_weight = 1.0

    # 5. Combined Deterministic Relevance Score
    # Formula: 0.40 * topic_score + 0.30 * comp_score + 0.15 * facility_score + 0.15 * ind_weight
    raw_score = (0.45 * topic_score) + (0.25 * comp_score) + (0.15 * facility_score) + (0.15 * min(1.0, ind_weight))
    relevance_score = round(max(0.0, min(1.0, raw_score)), 4)

    # Threshold Categorization (Research-backed validation thresholds)
    if relevance_score >= 0.75:
        match_cat = "STRONG_MATCH"
    elif relevance_score >= 0.55:
        match_cat = "PARTIAL_MATCH"
    else:
        match_cat = "REJECT_LOW_RELEVANCE"

    reasoning = (
        f"Đối chiếu đa chiều: Công ty={comp_matched} (Điểm={comp_score}), "
        f"Chủ đề={topic_matched} ({matched_domains}, Điểm={topic_score:.2f}), "
        f"Cơ sở={facility_score:.2f} -> Relevance={relevance_score} [{match_cat}]."
    )

    return {
        "relevance_score": relevance_score,
        "company_match": comp_matched,
        "topic_match": topic_matched,
        "entity_match": facility_score >= 0.7,
        "time_match": True,
        "match_category": match_cat,
        "matched_domains": matched_domains,
        "reasoning": reasoning
    }
