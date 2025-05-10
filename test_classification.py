import asyncio
from app.ml.training_engine import engine

async def test_classification():
    title = "SQL Injection in Login Form"
    description = ("A critical SQL injection vulnerability was discovered in the application's login form. "
                   "The username field is vulnerable to SQL injection attacks, allowing attackers to bypass authentication "
                   "and potentially extract sensitive data from the database.")
    cves = ["CVE-2023-12345"]

    result = await engine.classify_vulnerability(title, description, cves)
    print("Classification Result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_classification())
