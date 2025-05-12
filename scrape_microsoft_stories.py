import asyncio
import pandas as pd
from playwright.async_api import async_playwright

MAX_PAGES = 5  # For testing; increase to 313 for full run

async def scrape_stories():
    data = []
    base_url = "https://www.microsoft.com/en-us/customers/search?page={}"
    page_number = 1

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        while page_number <= MAX_PAGES:
            print(f"Scraping page {page_number}...")
            await page.goto(base_url.format(page_number), wait_until="domcontentloaded")

            story_cards = await page.query_selector_all("div.card--style-customer-story")
            print(f"Found {len(story_cards)} story cards on page {page_number}")

            for card in story_cards:
                try:
                    # Title
                    title_el = await card.query_selector(".block-feature__title")
                    title = await title_el.inner_text() if title_el else "N/A"

                    # Industry
                    industry_el = await card.query_selector(".block-feature__label")
                    industry = await industry_el.inner_text() if industry_el else "N/A"

                    # Story link
                    link_el = await card.query_selector("a.btn")
                    link = await link_el.get_attribute("href") if link_el else "N/A"
                    link = f"https://www.microsoft.com{link}" if link.startswith("/") else link

                    data.append({
                        "title": title.strip(),
                        "industry": industry.strip(),
                        "link": link.strip()
                    })

                    print(f"✔ {title.strip()}")

                except Exception as e:
                    print(f"❌ Error parsing card: {e}")

            page_number += 1

        await browser.close()

    df = pd.DataFrame(data)
    df.to_csv("microsoft_customer_stories.csv", index=False)
    print("✅ Done. CSV saved.")

if __name__ == "__main__":
    asyncio.run(scrape_stories())
