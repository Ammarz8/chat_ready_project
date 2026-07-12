-- Performance-tuning indexes for target analytical queries

-- Index for searching/filtering models by manufacturer and production year
CREATE INDEX IF NOT EXISTS idx_car_models_make_year 
ON car_models (make_id, year);

-- Index for sorting and computing statistics on combination fuel efficiency
CREATE INDEX IF NOT EXISTS idx_car_models_comb_mpg 
ON car_models (combination_mpg);

-- Index for wildcard searches and filtering by model name
CREATE INDEX IF NOT EXISTS idx_car_models_name 
ON car_models (model_name);
