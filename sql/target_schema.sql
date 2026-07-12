-- Schema definition for relational analytics database (Silver Layer)

-- 1. Manufacturer Dimension Table
CREATE TABLE IF NOT EXISTS makes (
    make_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Vehicle Class Dimension Table
CREATE TABLE IF NOT EXISTS vehicle_classes (
    class_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Core Car Models Table (Fact/Entity Table)
CREATE TABLE IF NOT EXISTS car_models (
    model_id SERIAL PRIMARY KEY,
    make_id INT NOT NULL REFERENCES makes(make_id) ON DELETE RESTRICT,
    model_name VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    class_id INT REFERENCES vehicle_classes(class_id) ON DELETE SET NULL,
    transmission VARCHAR(20),
    drive_type VARCHAR(10),
    fuel_type VARCHAR(20),
    cylinders INT,
    displacement NUMERIC(3, 1),
    city_mpg INT,
    highway_mpg INT,
    combination_mpg INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Composite unique constraint to ensure absolute deduplication of vehicle records
    CONSTRAINT uq_car_specification UNIQUE (
        make_id, 
        model_name, 
        year, 
        transmission, 
        drive_type, 
        fuel_type, 
        displacement, 
        cylinders
    )
);
