import asyncio
import pandas as pd
from playwright.async_api import async_playwright

async def extract_details(page, url):
    await page.goto(url, wait_until="domcontentloaded")
    await asyncio.sleep(2)

    # Extract executive summary
    try:
        summary_el = await page.query_selector("#exec-summary-section p")
        executive_summary = await summary_el.inner_text() if summary_el else "N/A"
    except:
        executive_summary = "N/A"

    # Initialize metadata
    details = {
        "executive_summary": executive_summary,
        "customer": "N/A",
        "products": [],
        "country_region": "N/A",
        "business_need": "N/A",
        "industry": "N/A",
        "organization_size": "N/A"
    }

    # All metadata items are in project-details-bar__body
    try:
        rows = await page.query_selector_all(".project-details-bar__body .project-details-bar__item")
        for row in rows:
            try:
                label_el = await row.query_selector(".label-eyebrow div")
                label = (await label_el.inner_text()).strip().lower() if label_el else ""

                value_list = await row.query_selector_all("ul li .link__text")
                values = [await v.inner_text() for v in value_list]

                if "customer" in label:
                    details["customer"] = values[0] if values else "N/A"
                elif "products" in label:
                    details["products"] = values
                elif "country" in label:
                    details["country_region"] = values[0] if values else "N/A"
                elif "business need" in label:
                    details["business_need"] = values[0] if values else "N/A"
                elif "industry" in label:
                    details["industry"] = values[0] if values else "N/A"
                elif "organization size" in label:
                    details["organization_size"] = values[0] if values else "N/A"

            except Exception as e:
                print(f"⚠️ Metadata parsing failed in one block: {e}")
    except Exception as e:
        print(f"❌ Failed to find metadata container: {e}")

    return details

async def enrich_csv():
    base_data = pd.read_csv("microsoft_customer_stories copy.csv")
    enriched_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for index, row in base_data.iterrows():
            url = row["link"]
            print(f"🔍 Enriching: {row['title']}")

            try:
                details = await extract_details(page, url)
                enriched_data.append({**row.to_dict(), **details})
            except Exception as e:
                print(f"❌ Failed to scrape {url}: {e}")
                enriched_data.append({**row.to_dict(), "executive_summary": "ERROR"})

        await browser.close()

    df = pd.DataFrame(enriched_data)
    # Join products into one string
    if "products" in df.columns:
        df["products"] = df["products"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    df.to_csv("microsoft_customer_stories_enriched.csv", index=False)
    print("✅ All done! Saved as microsoft_customer_stories_enriched.csv")

if __name__ == "__main__":
    asyncio.run(enrich_csv())
