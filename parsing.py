from bs4 import BeautifulSoup
from database import createTask
import asyncio

html = open('./ege.html', encoding='utf-8').read() 
soup = BeautifulSoup(html, 'html.parser')

title = soup.title.text
blocks = soup.findAll('p', class_='left_margin')
all_texts = []

for block in blocks:
    text = block.get_text(separator=' ', strip=True)
    text = text.replace('\xad', '')
    all_texts.append(text)

filtered_texts = [t for t in all_texts if t and t[0].isdigit()]


block_size = 5
results = []

for i in range(0, len(filtered_texts), block_size * 2):
    questions = filtered_texts[i:i+block_size]
    answers = filtered_texts[i+block_size:i+block_size*2]
    for q, a in zip(questions, answers):
        results.append((q, a))

async def process_tasks(results):
    for i, (q, a) in enumerate(results, 1):
        answer = a[4:]
        ready_answer = answer[:5] == 'Верно'
        print(ready_answer)
        await createTask(q[4:], a[4:], ready_answer)
asyncio.run(process_tasks(results))