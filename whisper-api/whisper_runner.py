import sys
import os
import psycopg2
import json
from datetime import datetime

if __name__ == "__main__":
    stem_name = sys.argv[1]
    name = "test"
    input_path = f"/shared_data/vocal_stems/{stem_name}"
    
    print(f"📥 Received: {input_path}", file=sys.stderr)

    if not os.path.exists(input_path):
        print("❌ File not found", file=sys.stderr)
        sys.exit(1)

    # Simulate transcript
    transcript = f"Transcribed text from {stem_name}"
    print(transcript,  file=sys.stderr)
    print(json.dumps({"lyrics": transcript }))

    # Connect to Postgres
    # try:
    #     conn = psycopg2.connect(
    #         dbname=os.getenv("POSTGRES_DB"),
    #         user=os.getenv("POSTGRES_USER"),
    #         password=os.getenv("POSTGRES_PASSWORD"),
    #         host="clanker_db",  # Docker service name
    #         port="5432"
    #     )
    #     cursor = conn.cursor()

    #     # Insert transcript into table
    #     cursor.execute(
    #         "INSERT INTO songs (name, lyrics, stem_name, created_at) VALUES (%s, %s, %s, %s);",
    #         (name, transcript, stem_name, datetime.now())
    #     )
    #     conn.commit()
    #     print("✅ Inserted transcript into DB")
    #     cursor.close()
    #     conn.close()

    # except Exception as e:
    #     print(f"❌ DB Error: {e}")
    #     sys.exit(1)
