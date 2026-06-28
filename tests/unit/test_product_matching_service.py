from pathlib import Path

from app.repositories.database import Database
from app.services.product_matching_service import ProductMatchingService


def test_product_matching_prefers_exact_saved_product(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    with database.transaction() as connection:
        product_type_id = connection.execute("SELECT id FROM product_types WHERE name = 'Pants'").fetchone()[0]
        profile_id = connection.execute("SELECT id FROM product_profiles WHERE name = 'Standard Pants'").fetchone()[0]
        connection.execute(
            """
            INSERT INTO products (
                product_code,
                product_name,
                product_type_id,
                profile_id,
                packaging_rule,
                mixed_box_allowed,
                created_at,
                updated_at
            )
            VALUES ('ABC-123', 'Saved Pants', ?, ?, 'BOXED', 1, '2026-01-01', '2026-01-01')
            """,
            (product_type_id, profile_id),
        )

    lines = ProductMatchingService(database).enrich_lines(
        [{"product_code": "ABC-123", "product_name": None, "product_type": "T-Shirt", "quantity": 4}]
    )

    assert lines[0]["product_type"] == "Pants"
    assert lines[0]["product_name"] == "Saved Pants"
    assert lines[0]["match_source"] == "EXACT_PRODUCT"


def test_product_matching_applies_code_rule_when_product_is_unknown(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    with database.transaction() as connection:
        product_type_id = connection.execute("SELECT id FROM product_types WHERE name = 'T-Shirt'").fetchone()[0]
        profile_id = connection.execute("SELECT id FROM product_profiles WHERE name = 'Standard T-Shirt'").fetchone()[0]
        connection.execute(
            """
            INSERT INTO product_code_rules (
                match_type,
                pattern,
                product_type_id,
                profile_id,
                priority
            )
            VALUES ('STARTS_WITH', 'TSH', ?, ?, 10)
            """,
            (product_type_id, profile_id),
        )

    lines = ProductMatchingService(database).enrich_lines(
        [{"product_code": "TSH-555", "product_name": None, "product_type": None, "quantity": 7}]
    )

    assert lines[0]["product_type"] == "T-Shirt"
    assert lines[0]["profile_name"] == "Standard T-Shirt"
    assert lines[0]["match_source"] == "CODE_RULE"


def test_product_matching_uses_provided_type_as_fallback(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    lines = ProductMatchingService(database).enrich_lines(
        [{"product_code": "NEW-1", "product_name": None, "product_type": "Pantolon", "quantity": 2}]
    )

    assert lines[0]["product_type"] == "Pants"
    assert lines[0]["match_source"] == "PROVIDED_TYPE"

