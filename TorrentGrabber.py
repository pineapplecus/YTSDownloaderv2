import sys
import os
import asyncio
from pyppeteer import launch




# Using Qbittorrent CLI to automate: https://github.com/fedarovich/qbittorrent-cli/releases/tag/v1.7.21116.1

movie_titles = sys.argv[1:]
DOWNLOAD_DIR = "C:\\Users\\Owner\\Downloads" #PUT download dir here


async def pressTab(page, num):
    for i in range(10): 
        await page.keyboard.press('Tab') #navigate to typing area

async def grabTorrent(page):

    ## Grab all torrent links with quality
    all = await page.querySelectorAll("a")

    all = []
    qualities = ['BluRay', 'WEB']
    for quality in qualities: 
        possible =  await page.Jx(f"//a[contains(., '{quality}')]")
        for element in possible: 
            if await page.evaluate("(element) => $(element).is(':visible')", element) == True: 
                all.append(element)
        # all += await page.Jx(f"//a[contains(., '{quality}')]")
    quality = {}
    for button in all: 
        text = await page.evaluate('(element) => element.textContent', button)
        link = await page.evaluate('(element) => element.getAttribute("href")', button)
        rel = await page.evaluate('(element) => element.getAttribute("rel")', button)
        if any(typeOfMovie in text for typeOfMovie in qualities) and rel == "nofollow": #grabbing more than necessarry // and link not in quality.keys()
            quality[link] = button

            

    ## Make a map for all buttons
    buttons = {}
    for i, link in enumerate(quality): 
        button = quality[link]
        QualityAsText = await page.evaluate('(element) => element.textContent', button)
        print(f"{i}: {QualityAsText}")
        buttons[i] = button
    
    ## Grab user input to get what quality they want
    answer = int(input("============\n Choose your quality based on the numbers above: \n"))
    while answer not in list(range(len(quality))):
        answer = int(input("That wasn't a valid input. Choose a number from above. \n") )

    await buttons[answer].click()
    await asyncio.sleep(5)


async def main(movie_title):
    browser = await launch(headless=False, args=["--window-position=0,0"] )
    page = await browser.newPage()
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36')
    await page.goto(f'https://yts.mx/browse-movies/{movie_title}')
    asyncio.sleep(1)
    movies = await page.querySelectorAll(".browse-movie-title")
    options = {}

    if len(movies) == 1: 
        movie_link = await page.evaluate('(element) => element.getAttribute("href")', movies[0])
        await page.goto(f'{movie_link}')
    else: 
        for i in range(len(movies)): 
            url = await page.evaluate('(element) => element.getAttribute("href")', movies[i])
            title = await page.evaluate('(element) => element.textContent', movies[i])
            year = url.split('-')[-1]
            options[i] = url
            print(f'{i}: {title} -- {year}')
        
        answer = int(input("================\n Choose a number form above, to select your movie: \n"))
        while answer not in list(range(len(movies))):
            answer = int(input("That wasn't a valid input. Choose a number from above. \n") )
        print("================")
        
        await page.goto(options[answer])
        url = await grabTorrent(page)
        DownloadTorrents(url)

def DownloadTorrents(link): 
    os.system("echo 'Opening torrent...'")
    os.system(f'cd {DOWNLOAD_DIR}' + """ && pwd && ls  *.torrent | sed 's,\(.*\),"\\1",' | xargs qbt torrent add file""")

    


for movie in movie_titles:
    asyncio.get_event_loop().run_until_complete(main(movie))
