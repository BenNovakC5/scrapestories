import asyncio
import pandas as pd
from playwright.async_api import async_playwright

async def scrape_stories():
    data = []
    base_url = "https://www.microsoft.com/en-us/customers/search?page={}"
    page_number = 1

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        while True:
            print(f"Scraping page {page_number}...")
            await page.goto(base_url.format(page_number))
            await page.wait_for_load_state('networkidle')

            story_cards = await page.query_selector_all('div.card')
            if not story_cards:
                break  # no more pages

            for card in story_cards:
                try:
                    title = await card.query_selector_eval("h3", "el => el.textContent.trim()")
                    summary = await card.query_selector_eval(".card-text", "el => el.textContent.trim()")
                    industry = await card.query_selector_eval(".industry", "el => el.textContent.trim()") if await card.query_selector(".industry") else "N/A"
                    link = await card.query_selector_eval("a", "el => el.href")

                    data.append({
                        "title": title,
                        "summary": summary,
                        "industry": industry,
                        "link": link
                    })
                except Exception as e:
                    print("Error parsing a card:", e)

            page_number += 1

        await browser.close()

    df = pd.DataFrame(data)
    df.to_csv("microsoft_customer_stories.csv", index=False)

if __name__ == "__main__":
    asyncio.run(scrape_stories())
