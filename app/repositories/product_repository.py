from dataclasses import dataclass
from datetime import datetime

from app.repositories.database import Database


@dataclass(frozen=True)
class ProductListItem:
    id: int
    product_code: str
    product_name: str | None
    product_type: str
    profile_name: str
    packaging_rule: str
    mixed_box_allowed: bool
    active: bool


@dataclass(frozen=True)
class ProductCodeRuleListItem:
    id: int
    match_type: str
    pattern: str
    product_type: str
    profile_name: str | None
    priority: int
    active: bool


class ProductRepository:
    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

    def list_products(self) -> list[ProductListItem]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    products.*,
                    product_types.name AS product_type,
                    product_profiles.name AS profile_name
                FROM products
                JOIN product_types ON product_types.id = products.product_type_id
                JOIN product_profiles ON product_profiles.id = products.profile_id
                ORDER BY products.product_code ASC
                """
            ).fetchall()
        return [
            ProductListItem(
                id=row["id"],
                product_code=row["product_code"],
                product_name=row["product_name"],
                product_type=row["product_type"],
                profile_name=row["profile_name"],
                packaging_rule=row["packaging_rule"],
                mixed_box_allowed=bool(row["mixed_box_allowed"]),
                active=bool(row["active"]),
            )
            for row in rows
        ]

    def list_code_rules(self) -> list[ProductCodeRuleListItem]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    product_code_rules.*,
                    product_types.name AS product_type,
                    product_profiles.name AS profile_name
                FROM product_code_rules
                JOIN product_types ON product_types.id = product_code_rules.product_type_id
                LEFT JOIN product_profiles ON product_profiles.id = product_code_rules.profile_id
                ORDER BY product_code_rules.priority ASC, product_code_rules.id ASC
                """
            ).fetchall()
        return [
            ProductCodeRuleListItem(
                id=row["id"],
                match_type=row["match_type"],
                pattern=row["pattern"],
                product_type=row["product_type"],
                profile_name=row["profile_name"],
                priority=row["priority"],
                active=bool(row["active"]),
            )
            for row in rows
        ]

    def list_product_types(self) -> list[str]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT name FROM product_types WHERE active = 1 ORDER BY id ASC"
            ).fetchall()
        return [row["name"] for row in rows]

    def list_profiles_for_type(self, product_type: str) -> list[str]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT product_profiles.name
                FROM product_profiles
                JOIN product_types ON product_types.id = product_profiles.product_type_id
                WHERE product_types.name = ?
                  AND product_profiles.active = 1
                ORDER BY product_profiles.id ASC
                """,
                (product_type,),
            ).fetchall()
        return [row["name"] for row in rows]

    def save_product(self, product: ProductListItem) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        with self.database.transaction() as connection:
            product_type_id = self._product_type_id(connection, product.product_type)
            profile_id = self._profile_id(connection, product.profile_name)
            product_id = product.id or self._existing_product_id(connection, product.product_code)
            if product_id == 0:
                cursor = connection.execute(
                    """
                    INSERT INTO products (
                        product_code,
                        product_name,
                        product_type_id,
                        profile_id,
                        packaging_rule,
                        mixed_box_allowed,
                        active,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        product.product_code,
                        product.product_name,
                        product_type_id,
                        profile_id,
                        product.packaging_rule,
                        int(product.mixed_box_allowed),
                        int(product.active),
                        now,
                        now,
                    ),
                )
                return int(cursor.lastrowid)

            connection.execute(
                """
                UPDATE products
                SET
                    product_code = ?,
                    product_name = ?,
                    product_type_id = ?,
                    profile_id = ?,
                    packaging_rule = ?,
                    mixed_box_allowed = ?,
                    active = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    product.product_code,
                    product.product_name,
                    product_type_id,
                    profile_id,
                    product.packaging_rule,
                    int(product.mixed_box_allowed),
                    int(product.active),
                    now,
                    product_id,
                ),
            )
            return product_id

    def save_code_rule(self, rule: ProductCodeRuleListItem) -> int:
        with self.database.transaction() as connection:
            product_type_id = self._product_type_id(connection, rule.product_type)
            profile_id = self._profile_id(connection, rule.profile_name) if rule.profile_name else None
            if rule.id == 0:
                cursor = connection.execute(
                    """
                    INSERT INTO product_code_rules (
                        match_type,
                        pattern,
                        product_type_id,
                        profile_id,
                        priority,
                        active
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rule.match_type,
                        rule.pattern,
                        product_type_id,
                        profile_id,
                        rule.priority,
                        int(rule.active),
                    ),
                )
                return int(cursor.lastrowid)

            connection.execute(
                """
                UPDATE product_code_rules
                SET
                    match_type = ?,
                    pattern = ?,
                    product_type_id = ?,
                    profile_id = ?,
                    priority = ?,
                    active = ?
                WHERE id = ?
                """,
                (
                    rule.match_type,
                    rule.pattern,
                    product_type_id,
                    profile_id,
                    rule.priority,
                    int(rule.active),
                    rule.id,
                ),
            )
            return rule.id

    def _product_type_id(self, connection: object, product_type: str) -> int:
        row = connection.execute(
            "SELECT id FROM product_types WHERE name = ? AND active = 1",
            (product_type,),
        ).fetchone()
        if row is None:
            raise ValueError("Ürün tipi bulunamadı.")
        return int(row["id"])

    def _existing_product_id(self, connection: object, product_code: str) -> int:
        row = connection.execute(
            "SELECT id FROM products WHERE product_code = ?",
            (product_code,),
        ).fetchone()
        return int(row["id"]) if row is not None else 0

    def _profile_id(self, connection: object, profile_name: str | None) -> int:
        if not profile_name:
            raise ValueError("Profil seçilmelidir.")
        row = connection.execute(
            "SELECT id FROM product_profiles WHERE name = ? AND active = 1",
            (profile_name,),
        ).fetchone()
        if row is None:
            raise ValueError("Profil bulunamadı.")
        return int(row["id"])
