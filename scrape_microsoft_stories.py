import asyncio
import pandas as pd
from playwright.async_api import async_playwright

# Adjust for testing or full scraping
MAX_PAGES = 5

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

            story_cards = await page.query_selector_all("div.card")
            if not story_cards:
                print("No more stories found. Stopping.")
                break

            for card in story_cards:
                try:
                    title_el = await card.query_selector("h3")
                    summary_el = await card.query_selector(".card-text")
                    industry_el = await card.query_selector(".industry")
                    link_el = await card.query_selector("a")

                    title = await title_el.inner_text() if title_el else "N/A"
                    summary = await summary_el.inner_text() if summary_el else "N/A"
                    industry = await industry_el.inner_text() if industry_el else "N/A"
                    link = await link_el.get_attribute("href") if link_el else "N/A"

                    full_link = f"https://www.microsoft.com{link.strip()}" if link and link.startswith("/") else link

                    data.append({
                        "title": title.strip(),
                        "summary": summary.strip(),
                        "industry": industry.strip(),
                        "link": full_link
                    })

                    print(f"✔ Scraped: {title.strip()}")

                except Exception as e:
                    print("❌ Error parsing a card:", e)

            # Save partial output every 25 pages
            if page_number % 25 == 0:
                pd.DataFrame(data).to_csv("microsoft_customer_stories.csv", index=False)
                print(f"💾 Intermediate CSV saved at page {page_number}")

            page_number += 1

        await browser.close()

    # Save final CSV
    df = pd.DataFrame(data)
    df.to_csv("microsoft_customer_stories.csv", index=False)
    print("✅ Scraping completed. Final CSV saved.")

if __name__ == "__main__":
    asyncio.run(scrape_stories())
