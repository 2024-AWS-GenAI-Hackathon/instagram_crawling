#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import json

import boto3
from dotenv import load_dotenv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

selector = {
    'id_input': '._aa4b._add6._ac4d._ap35',
    'first_post': '._ac7v div a ._aagu > ._aagv + ._aagw',
    'next_btn': '._aaqg._aaqh > ._abl-',
    'cover': 'a ._aagu ._aagv img',
    'text': 'h1._ap3a._aaco._aacu._aacx._aad7._aade',
    'like': 'span a span .html-span.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x1hl2dhg.x16tdsg8.x1vvkbs',
    'date': '.x1p4m5qa',
    'comment_span': 'div._a9zr > div._a9zs > span'
}

account_name_list = ['nike']

load_dotenv(verbose=True)
INSTAGRAM_ID = os.getenv('INSTAGRAM_ID')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

options = webdriver.ChromeOptions()
options.add_argument(
    'User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
driver = webdriver.Chrome()

driver.get('https://instagram.com')
driver.implicitly_wait(10)
driver.maximize_window()


def click_nxt():
    next_btn = driver.find_element(By.CSS_SELECTOR, selector['next_btn'])
    next_btn.click()
    driver.implicitly_wait(10)


# 인스타그램 로그인하기
el = driver.find_elements(By.CSS_SELECTOR, selector['id_input'])  # ID input태그 선택하기
el[0].send_keys(INSTAGRAM_ID)
el[1].send_keys(INSTAGRAM_PASSWORD)
el[1].send_keys(Keys.ENTER)
time.sleep(10)

# 데이터를 저장할 리스트 초기화
data = []

# account_name에 접속하여 posts에서
# 1. 업로드 날짜
# 2. 본문 내용
# 3. 첫번째 이미지
# 4. 좋아요 개수
# 5. 댓글

MAX_POST_LENGTH = 20

for account_name in account_name_list:
    driver.get(f'https://instagram.com/{account_name}/')
    driver.implicitly_wait(10)

    covers = driver.find_elements(By.CSS_SELECTOR, selector['cover'])
    MIN_POST_LENGTH = min(MAX_POST_LENGTH, len(covers))

    # 첫 번째 게시물 클릭
    posts = driver.find_elements(By.CSS_SELECTOR, selector['first_post'])
    if posts:
        post = posts[0]
        post.click()
        driver.implicitly_wait(10)
    else:
        print(f"No posts found for account: {account_name}")
        continue

    # 게시물에서 본문/좋아요수/날짜/댓글을 얻기
    for i in range(MIN_POST_LENGTH):
        post_data = {}

        try:
            post_data["text"] = driver.find_element(By.CSS_SELECTOR, selector['text']).text
        except NoSuchElementException:
            post_data["text"] = ''

        post_data["image"] = covers[i].get_attribute('src')

        try:
            post_data["like"] = driver.find_element(By.CSS_SELECTOR, selector['like']).text
        except NoSuchElementException:
            post_data["like"] = '0'

        try:
            post_data["date"] = driver.find_element(By.CSS_SELECTOR, selector['date']).get_attribute('title')
        except NoSuchElementException:
            post_data["date"] = ''

        # 댓글 수집
        post_data["comment"] = []
        comments = driver.find_elements(By.CSS_SELECTOR, selector['comment_span'])

        for comment in comments:
            try:
                post_data["comment"].append(comment.text)
            except NoSuchElementException:
                break

        data.append(post_data)

        if i < MIN_POST_LENGTH - 1:
            click_nxt()

# JSON 파일로 저장
with open('./instagram.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("==============================")

with open('./instagram.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)

print(json.dumps(json_data, ensure_ascii=False, indent=4))


AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')

result_array = []


### S3 업로드 작성 ###
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
file_name = 'instagram'

def upload_file_s3(bucket, file_name, file):
    s3 = boto3.client('s3',aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    encode_file = json.dumps(file, indent=4, ensure_ascii=False)
    try:
        s3.put_object(Bucket=bucket, Key=file_name, Body=encode_file)
        return True
    except:
        return False

save = upload_file_s3(AWS_BUCKET_NAME, file_name + '.json', json_data)
print("S3 upload success : "+str(save))


# 드라이버 종료
driver.quit()