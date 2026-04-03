import asyncio
import random
import time
import logging
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(filename='youtube_activity.log', level=logging.INFO, format='%(asctime)s - %(message)s')

async def browse_youtube(duration_sec=60, click_probability=0.2, reward_callback=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Use headful for debugging/testing
        page = await browser.new_page()
        await page.goto("https://youtube.com")
        
        start_time = time.time()
        while time.time() - start_time < duration_sec:
            # Perform random scrolling
            scroll_amount = random.randint(100, 500)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            logging.info("Scrolled by %d pixels", scroll_amount)
            
            # Detect visible video thumbnails
            try:
                videos = await page.query_selector_all('a[href^="/watch?v="]')
                if videos and random.random() < click_probability:
                    video = random.choice(videos)
                    await video.click()
                    logging.info("Clicked on a video")
                    
                    # Wait for random period (30-180 seconds)
                    watch_time = random.randint(30, 180)
                    await asyncio.sleep(watch_time)
                    
                    # Simulate watching by occasional scrolling
                    for _ in range(random.randint(1, 5)):
                        await page.evaluate(f"window.scrollBy(0, {random.randint(50, 200)})")
                        await asyncio.sleep(random.randint(5, 15))
                    
                    logging.info("Watched video for %d seconds", watch_time)
                    
                    # Return to homepage
                    await page.goto("https://youtube.com")
                    logging.info("Returned to homepage")
                else:
                    # Wait for random interval between 2-8 seconds
                    wait_time = random.randint(2, 8)
                    await asyncio.sleep(wait_time)
            except Exception as e:
                logging.error("Error during browsing: %s", str(e))
                # Continue scrolling
                wait_time = random.randint(2, 8)
                await asyncio.sleep(wait_time)
        
        await browser.close()

        # Optional reward callback on successful completion
        if reward_callback is not None:
            try:
                result = reward_callback(0.01, "youtube")
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logging.error("Reward callback failed: %s", str(e))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Simulate human-like browsing on YouTube")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds to browse")
    parser.add_argument("--click-probability", type=float, default=0.2, help="Probability to click on a video (0.0 to 1.0)")
    args = parser.parse_args()
    asyncio.run(browse_youtube(args.duration, args.click_probability))