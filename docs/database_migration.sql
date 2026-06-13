-- Production schema draft for replacing data/app_state.json with Postgres.
-- The current app uses backend/services/storage_service.py as a swappable adapter.

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY,
    health_profile JSONB,
    preference_profile JSONB,
    daily_targets JSONB,
    meal_plan JSONB,
    grocery_list JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS meal_feedback (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    day TEXT,
    meal_type TEXT NOT NULL,
    meal_name TEXT NOT NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    liked BOOLEAN,
    difficulty TEXT,
    taste_preference TEXT,
    digestion TEXT,
    hunger_level TEXT,
    energy_level TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS adherence_logs (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    meal_type TEXT NOT NULL,
    meal_name TEXT,
    status TEXT NOT NULL CHECK (status IN ('completed', 'partial', 'skipped')),
    calories NUMERIC,
    protein_g NUMERIC,
    water_ml NUMERIC,
    weight_kg NUMERIC,
    sleep_hours NUMERIC,
    mood TEXT,
    digestion TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_user_created ON chat_messages(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_meal_feedback_user_meal ON meal_feedback(user_id, meal_name);
CREATE INDEX IF NOT EXISTS idx_adherence_user_date ON adherence_logs(user_id, date DESC);
