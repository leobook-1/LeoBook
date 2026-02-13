-- GLOBAL SUPABASE SCHEMA (LeoBook)
-- This file serves as the single source of truth for the database schema.
-- v1.1: Added robust ALTER TABLE statements to handle existing tables.

-- =============================================================================
-- 1. EXTENSIONS & SETUP
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- 2. USER MANAGEMENT (Public Profiles)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT,
    username TEXT UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    tier TEXT DEFAULT 'free',
    credits INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Migration checks for profiles
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW();

CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- Trigger for new user
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, avatar_url)
  VALUES (new.id, new.email, new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'avatar_url');
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- =============================================================================
-- 3. CUSTOM RULE ENGINE
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.custom_rules (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    logic JSONB DEFAULT '{}'::jsonb NOT NULL,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE public.custom_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.custom_rules ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW();

CREATE POLICY "Users can fully manage own rules" ON public.custom_rules FOR ALL USING (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS public.rule_executions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    rule_id UUID REFERENCES public.custom_rules(id) ON DELETE CASCADE,
    fixture_id TEXT,
    user_id UUID REFERENCES public.profiles(id),
    result JSONB,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE public.rule_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rule_executions ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW();

CREATE POLICY "Users can view own rule executions" ON public.rule_executions FOR SELECT USING (auth.uid() = user_id);

-- =============================================================================
-- 4. DATA STORE (Core Tables)
-- =============================================================================

-- Region/League
CREATE TABLE IF NOT EXISTS public.region_league (
    rl_id TEXT PRIMARY KEY,
    region TEXT,
    region_flag TEXT,
    region_url TEXT,
    league TEXT,
    league_crest TEXT,
    league_url TEXT,
    date_updated TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.region_league ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.region_league ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW();
CREATE POLICY "Public Read Access RegionLeague" ON public.region_league FOR SELECT USING (true);

-- Teams
CREATE TABLE IF NOT EXISTS public.teams (
    team_id TEXT PRIMARY KEY,
    team_name TEXT,
    rl_ids TEXT,
    team_crest TEXT,
    team_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.teams ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW();
CREATE POLICY "Public Read Access Teams" ON public.teams FOR SELECT USING (true);

-- Schedules
CREATE TABLE IF NOT EXISTS public.schedules (
    fixture_id TEXT PRIMARY KEY,
    date TEXT,
    match_time TEXT,
    region_league TEXT,
    home_team TEXT,
    away_team TEXT,
    home_team_id TEXT,
    away_team_id TEXT,
    home_score TEXT,
    away_score TEXT,
    match_status TEXT,
    status TEXT,
    match_link TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.schedules ENABLE ROW LEVEL SECURITY;
-- CRITICAL FIX: Ensure 'status' column exists if table was created in an older version
ALTER TABLE public.schedules ADD COLUMN IF NOT EXISTS status TEXT;
ALTER TABLE public.schedules ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW();
CREATE POLICY "Public Read Access Schedules" ON public.schedules FOR SELECT USING (true);

-- Predictions
CREATE TABLE IF NOT EXISTS public.predictions (
    fixture_id TEXT PRIMARY KEY,
    date TEXT,
    match_time TEXT,
    region_league TEXT,
    home_team TEXT,
    away_team TEXT,
    home_team_id TEXT,
    away_team_id TEXT,
    prediction TEXT,
    confidence TEXT,
    reason TEXT,
    xg_home TEXT,
    xg_away TEXT,
    btts TEXT,
    over_2_5 TEXT,
    best_score TEXT,
    top_scores TEXT,
    home_form_n TEXT,
    away_form_n TEXT,
    home_tags TEXT,
    away_tags TEXT,
    h2h_tags TEXT,
    standings_tags TEXT,
    h2h_count TEXT,
    form_count TEXT,
    actual_score TEXT,
    outcome_correct TEXT,
    generated_at TEXT,
    status TEXT,
    match_link TEXT,
    odds TEXT,
    market_reliability_score TEXT,
    home_crest_url TEXT,
    away_crest_url TEXT,
    is_recommended TEXT,
    recommendation_score TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW();
CREATE POLICY "Public Read Access Predictions" ON public.predictions FOR SELECT USING (true);

-- Standings
CREATE TABLE IF NOT EXISTS public.standings (
    standings_key TEXT PRIMARY KEY,
    region_league TEXT,
    position INTEGER,
    team_name TEXT,
    team_id TEXT,
    played INTEGER,
    wins INTEGER,
    draws INTEGER,
    losses INTEGER,
    goals_for INTEGER,
    goals_against INTEGER,
    goal_difference INTEGER,
    points INTEGER,
    url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.standings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.standings ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW();
CREATE POLICY "Public Read Access Standings" ON public.standings FOR SELECT USING (true);

-- FB Matches
CREATE TABLE IF NOT EXISTS public.fb_matches (
    site_match_id TEXT PRIMARY KEY,
    date TEXT,
    time TEXT,
    home_team TEXT,
    away_team TEXT,
    league TEXT,
    url TEXT,
    last_extracted TEXT,
    fixture_id TEXT,
    matched TEXT,
    odds TEXT,
    booking_status TEXT,
    booking_details TEXT,
    booking_code TEXT,
    booking_url TEXT,
    status TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
ALTER TABLE public.fb_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fb_matches ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW();
CREATE POLICY "Public Read Access FBMatches" ON public.fb_matches FOR SELECT USING (true);

-- =============================================================================
-- 5. UTILITY & MAINTENANCE
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   NEW.last_updated = NOW(); -- Also update last_updated
   RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

DROP TRIGGER IF EXISTS update_rules_updated_at ON public.custom_rules;
CREATE TRIGGER update_rules_updated_at BEFORE UPDATE ON public.custom_rules FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
