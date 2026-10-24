import os
import sys

# Change to the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from database import SessionLocal, Prediction
from espn_api import LEAGUE_NAMES

def update_existing_leagues():
    db = SessionLocal()
    try:
        predictions = db.query(Prediction).all()
        updated_count = 0
        for p in predictions:
            if p.league_name in LEAGUE_NAMES:
                old_name = p.league_name
                p.league_name = LEAGUE_NAMES[p.league_name]
                print(f"Updating {old_name} -> {p.league_name}")
                updated_count += 1
        
        if updated_count > 0:
            db.commit()
            print(f"Successfully updated {updated_count} prediction records.")
        else:
            print("No records needed updating.")
    except Exception as e:
        print(f"Error updating records: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_existing_leagues()
