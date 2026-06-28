from dataclasses import dataclass

from app.repositories.database import Database


@dataclass(frozen=True)
class ProfileListItem:
    id: int
    name: str
    product_type: str
    average_length_cm: float | None
    average_width_cm: float | None
    average_height_cm: float | None
    average_weight_kg: float | None
    average_diameter_cm: float | None
    allowed_orientation: str | None
    default_packaging_rule: str
    default_mixed_box_allowed: bool
    active: bool


class ProfileRepository:
    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

    def list_active_profiles(self) -> list[ProfileListItem]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    product_profiles.*,
                    product_types.name AS product_type
                FROM product_profiles
                JOIN product_types ON product_types.id = product_profiles.product_type_id
                WHERE product_profiles.active = 1
                ORDER BY product_types.id ASC, product_profiles.id ASC
                """
            ).fetchall()
        return [
            ProfileListItem(
                id=row["id"],
                name=row["name"],
                product_type=row["product_type"],
                average_length_cm=row["average_length_cm"],
                average_width_cm=row["average_width_cm"],
                average_height_cm=row["average_height_cm"],
                average_weight_kg=row["average_weight_kg"],
                average_diameter_cm=row["average_diameter_cm"],
                allowed_orientation=row["allowed_orientation"],
                default_packaging_rule=row["default_packaging_rule"],
                default_mixed_box_allowed=bool(row["default_mixed_box_allowed"]),
                active=bool(row["active"]),
            )
            for row in rows
        ]

    def list_product_types(self) -> list[str]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT name
                FROM product_types
                WHERE active = 1
                ORDER BY id ASC
                """
            ).fetchall()
        return [row["name"] for row in rows]

    def save_profile(self, profile: ProfileListItem) -> int:
        with self.database.transaction() as connection:
            type_row = connection.execute(
                "SELECT id FROM product_types WHERE name = ? AND active = 1",
                (profile.product_type,),
            ).fetchone()
            if type_row is None:
                raise ValueError("Ürün tipi bulunamadı.")

            if profile.id == 0:
                cursor = connection.execute(
                    """
                    INSERT INTO product_profiles (
                        name,
                        product_type_id,
                        average_length_cm,
                        average_width_cm,
                        average_height_cm,
                        average_weight_kg,
                        average_diameter_cm,
                        allowed_orientation,
                        stackable,
                        default_packaging_rule,
                        default_mixed_box_allowed,
                        active
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                    """,
                    (
                        profile.name,
                        type_row["id"],
                        profile.average_length_cm,
                        profile.average_width_cm,
                        profile.average_height_cm,
                        profile.average_weight_kg,
                        profile.average_diameter_cm,
                        profile.allowed_orientation,
                        profile.default_packaging_rule,
                        int(profile.default_mixed_box_allowed),
                        int(profile.active),
                    ),
                )
                return int(cursor.lastrowid)

            connection.execute(
                """
                UPDATE product_profiles
                SET
                    name = ?,
                    product_type_id = ?,
                    average_length_cm = ?,
                    average_width_cm = ?,
                    average_height_cm = ?,
                    average_weight_kg = ?,
                    average_diameter_cm = ?,
                    allowed_orientation = ?,
                    default_packaging_rule = ?,
                    default_mixed_box_allowed = ?,
                    active = ?
                WHERE id = ?
                """,
                (
                    profile.name,
                    type_row["id"],
                    profile.average_length_cm,
                    profile.average_width_cm,
                    profile.average_height_cm,
                    profile.average_weight_kg,
                    profile.average_diameter_cm,
                    profile.allowed_orientation,
                    profile.default_packaging_rule,
                    int(profile.default_mixed_box_allowed),
                    int(profile.active),
                    profile.id,
                ),
            )
            return profile.id
