import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.update({
    "BUSINESS_ID": "test-business",
    "BUSINESS_NAME": "Test HVAC Co",
    "BUSINESS_TYPE": "HVAC",
    "OWNER_FIRST_NAME": "Sam",
    "PUBLIC_BASE_URL": "http://testserver",
    "TWILIO_ACCOUNT_SID": "ACtest",
    "TWILIO_AUTH_TOKEN": "test_auth",
    "TWILIO_PHONE_NUMBER": "+15550001111",
    "OWNER_PHONE_NUMBER": "+15550002222",
    "VALIDATE_TWILIO_SIGNATURE": "false",
    "SMS_DRY_RUN": "true",
    "MISTRAL_API_KEY": "test_mistral",
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_KEY": "sb_test",
})
