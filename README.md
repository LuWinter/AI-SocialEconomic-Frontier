# Literature Review Generator

## Authors
- Zekai Shen
- Wentao Lu

## Description
This project utilizes library APIs and the OpenAI API to implement an automated literature review generator. Key steps include retrieving relevant literature, extracting literature information, and generating literature summaries

## Application
Input your research variables, output your literature review !

## Program Structure
    - get-articles.py: get articles' info from API which are most relevant to the search words
    - download-pdf.py: download the pdf of the found articles
    - paper-framer.py: get the article structure by analyzing the pdf file
    - summarize.py: get key info from the analyzed articles  by using OpenAI API
    - main.py: generate the literature review using key info of the articles