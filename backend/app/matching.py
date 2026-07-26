"""
Akıllı Eşleştirme Motoru.

Saf Python fonksiyonlarıdır — backend'den bağımsız test edilebilir.
İleride bir AI motoruyla (ai_matching.py) değiştirilebilir; bu modülün
sözleşmesi (girdi/çıktı biçimi) sabit tutulmalıdır ki geri kalan sistem
(onay akışı, raporlama) hiç değişmeden çalışsın.
"""
import re
import difflib
from typing import Optional


def _tokenize(text: Optional[str]) -> set:
    if not text:
        return set()
    text = text.lower()
    return set(re.findall(r"[a-zA-ZğüşıöçĞÜŞİÖÇ0-9]+", text))


def _text_similarity(a: Optional[str], b: Optional[str]) -> float:
    """0-100 arası metin benzerliği: kelime kesişimi + dizi benzerliğinin en yükseği."""
    if not a or not b:
        return 0.0
    set_a, set_b = _tokenize(a), _tokenize(b)
    jaccard = 0.0
    if set_a and set_b:
        union = set_a | set_b
        jaccard = len(set_a & set_b) / len(union) if union else 0.0
    seq_ratio = difflib.SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()
    return round(max(jaccard, seq_ratio) * 100, 1)


def product_match_score(buyer_products: Optional[str], participant_products: Optional[str]) -> float:
    """
    Buyer'ın virgülle ayrılmış ilgi alanları ile katılımcının sunduğu
    ürünler arasında en iyi eşleşmelerin ortalaması.
    """
    if not buyer_products or not participant_products:
        return 0.0
    buyer_items = [p.strip() for p in buyer_products.split(",") if p.strip()]
    participant_items = [p.strip() for p in participant_products.split(",") if p.strip()]
    if not buyer_items or not participant_items:
        return 0.0
    best_scores = []
    for b_item in buyer_items:
        best = max(_text_similarity(b_item, p_item) for p_item in participant_items)
        best_scores.append(best)
    return round(sum(best_scores) / len(best_scores), 1)


def sector_match_score(buyer_sector: Optional[str], participant_sector: Optional[str]) -> float:
    return _text_similarity(buyer_sector, participant_sector)


def country_match_score(buyer_country: Optional[str], participant_country: Optional[str], mode: str) -> Optional[float]:
    """
    mode: 'none' | 'same_only' | 'exclude_same'
    None dönerse bu çift eleniyor demektir (filtre uygunsuz).
    """
    same = bool(buyer_country) and bool(participant_country) and \
        buyer_country.strip().lower() == participant_country.strip().lower()

    if mode == "same_only":
        return 100.0 if same else None
    if mode == "exclude_same":
        return None if same else 100.0
    # mode == 'none': filtre yok, ama skora yine de dahil edilir
    return 40.0 if same else 100.0


def compute_match(
    buyer,
    participant,
    weight_product: float,
    weight_sector: float,
    weight_country: float,
    country_mode: str,
) -> Optional[dict]:
    """Tek bir buyer-katılımcı çifti için skor hesaplar. Ülke filtresine
    uymuyorsa None döner (eleme)."""
    country_score = country_match_score(buyer.country, participant.country, country_mode)
    if country_score is None:
        return None

    product_score = product_match_score(buyer.interested_products, participant.offered_products)
    sector_score = sector_match_score(buyer.sector, participant.sector)

    total_weight = (weight_product + weight_sector + weight_country) or 1.0
    w_p = weight_product / total_weight
    w_s = weight_sector / total_weight
    w_c = weight_country / total_weight

    total = product_score * w_p + sector_score * w_s + country_score * w_c

    return {
        "product_score": product_score,
        "sector_score": sector_score,
        "country_score": country_score,
        "total_score": round(total, 1),
    }
