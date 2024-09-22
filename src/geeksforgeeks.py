import asyncio
from playwright.async_api import async_playwright
import re
import pandas as pd

async def ensure_page_loaded(page):
    previous_height = await page.evaluate("document.body.scrollHeight")
    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
        current_height = await page.evaluate("document.body.scrollHeight")
        if current_height == previous_height:
            break
        previous_height = current_height

async def scrape_question_answer(page, question_text):
    question_element = await page.query_selector(f"h3:has-text('{question_text}')")
    
    if not question_element:
        print(f"Question not found: {question_text}")
        return None
    
    answer_elements = []
    next_sibling = await question_element.evaluate_handle('(el) => el.closest("h3").nextElementSibling')
    
    while next_sibling:
        tag_name = await next_sibling.evaluate('(el) => el.tagName.toLowerCase()')
        if tag_name == 'h3':
            break
        if tag_name in ['p', 'ul', 'span', 'h4', 'div']:
            answer_text = await next_sibling.inner_text()
            if answer_text.strip():
                answer_elements.append(answer_text)
        next_sibling = await next_sibling.evaluate_handle('(el) => el.nextElementSibling')

    return "\n".join(answer_elements)

async def scrape_website(url, start_from=0):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await ensure_page_loaded(page)
        
        paragraphs = await page.query_selector_all('h3')
        filtered_questions = [await p.inner_text() for p in paragraphs if re.match(r'^\d+\.', await p.inner_text())]
        
        questions_and_answers = []
        for idx, question in enumerate(filtered_questions[start_from:], start=start_from):
            try:
                print(f"Processing question {idx + 1}/{len(filtered_questions)}: {question}")
                answer = await scrape_question_answer(page, question)
                if not answer:
                    print(f"Warning: No answer found for question: {question}")
                else:
                    questions_and_answers.append({'Question': question, 'Answer': answer})
                    
            except Exception as e:
                print(f"Error processing question {question}: {e}")
        
        await browser.close()
        return pd.DataFrame(questions_and_answers)

async def main():
    url = "https://www.geeksforgeeks.org/data-analyst-interview-questions-and-answers/"
    df_gfg = await scrape_website(url)
    
    if df_gfg is not None:
        return df_gfg
    else:
        return None



def handler(event, context):
    # Your logic here
    df_gfg = asyncio.run(main())

    if df_gfg is not None:
        print("\nFinal DataFrame:")
        print(df_gfg)
        #df_gfg.to_csv('geeksforgeeks_QA.csv', index=False)
        print("File saved")
    else:
        print("No data was returned.")

    return {
        'statusCode': 200,
        'body': 'Hello from Lambda Vaidehi'
    }
