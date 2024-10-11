import asyncio
import json
import re
import threading

from playwright.async_api import async_playwright, TimeoutError


URL = "https://www.abcp.ru/suppliers/estonia"

def save_to_json(data, filename):
    with open(filename, "w", encoding="UTF-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

async def writing_links_to_txt():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(URL)

        k = 0
        td = await page.query_selector_all('[style="color: grey; font-size: 12px;"]')
        supplierlink = await page.query_selector_all('a[class="supplierInfoLink"]')
        data = {}
        print(len(supplierlink))
        for link in supplierlink:
            href = await td[k].inner_text()
            sup_href = await link.get_attribute("href")
            data[href] = sup_href
            k += 1
        
        save_to_json(data, "data_estonia.json")

        await browser.close()

def read_json():
    with open("data_estonia.json", encoding="UTF-8") as file:
        return json.load(file)

async def get_contacts(url):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(url, timeout=11111)
        await page.wait_for_selector('div#accordion a[rel="noopener nofollow"]', timeout=11111)

        accordion_links = await page.query_selector_all('div#accordion a')
        k = 0
        result = {}
        for accordion_link in accordion_links:
            value = await accordion_link.get_attribute("href")
            if "+" in value:
                result["phone"] = value[5:]
            elif "@" in value:
                cleaned_email = re.sub(r'[\u200b\u200c\u200d\uFEFF]', '', value[7:])
                result["email"] = cleaned_email
        return result
        await browser.close()

def main():
    asyncio.run(writing_links_to_txt())

def parser(dct):
    while True:
        if len(dct["data_only_keys"]) != 0:
            link = dct["data_only_keys"].pop(0)
        else:
            break
        try:
            try:
                val = asyncio.run(get_contacts(dct["data"][link]))
            except TimeoutError as e:
                val = asyncio.run(get_contacts(dct["data"][link]))
        except TimeoutError as e:
            dct["result"][link] = {}
            continue
        except Exception as e:
            pass
        dct["result"][link] = val
        print(f"{link}: {dct["result"][link]}", dct["k"])
        dct["k"] += 1

if __name__ == "__main__":
    main()
    data = read_json()
    result = {}
    thrs = []
    dct = {"data": data, "result": result, "data_only_keys": list(data.keys()), "k": 0}
    for _ in range(6):
        thr = threading.Thread(target=parser, args=(dct, ))
        thr.start()
        thrs.append(thr)
    
    for thr in thrs:
        thr.join()

    save_to_json(result, "result_estonia.json")