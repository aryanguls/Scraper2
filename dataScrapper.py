import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
import json
import urllib.parse as urlparse
from urllib.parse import urlencode

def ensure_directory_and_file_exist(directory_path, json_filename):
    os.makedirs(directory_path, exist_ok=True)
    if not os.path.exists(json_filename):
        with open(json_filename, 'w') as file:
            json.dump([], file)

def download_mp4(url, save_path):
    response = requests.get(url, stream=True)
    with open(save_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)
    print(f"Video downloaded: {save_path}")
    return save_path

def extract_metadata(driver, video_page_url):
    title = driver.find_element(By.CSS_SELECTOR, "h1.css-l6q8uz.e12adubs2").text
    filmmaker_name = driver.find_element(By.CSS_SELECTOR, "a.css-jrjoqw.e1829w741").text
    filmmaker_link = driver.find_element(By.CSS_SELECTOR, "a.css-jrjoqw.e1829w741").get_attribute('href')
    clip_id = driver.find_element(By.CSS_SELECTOR, "div.css-1i7w1v3.ejwfffu0 > p.css-14bjou0.e1020yka7").text
    releases = driver.find_element(By.CSS_SELECTOR, "div.css-zmkk7s.ejwfffu0 > p.css-14bjou0.e1020yka7").text
    return {
        "video_page_url": video_page_url,
        "title": title,
        "filmmaker": {
            "name": filmmaker_name,
            "link": filmmaker_link
        },
        "clip_id": clip_id,
        "releases": releases.split(", ")
    }

def update_json_with_metadata(metadata, video_source, download_path, json_path):
    with open(json_path, "r+") as file:
        data = json.load(file)
        metadata["video_source"] = video_source
        metadata["download_path"] = download_path
        data.append(metadata)
        file.seek(0)
        json.dump(data, file, indent=4)

def scrape_video_links(driver, url):
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.css-135q691.e15u04v5")))
    elements = driver.find_elements(By.CSS_SELECTOR, "a.css-135q691.e15u04v5")
    return [element.get_attribute('href') for element in elements]

def get_video_source(driver, video_page_url):
    driver.get(video_page_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "video > source")))
    return driver.find_element(By.CSS_SELECTOR, "video > source").get_attribute('src')

def update_url_with_page(url, page_number):
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query['page'] = str(page_number)
    url_parts[4] = urlencode(query)
    return urlparse.urlunparse(url_parts)

def main(base_url, save_directory, json_filename, max_videos=None):
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    videos_downloaded = 0
    page_number = 1

    ensure_directory_and_file_exist(save_directory, json_filename)

    while max_videos is None or videos_downloaded < max_videos:
        current_page_url = update_url_with_page(base_url, page_number)
        video_links = scrape_video_links(driver, current_page_url)

        if not video_links:
            break

        for link in video_links:
            if max_videos is not None and videos_downloaded >= max_videos:
                break

            video_source = get_video_source(driver, link)
            save_path = os.path.join(save_directory, f"video_{videos_downloaded + 1}.mp4")
            downloaded_path = download_mp4(video_source, save_path)

            metadata = extract_metadata(driver, link)
            update_json_with_metadata(metadata, video_source, downloaded_path, json_filename)

            videos_downloaded += 1

        page_number += 1

    driver.quit()
    print(f"Total videos downloaded: {videos_downloaded}")

user_input = input("Enter the number of videos you want to download or type 'ALL' for all videos: ").strip()
max_videos = None if user_input.upper() == 'ALL' else int(user_input)

base_url = "https://www.filmsupply.com/clips?gad_source=1&gclid=CjwKCAiA1-6sBhAoEiwArqlGPvct_rdoysH615k9uNzmL0OPXTVCVCSS0WLCVCudunTGlk5HsVgHYxoCdBIQAvD_BwE&hsa_acc=7063998716&hsa_ad=608524904520&hsa_cam=9672234843&hsa_grp=129684667354&hsa_kw=nature%20stock%20video&hsa_mt=e&hsa_net=adwords&hsa_src=g&hsa_tgt=kwd-3210917164&hsa_ver=3&page=1&search=nature&utm_campaign=all-tier-categories&utm_medium=ppc&utm_source=adwords&utm_term=nature%20stock%20video"
save_directory = "FilmSupplyVideos"
json_filename = "videos_metadata.json"
main(base_url, save_directory, json_filename, max_videos)
