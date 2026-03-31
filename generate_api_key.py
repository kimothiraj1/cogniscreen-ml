"""
Run this ONCE to generate your ML API key.
Copy the output into your .env file and share the key with the backend team.

Usage:
  python generate_api_key.py
"""

import secrets
import string


def generate_key(length: int = 48) -> str:
    alphabet = string.ascii_letters + string.digits
    return "csk_" + "".join(secrets.choice(alphabet) for _ in range(length))


if __name__ == "__main__":
    key = generate_key()
    print("\n" + "="*60)
    print("  CogniScreen ML API Key")
    print("="*60)
    print(f"\n  {key}\n")
    print("="*60)
    print("\nSteps:")
    print("  1. Copy the key above")
    print("  2. Add to ML server .env:   ML_API_KEY=" + key)
    print("  3. Send the key to backend team (WhatsApp/Slack — NOT GitHub)")
    print("  4. Backend adds to their .env:  ML_API_KEY=" + key)
    print("  5. Backend sends it in every request header:")
    print('     headers: { "X-ML-API-Key": process.env.ML_API_KEY }')
    print("\n  NEVER commit this key to git.\n")
