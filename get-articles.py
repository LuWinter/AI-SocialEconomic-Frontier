#!/usr/bin/env python
# coding: utf-8

# In[1]:


import sys
import requests
import pickle
import json
import openai
import numpy as np


# In[2]:


API_KEY = ""
openai.api_key = ""


research_question = f"I want to research the relationship between {sys.argv[1]} and {sys.argv[2]}"
print(research_question)

if research_question is None or len(research_question) < 3:
    print("Using Default Question")
    research_question = "I want to research the relationship between accounting conservatism and political connection"
# In[3]:


def get_search_res(search_words, api_key=API_KEY, num=100):
    gateway_search_url = "https://api-ap.hosted.exlibrisgroup.com/primo/v1/search?"
    search_params = [
        "vid=65SMU_INST:SMU_NUI",
        "tab=Everything",
        "scope=Everything",
        f"q=any,contains,{search_words}",
        "qInclude=facet_rtype,exact,articles",
        f"apikey={api_key}",
        f"limit={num}"
    ]
    res = requests.get(url=gateway_search_url + "&".join(search_params))
    
    if res.status_code == 200:
        return res.content
    
    print(f"Error Code: {res.status_code}")
    print(f"Error Message: {res.content}")
    return None

# get_search_res(search_words="political connection")


# In[4]:


def deal_publisher(publisher):
    if publisher.find("Springer") != -1:
        return "Springer"
    elif publisher.find("Wiley") != -1:
        return "Wiley"
    elif publisher.find("Emerald") != -1:
        return "Emerald"
    elif publisher.find("Routledge") != -1:
        return "Routledge"
    elif publisher.find("SAGE") != -1:
        return "SAGE"
    elif publisher.find("Elsevier") != -1:
        return "Elsevier"
    else:
        return None


# In[5]:


def get_article_details(search_words="political connection"):
    topic_res = get_search_res(search_words)
    topic_res_parsed = json.loads(topic_res)
    article_details = []
    for item in topic_res_parsed["docs"]:
        info = item["pnx"]["search"]
        identifier = item['pnx']['display']['identifier']
        identifier = {item.split(": ")[0]: item.split(": ")[1] for item in identifier}
        
        if "publisher" in item['pnx']['display']:
            publisher = item['pnx']['display']['publisher'][0]
            publisher = deal_publisher(publisher)
        else:
            publisher = None
        
        article_details.append({
            'author': info['creator'],
            'title': info['title'][0],
            'journal': info['title'][1].title(),
            'year': info['creationdate'][0],
            'doi': identifier['DOI'],
            'abstract': info['description'],
            'publisher': publisher
        })

    return article_details


# get_article_details()


# In[6]:


def get_full_text_url(doi):
    headers = {
        "Referer": "https://libkey.io/",
        "Origin": "https://libkey.io",
        "Host": "api.thirdiron.com",
        "Connection": "keep-alive",
        "Accept": "application/vnd.api+json",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-us",
        "Authorization": "Bearer 3d7bf5a8-cc7f-4090-b8c7-c97e15f9e05c",
        "If-None-Match": 'W/"10f4-J0sB6vK/KgYpSKNr5YRm0rnxA1A"',
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.0.0"
    }
    
    doi = doi.replace("/", "%2F")
    res = requests.get(
        url=f"https://api.thirdiron.com/v2/articles/doi%3A{doi}?include=issue,journal&reload=true",
        headers=headers
    )
    # print(res.content)
    
    try:
        full_text_url = json.loads(res.content)["data"]["attributes"]["libkeyFullTextFile"]
    except Exception as e:
        full_text_url = None
    
    return full_text_url


get_full_text_url(doi="10.1111/joes.12448")


# In[7]:

print("Get Article Details ...")
article_details = get_article_details()

publisher_list = ["Springer", "Emerald", "Routledge", "SAGE", "Wiley"]
article_details = [item for item in article_details if item['publisher'] in publisher_list]


# In[8]:


def get_embedding(string):
    embedding = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=string
    )
    return embedding["data"][0]["embedding"]


def cos_sim(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    return v1.dot(v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


# In[9]:


print("Getting Embeddings ...")
abstract_embedding = []
for article in article_details:
    abstract_embedding.append(get_embedding(article["abstract"]))

question_embedding = get_embedding(research_question)


# In[10]:


abstract_similar = [cos_sim(question_embedding, item_embedding) for item_embedding in abstract_embedding]
# print(abstract_similar)


# In[11]:


def find_max_indices(lst, n=15):
    indices = sorted(range(len(lst)), key=lambda i: lst[i], reverse=True)[:n]
    return indices

print("Find Most Relevant Articles ...")
max_indices = find_max_indices(abstract_similar)
article_details_filter = [article_details[idx] for idx in max_indices]


# In[12]:


print("Getting Article URLs ...")
for item in article_details_filter:
    item["url"] = get_full_text_url(item["doi"])
article_details_filter = [item for item in article_details_filter if item['url'] is not None]


# In[13]:


pickle.dump(article_details_filter, open("article-details.pkl", "wb"))
# print(len(article_details_filter))
