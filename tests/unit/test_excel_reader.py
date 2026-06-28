from pathlib import Path

import pytest
from openpyxl import Workbook

from app.domain.exceptions import MissingRequiredColumnError
from app.importers.excel_reader import ExcelOrderReader


def save_workbook(path: Path, rows: list[list[object]]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def test_excel_reader_detects_turkish_columns_and_merges_duplicates(tmp_path: Path) -> None:
    file_path = tmp_path / "order.xlsx"
    save_workbook(
        file_path,
        [
            ["Ürün Kodu", "Ürün Adı", "Ürün Tipi", "Adet"],
            ["TSH-001", "Beyaz Tişört", "T-Shirt", 10],
            ["TSH-001", "Beyaz Tişört", "T-Shirt", 5],
            ["PNT-002", "Pantolon", "Pantolon", 3],
        ],
    )

    preview = ExcelOrderReader().read(file_path)

    assert preview.is_valid
    assert len(preview.lines) == 2
    assert preview.total_quantity == 18
    assert preview.lines[0].quantity == 15
    assert preview.lines[1].product_type == "Pants"


def test_excel_reader_reports_invalid_rows(tmp_path: Path) -> None:
    file_path = tmp_path / "invalid-order.xlsx"
    save_workbook(
        file_path,
        [
            ["Stok Kodu", "Miktar"],
            ["ABC", -1],
            [None, 4],
        ],
    )

    preview = ExcelOrderReader().read(file_path)

    assert not preview.is_valid
    assert len(preview.errors) == 2


def test_excel_reader_requires_product_code_and_quantity_columns(tmp_path: Path) -> None:
    file_path = tmp_path / "missing-columns.xlsx"
    save_workbook(file_path, [["Ürün Kodu", "Açıklama"], ["ABC", "Test"]])

    with pytest.raises(MissingRequiredColumnError):
        ExcelOrderReader().read(file_path)

