from pathlib import Path

from app.repositories.database import Database
from app.repositories.product_repository import ProductCodeRuleListItem, ProductListItem, ProductRepository


def test_product_repository_lists_products_and_rules(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()
    with database.transaction() as connection:
        product_type_id = connection.execute("SELECT id FROM product_types WHERE name = 'T-Shirt'").fetchone()[0]
        profile_id = connection.execute("SELECT id FROM product_profiles WHERE name = 'Standard T-Shirt'").fetchone()[0]
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
            VALUES ('TSH-TEST', 'Test T-Shirt', ?, ?, 'BOXED', 1, '2026-01-01', '2026-01-01')
            """,
            (product_type_id, profile_id),
        )
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

    repository = ProductRepository(database)

    assert repository.list_products()[0].product_code == "TSH-TEST"
    assert repository.list_code_rules()[0].pattern == "TSH"


def test_product_repository_saves_product_and_rule(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()
    repository = ProductRepository(database)

    product_id = repository.save_product(
        ProductListItem(
            id=0,
            product_code="NEW-TSH",
            product_name="Yeni Ürün",
            product_type="T-Shirt",
            profile_name="Standard T-Shirt",
            packaging_rule="BOXED",
            mixed_box_allowed=True,
            active=True,
        )
    )
    rule_id = repository.save_code_rule(
        ProductCodeRuleListItem(
            id=0,
            match_type="STARTS_WITH",
            pattern="NEW",
            product_type="T-Shirt",
            profile_name="Standard T-Shirt",
            priority=10,
            active=True,
        )
    )

    assert product_id is not None
    assert rule_id is not None
    assert any(product.product_code == "NEW-TSH" for product in repository.list_products())
    assert any(rule.pattern == "NEW" for rule in repository.list_code_rules())


def test_product_repository_updates_existing_product_when_code_already_exists(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()
    repository = ProductRepository(database)
    first_id = repository.save_product(
        ProductListItem(
            id=0,
            product_code="DUP-TSH",
            product_name="Eski Ad",
            product_type="T-Shirt",
            profile_name="Standard T-Shirt",
            packaging_rule="BOXED",
            mixed_box_allowed=True,
            active=True,
        )
    )

    second_id = repository.save_product(
        ProductListItem(
            id=0,
            product_code="DUP-TSH",
            product_name="Yeni Ad",
            product_type="T-Shirt",
            profile_name="Standard T-Shirt",
            packaging_rule="BOXED",
            mixed_box_allowed=False,
            active=True,
        )
    )

    products = [product for product in repository.list_products() if product.product_code == "DUP-TSH"]
    assert second_id == first_id
    assert len(products) == 1
    assert products[0].product_name == "Yeni Ad"
    assert not products[0].mixed_box_allowed
