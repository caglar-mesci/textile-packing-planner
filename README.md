# Textile Packing Planner

Desktop application for planning textile order packing from Excel files or manual order entry.

The codebase is written in English, while the end-user interface is Turkish.

## Features

- Import textile orders from `.xlsx` files.
- Detect common Turkish and English Excel column aliases.
- Review every worksheet before continuing when a workbook contains multiple order sheets.
- Highlight import errors and preview-level missing data before packing calculation.
- Edit order rows inline from the preview screen.
- Maintain product code mappings, product profiles, boxes, and vehicles.
- Calculate box counts, estimated weights, fullness, and vehicle usage.
- Block incomplete plans before the result screen.
- Export packing results to Excel.
- Save previous plans and view plan history.
- Create and restore database backups.
- Build a Windows desktop distribution with PyInstaller.

## Project Structure

```text
app/
  algorithms/      Packing and vehicle selection algorithms
  domain/          Shared models, enums, and exceptions
  importers/       Excel reading, column detection, and import models
  repositories/    SQLite schema access and persistence
  services/        Application services for packing, export, backup, settings
  ui/              PySide6 windows and screens
sample_data/       Mock Excel files for manual testing
scripts/           Mock data generation and Windows build script
tests/             Unit tests
```

## Requirements

- Python 3.11 or newer
- Windows for the desktop build script
- Python packages listed in `requirements.txt`

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the virtual environment does not exist yet, create it first:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run Locally

```powershell
cd textile_packing_planner
.\.venv\Scripts\python.exe -m app.main
```

You can also double-click:

```text
run_app.bat
```

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Current expected result:

```text
50 passed
```

## Mock Data

Sample Excel workbooks:

```text
sample_data/mock_orders.xlsx
sample_data/mock_orders_error_cases.xlsx
```

`mock_orders.xlsx` contains a table-style usage guide plus clean, preview-warning, import-error, edge-case, and column-alias sheets.

- `Temiz_Siparisler`: Clean end-to-end test data.
- `Onizleme_Eksikleri`: Valid import rows that still need preview fixes, such as missing product type or fabric-roll data.
- `Import_Hatalari`: Rows with blank product code and invalid quantities.
- `Kenar_Durumlar`: Large quantities, unknown product types, passive-profile scenarios, and heavy rolls.
- `Kolon_Aliaslari`: Alternate customer column names and Turkish product type aliases.

`mock_orders_error_cases.xlsx` is a smaller workbook for quick validation of import, preview, and calculation-warning flows.

Regenerate the mock files:

```powershell
.\.venv\Scripts\python.exe scripts\create_mock_data.py
```

## Build Windows App

Install PyInstaller once:

```powershell
.\.venv\Scripts\python.exe -m pip install pyinstaller
```

Build the app:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

The distributable app is created under:

```text
dist\TekstilPaketlemePlanlayici\
```

The executable is:

```text
dist\TekstilPaketlemePlanlayici\TekstilPaketlemePlanlayici.exe
```

Distribute the whole `dist\TekstilPaketlemePlanlayici` folder, not only the `.exe` file.

## Runtime Data

During local development, SQLite data is stored under:

```text
data\planner.sqlite3
```

When packaged as an EXE, application data is stored under the Windows user data folder:

```text
%LOCALAPPDATA%\TekstilPaketlemePlanlayici\
```

Backups contain the application database: products, rules, profiles, boxes, vehicles, settings, and saved plans. Excel exports are separate output files.

## Git Hygiene

The repository intentionally excludes generated and local files:

- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `work/`
- `data/*.sqlite3`
- `exports/`
- `backups/`
- `build/`
- `dist/`
- `*.spec`

This keeps GitHub focused on source code, tests, scripts, README, and mock data only.

## GitHub Publish

Create an empty GitHub repository, then connect and push:

```powershell
git remote add origin https://github.com/<owner>/<repo>.git
git push -u origin main
```

Do not commit generated EXE/build folders. They are intentionally ignored.
