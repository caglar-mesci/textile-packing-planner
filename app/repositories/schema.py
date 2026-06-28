SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS product_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS product_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    product_type_id INTEGER NOT NULL,
    average_length_cm REAL,
    average_width_cm REAL,
    average_height_cm REAL,
    average_weight_kg REAL,
    average_diameter_cm REAL,
    allowed_orientation TEXT,
    stackable INTEGER NOT NULL DEFAULT 1,
    default_packaging_rule TEXT NOT NULL,
    default_mixed_box_allowed INTEGER NOT NULL DEFAULT 1,
    active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (product_type_id) REFERENCES product_types(id)
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code TEXT NOT NULL UNIQUE,
    product_name TEXT,
    product_type_id INTEGER NOT NULL,
    profile_id INTEGER NOT NULL,
    packaging_rule TEXT NOT NULL,
    mixed_box_allowed INTEGER NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (product_type_id) REFERENCES product_types(id),
    FOREIGN KEY (profile_id) REFERENCES product_profiles(id)
);

CREATE TABLE IF NOT EXISTS product_code_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_type TEXT NOT NULL,
    pattern TEXT NOT NULL,
    product_type_id INTEGER NOT NULL,
    profile_id INTEGER,
    priority INTEGER NOT NULL DEFAULT 100,
    active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (product_type_id) REFERENCES product_types(id),
    FOREIGN KEY (profile_id) REFERENCES product_profiles(id)
);

CREATE TABLE IF NOT EXISTS boxes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    inner_length_cm REAL NOT NULL,
    inner_width_cm REAL NOT NULL,
    inner_height_cm REAL NOT NULL,
    outer_length_cm REAL NOT NULL,
    outer_width_cm REAL NOT NULL,
    outer_height_cm REAL NOT NULL,
    empty_weight_kg REAL NOT NULL,
    max_gross_weight_kg REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS product_box_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id_nullable INTEGER,
    product_type_id_nullable INTEGER,
    box_id INTEGER NOT NULL,
    compatible INTEGER NOT NULL DEFAULT 1,
    operational_max_quantity_nullable INTEGER,
    priority INTEGER NOT NULL DEFAULT 100,
    FOREIGN KEY (product_id_nullable) REFERENCES products(id),
    FOREIGN KEY (product_type_id_nullable) REFERENCES product_types(id),
    FOREIGN KEY (box_id) REFERENCES boxes(id)
);

CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    inner_length_cm REAL NOT NULL,
    inner_width_cm REAL NOT NULL,
    inner_height_cm REAL NOT NULL,
    max_load_weight_kg REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT,
    customer_name TEXT,
    shipment_date TEXT,
    source_type TEXT NOT NULL,
    source_file TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_code TEXT NOT NULL,
    product_name TEXT,
    product_type_id INTEGER,
    profile_id INTEGER,
    quantity REAL NOT NULL,
    unit TEXT,
    roll_length_cm_nullable REAL,
    roll_weight_kg_nullable REAL,
    packaging_rule TEXT NOT NULL,
    mixed_box_allowed INTEGER NOT NULL,
    source_row INTEGER,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_type_id) REFERENCES product_types(id),
    FOREIGN KEY (profile_id) REFERENCES product_profiles(id)
);

CREATE TABLE IF NOT EXISTS packing_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    total_product_quantity REAL NOT NULL,
    total_box_count INTEGER NOT NULL,
    total_weight_kg REAL NOT NULL,
    average_box_fullness REAL NOT NULL,
    vehicle_id_nullable INTEGER,
    vehicle_count INTEGER NOT NULL,
    vehicle_volume_utilization REAL NOT NULL,
    vehicle_weight_utilization REAL NOT NULL,
    is_valid INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (vehicle_id_nullable) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS packing_plan_boxes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    packing_plan_id INTEGER NOT NULL,
    box_id INTEGER NOT NULL,
    sequence_number INTEGER NOT NULL,
    estimated_gross_weight_kg REAL NOT NULL,
    fullness_percent REAL NOT NULL,
    is_valid INTEGER NOT NULL,
    FOREIGN KEY (packing_plan_id) REFERENCES packing_plans(id),
    FOREIGN KEY (box_id) REFERENCES boxes(id)
);

CREATE TABLE IF NOT EXISTS packing_plan_box_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    packing_plan_box_id INTEGER NOT NULL,
    order_item_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    estimated_volume_cm3 REAL NOT NULL,
    estimated_weight_kg REAL NOT NULL,
    FOREIGN KEY (packing_plan_box_id) REFERENCES packing_plan_boxes(id),
    FOREIGN KEY (order_item_id) REFERENCES order_items(id)
);

CREATE TABLE IF NOT EXISTS application_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

