import asyncio
import pandas as pd
from playwright.async_api import async_playwright

MAX_PAGES = 5  # Adjust as needed

async def scrape_stories():
    data = []
    base_url = "https://www.microsoft.com/en-us/customers/search?page={}"
    page_number = 1

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        while page_number <= MAX_PAGES:
            print(f"\n🔄 Loading page {page_number}...")
            await page.goto(base_url.format(page_number), wait_until="domcontentloaded")

            # Explicitly wait for at least one customer story to render
            await page.wait_for_selector(".card--style-customer-story .block-feature__title", timeout=10000)

            story_cards = await page.query_selector_all(".card--style-customer-story")

            for card in story_cards:
                try:
                    # Title
                    title_el = await card.query_selector(".block-feature__title")
                    title = await title_el.inner_text() if title_el else "N/A"
                    if "Placeholder" in title:
                        continue

                    # Industry
                    industry_el = await card.query_selector(".block-feature__label")
                    industry = await industry_el.inner_text() if industry_el else "N/A"

                    # Link
                    link_el = await card.query_selector("a.btn")
                    link = await link_el.get_attribute("href") if link_el else None
                    if not link or "javascript:void" in link:
                        continue

                    full_link = f"https://www.microsoft.com{link}" if link.startswith("/") else link

                    data.append({
                        "title": title.strip(),
                        "industry": industry.strip(),
                        "link": full_link.strip()
                    })

                    print(f"✅ {title.strip()}")

                except Exception as e:
                    print(f"❌ Error on card: {e}")

            page_number += 1

        await browser.close()

    df = pd.DataFrame(data)
    df.to_csv("microsoft_customer_stories.csv", index=False)
    print(f"\n📁 Scraping complete. {len(df)} stories saved to CSV.")

if __name__ == "__main__":
    asyncio.run(scrape_stories())
