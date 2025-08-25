#!/bin/bash
export SUPABASE_URL="https://veklxmosegqkjtvjbksd.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZla2x4bW9zZWdxa2p0dmpia3NkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDcyODYxNiwiZXhwIjoyMDcwMzA0NjE2fQ.z8ahiNtn04kIjgNFyKXb8zAcSEj6BoEIxIc789dZZ-k"
export ANTHROPIC_API_KEY="dummy-key-for-test"
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000