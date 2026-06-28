import re
import sqlite3
from dataclasses import dataclass

from app.importers.column_detector import normalize_product_type
from app.repositories.database import Database


@dataclass(frozen=True)
class ProductMatch:
    product_code: str
    product_name: str | None
    product_type: str | None
    profile_id: int | None
    profile_name: str | None
    packaging_rule: str | None
    mixed_box_allowed: bool | None
    match_source: str
    status_text: str


class ProductMatchingService:
    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

    def enrich_lines(self, lines: list[dict[str, object]]) -> list[dict[str, object]]:
        with self.database.connect() as connection:
            return [self._enrich_line(connection, line) for line in lines]

    def _enrich_line(self, connection: sqlite3.Connection, line: dict[str, object]) -> dict[str, object]:
        enriched = dict(line)
        product_code = str(enriched.get("product_code") or "").strip()

        exact_match = self._match_exact_product(connection, product_code)
        if exact_match:
            return self._apply_match(enriched, exact_match)

        rule_match = self._match_code_rule(connection, product_code)
        if rule_match:
            return self._apply_match(enriched, rule_match)

        provided_type = normalize_product_type(enriched.get("product_type"))
        if provided_type:
            enriched["product_type"] = provided_type
            enriched["match_source"] = "PROVIDED_TYPE"
            enriched["match_status"] = "Tip hazır"
            return enriched

        enriched["match_source"] = "UNKNOWN"
        enriched["match_status"] = "Tip eksik"
        return enriched

    def _apply_match(self, line: dict[str, object], match: ProductMatch) -> dict[str, object]:
        line["product_name"] = line.get("product_name") or match.product_name
        line["product_type"] = match.product_type
        line["profile_id"] = match.profile_id
        line["profile_name"] = match.profile_name
        line["packaging_rule"] = match.packaging_rule
        line["mixed_box_allowed"] = match.mixed_box_allowed
        line["match_source"] = match.match_source
        line["match_status"] = match.status_text
        return line

    def _match_exact_product(self, connection: sqlite3.Connection, product_code: str) -> ProductMatch | None:
        if not product_code:
            return None
        row = connection.execute(
            """
            SELECT
                products.product_code,
                products.product_name,
                product_types.name AS product_type,
                product_profiles.id AS profile_id,
                product_profiles.name AS profile_name,
                products.packaging_rule,
                products.mixed_box_allowed
            FROM products
            JOIN product_types ON product_types.id = products.product_type_id
            JOIN product_profiles ON product_profiles.id = products.profile_id
            WHERE products.product_code = ?
              AND products.active = 1
            """,
            (product_code,),
        ).fetchone()
        if row is None:
            return None
        return self._product_match_from_row(row, "EXACT_PRODUCT", "Ürün tanındı")

    def _match_code_rule(self, connection: sqlite3.Connection, product_code: str) -> ProductMatch | None:
        if not product_code:
            return None
        rows = connection.execute(
            """
            SELECT
                product_code_rules.match_type,
                product_code_rules.pattern,
                product_types.name AS product_type,
                product_profiles.id AS profile_id,
                product_profiles.name AS profile_name
            FROM product_code_rules
            JOIN product_types ON product_types.id = product_code_rules.product_type_id
            LEFT JOIN product_profiles ON product_profiles.id = product_code_rules.profile_id
            WHERE product_code_rules.active = 1
            ORDER BY product_code_rules.priority ASC, product_code_rules.id ASC
            """
        ).fetchall()

        for row in rows:
            if self._rule_matches(row["match_type"], row["pattern"], product_code):
                return ProductMatch(
                    product_code=product_code,
                    product_name=None,
                    product_type=row["product_type"],
                    profile_id=row["profile_id"],
                    profile_name=row["profile_name"],
                    packaging_rule=None,
                    mixed_box_allowed=None,
                    match_source="CODE_RULE",
                    status_text="Kod kuralı uygulandı",
                )
        return None

    def _rule_matches(self, match_type: str, pattern: str, product_code: str) -> bool:
        if match_type == "EXACT":
            return product_code == pattern
        if match_type == "STARTS_WITH":
            return product_code.startswith(pattern)
        if match_type == "CONTAINS":
            return pattern in product_code
        if match_type == "REGEX":
            try:
                return re.search(pattern, product_code) is not None
            except re.error:
                return False
        return False

    def _product_match_from_row(self, row: sqlite3.Row, match_source: str, status_text: str) -> ProductMatch:
        return ProductMatch(
            product_code=row["product_code"],
            product_name=row["product_name"],
            product_type=row["product_type"],
            profile_id=row["profile_id"],
            profile_name=row["profile_name"],
            packaging_rule=row["packaging_rule"],
            mixed_box_allowed=bool(row["mixed_box_allowed"]),
            match_source=match_source,
            status_text=status_text,
        )
