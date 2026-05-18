from config import ENABLE_AI, OPENAI_API_KEY

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def generate_ai_description(product: dict) -> str:
    title = product.get("title", "Product")
    price = product.get("price", "")
    rating = product.get("rating", "")

    fallback = (
        f"🔥 Best deal alert!\n\n"
        f"{title}\n\n"
        f"✅ Good value product\n"
        f"✅ Limited time offer\n"
        f"✅ Check price before buying\n\n"
        f"#Deals #AmazonDeals #Shopping #Offer"
    )

    if not ENABLE_AI or not OPENAI_API_KEY or OpenAI is None:
        return fallback

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = f"""
Write a short Telegram affiliate product description in Hindi-English.

Product:
Title: {title}
Price: {price}
Rating: {rating}

Include:
- Short catchy description
- 3 benefits
- CTA
- 4 hashtags

Keep it under 120 words.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You write high-converting Telegram deal posts."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    except Exception:
        return fallback
