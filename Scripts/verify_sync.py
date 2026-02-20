import asyncio
from Data.Access.supabase_client import get_supabase_client

async def verify_match_sync(fixture_id):
    supabase = get_supabase_client()
    if not supabase:
        print("Error: Supabase client not initialized")
        return
    
    print(f"Checking Supabase for fixture_id: {fixture_id}...")
    try:
        res = supabase.table('schedules').select('*').eq('fixture_id', fixture_id).execute()
        if res.data:
            match = res.data[0]
            print(f"Match found in Supabase:")
            print(f"  Teams: {match.get('home_team')} vs {match.get('away_team')}")
            print(f"  Score: {match.get('home_score')} - {match.get('away_score')}")
            print(f"  Status: {match.get('status')}")
            print(f"  Last Updated: {match.get('last_updated')}")
        else:
            print("Match not found in Supabase")
    except Exception as e:
        print(f"Error querying Supabase: {e}")

if __name__ == '__main__':
    asyncio.run(verify_match_sync('faowUnTa'))
