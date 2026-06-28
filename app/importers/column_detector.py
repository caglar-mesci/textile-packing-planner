import re
import unicodedata


COLUMN_ALIASES = {
    "product_code": [
        "ürün kodu",
        "urun kodu",
        "stok kodu",
        "malzeme kodu",
        "kod",
        "stok no",
        "product code",
        "product_code",
        "sku",
    ],
    "quantity": [
        "adet",
        "miktar",
        "sipariş miktarı",
        "siparis miktari",
        "qty",
        "quantity",
    ],
    "product_name": [
        "ürün adı",
        "urun adi",
        "ürün ismi",
        "urun ismi",
        "malzeme adı",
        "malzeme adi",
        "product name",
        "description",
        "açıklama",
        "aciklama",
    ],
    "product_type": [
        "ürün tipi",
        "urun tipi",
        "ürün türü",
        "urun turu",
        "tip",
        "type",
        "product type",
    ],
    "roll_length": [
        "rulo uzunluğu",
        "rulo uzunlugu",
        "roll length",
        "roll_length",
        "length",
        "uzunluk",
    ],
    "roll_weight": [
        "rulo ağırlığı",
        "rulo agirligi",
        "birim rulo ağırlığı",
        "birim rulo agirligi",
        "roll weight",
        "roll_weight",
        "weight",
        "ağırlık",
        "agirlik",
    ],
    "order_number": [
        "sipariş no",
        "siparis no",
        "order number",
        "order_number",
    ],
    "customer_name": [
        "müşteri",
        "musteri",
        "müşteri adı",
        "musteri adi",
        "customer",
        "customer name",
    ],
}

PRODUCT_TYPE_ALIASES = {
    "t-shirt": "T-Shirt",
    "tişört": "T-Shirt",
    "tisort": "T-Shirt",
    "shirt": "Shirt",
    "gömlek": "Shirt",
    "gomlek": "Shirt",
    "pants": "Pants",
    "pantolon": "Pants",
    "sweatshirt": "Sweatshirt",
    "jacket": "Jacket",
    "ceket": "Jacket",
    "other garment": "Other Garment",
    "diğer": "Other Garment",
    "diger": "Other Garment",
    "fabric roll": "Fabric Roll",
    "kumaş rulosu": "Fabric Roll",
    "kumas rulosu": "Fabric Roll",
    "rulo": "Fabric Roll",
}


def normalize_header(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = re.sub(r"[^a-z0-9ğüşıöç\s_]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_columns(headers: list[object]) -> dict[str, str]:
    normalized_headers = {normalize_header(header): str(header).strip() for header in headers if header is not None}
    mapping: dict[str, str] = {}

    for logical_name, aliases in COLUMN_ALIASES.items():
        normalized_aliases = {normalize_header(alias) for alias in aliases}
        for normalized_header, original_header in normalized_headers.items():
            if normalized_header in normalized_aliases:
                mapping[logical_name] = original_header
                break

    return mapping


def normalize_product_type(value: object) -> str | None:
    if value is None:
        return None
    normalized_value = normalize_header(value)
    if not normalized_value:
        return None
    return PRODUCT_TYPE_ALIASES.get(normalized_value, str(value).strip())

