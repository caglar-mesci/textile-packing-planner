from pathlib import Path

from app.repositories.database import Database
from app.repositories.profile_repository import ProfileListItem, ProfileRepository


def test_profile_repository_lists_seeded_active_profiles(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    profiles = ProfileRepository(database).list_active_profiles()

    assert len(profiles) == 9
    assert any(profile.product_type == "Fabric Roll" for profile in profiles)


def test_profile_repository_saves_new_profile(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()
    repository = ProfileRepository(database)

    profile_id = repository.save_profile(
        ProfileListItem(
            id=0,
            name="Yeni T-Shirt",
            product_type="T-Shirt",
            average_length_cm=31,
            average_width_cm=26,
            average_height_cm=2,
            average_weight_kg=0.21,
            average_diameter_cm=None,
            allowed_orientation=None,
            default_packaging_rule="BOXED",
            default_mixed_box_allowed=True,
            active=True,
        )
    )

    profiles = repository.list_active_profiles()
    assert profile_id is not None
    assert any(profile.name == "Yeni T-Shirt" for profile in profiles)
