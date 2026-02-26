import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SchemaPusher")

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
SQL_FILE = PROJECT_ROOT / "Data" / "Supabase" / "supabase_schema.sql"

def push_schema():
    """Reads the local supabase_schema.sql and pushes it to Supabase via RPC."""
    load_dotenv(PROJECT_ROOT / ".env")
    
    url = os.environ.get("SUPABASE_URL")
    # Must use service key for DDL execution, anon key doesn't have privileges
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        logger.error("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
        return False
        
    try:
        supabase: Client = create_client(url, key)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return False

    if not SQL_FILE.exists():
        logger.error(f"Schema file not found at {SQL_FILE}")
        return False
        
    logger.info(f"Reading schema from {SQL_FILE}")
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    logger.info("Pushing schema to Supabase via RPC 'execute_sql'...")
    try:
        # Calls exactly 'execute_sql' function that the user must create once
        supabase.rpc('execute_sql', {'query': sql_content}).execute()
        
        # We MUST refresh the PostgREST schema cache immediately after dropping/creating tables,
        # otherwise subsequent REST API calls in the same script run will get PGRST205 (Table Not Found)
        logger.info("Refreshing PostgREST schema cache via RPC 'refresh_schema'...")
        supabase.rpc('refresh_schema').execute()
        
        logger.info("Schema push successful. Database is fully provisioned and synced.")
        return True
    except Exception as e:
        err_str = str(e)
        if "Could not find the function execute_sql" in err_str or "Could not find the function refresh_schema" in err_str:
            logger.error("\n" + "="*80)
            logger.error("CRITICAL: Required RPC functions are missing on your Supabase project.")
            logger.error("You must create them ONCE manually in the Supabase SQL Editor.")
            logger.error("Please run the following EXACT script in your Supabase SQL Editor:")
            logger.error("\n-- 1. Function to execute raw DDL")
            logger.error("CREATE OR REPLACE FUNCTION public.execute_sql(query text)\nRETURNS void\nLANGUAGE plpgsql\nSECURITY DEFINER\nAS $$\nBEGIN\n  EXECUTE query;\nEND;\n$$;\n")
            logger.error("-- 2. Function to reload PostgREST schema cache (Fixes PGRST205)")
            logger.error("CREATE OR REPLACE FUNCTION public.refresh_schema()\nRETURNS void\nLANGUAGE plpgsql\nSECURITY DEFINER\nAS $$\nBEGIN\n  NOTIFY pgrst, 'reload schema';\nEND;\n$$;\n")
            logger.error("After running those once, this auto-sync will work permanently.")
            logger.error("="*80 + "\n")
        else:
            logger.error(f"Schema push failed. Details: {e}")
        return False

if __name__ == "__main__":
    success = push_schema()
    sys.exit(0 if success else 1)
