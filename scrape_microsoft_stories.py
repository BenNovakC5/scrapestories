import asyncio
import pandas as pd
from playwright.async_api import async_playwright

MAX_PAGES = 314  # Adjust to 313+ for full run

async def scrape_stories():
    data = []
    base_url = "https://www.microsoft.com/en-us/customers/search?page={}"
    page_number = 1

    async with async_playwright() as p:
        # Use headless=True for GitHub Actions; use headless=False for local debugging
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        while page_number <= MAX_PAGES:
            print(f"\n🔄 Loading page {page_number}...")
            await page.goto(base_url.format(page_number), wait_until="domcontentloaded")

            # Wait for real titles (not placeholders) to appear
            try:
                await page.wait_for_function(
                    """() => {
                        const titles = Array.from(document.querySelectorAll('.card--style-customer-story .block-feature__title'));
                        return titles.some(el => el.textContent && !el.textContent.includes('Placeholder'));
                    }""",
                    timeout=15000
                )
                await asyncio.sleep(2)  # Give extra time for full load
            except Exception as e:
                print(f"⚠️ Timeout or issue waiting for real story content on page {page_number}: {e}")
                page_number += 1
                continue

            # DEBUG: Save HTML snapshot for troubleshooting
            with open(f"page_{page_number}_snapshot.html", "w", encoding="utf-8") as f:
                f.write(await page.content())

            story_cards = await page.query_selector_all(".card--style-customer-story")
            print(f"📦 Found {len(story_cards)} cards")

            for card in story_cards:
                try:
                    title_el = await card.query_selector(".block-feature__title")
                    title = await title_el.inner_text() if title_el else "N/A"
                    if "Placeholder" in title:
                        continue

                    industry_el = await card.query_selector(".block-feature__label")
                    industry = await industry_el.inner_text() if industry_el else "N/A"

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
                    print(f"❌ Error parsing a card: {e}")

            page_number += 1

        await browser.close()

    df = pd.DataFrame(data)
    df.to_csv("microsoft_customer_stories.csv", index=False)
    print(f"\n✅ Done! {len(df)} stories saved to microsoft_customer_stories.csv")

if __name__ == "__main__":
    asyncio.run(scrape_stories())
