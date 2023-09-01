import os 
from paper_framer import title_splitted_document
from langchain.chat_models import ChatOpenAI
from summarize import summary
from langchain import PromptTemplate, OpenAI, LLMChain
import json
import pickle
import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def get_identify_variable_template():
    template = """
    
    Assuming you are an economist, and you are writing an academic paper. Now you have literatures which is highly correlated with the paper you write.

    Given the summary of this literature, please output the research question, and variables of the paper.

    You can get the research question, and variables of the literature throught following step:
    
    Step 1:

    First, you need to identify the research question into the following format. For example, the impact of A on B or the application of A on B.

    Step 2:

    Then, extract the research variables in the research question, for example, A and B are the research variables in the research question in the Step1.
    
    Step 3:
    
    Finally, return a json which include the research question get in Step 1 and research variables, namely A and B in the Step 2.
    
    The summary is given following:

    Summary:
    {summary}
    
    Now, please return the json in the following format:{json_format}
    """
    
    return template

def get_variable(summary,llm):
    variable_template = get_identify_variable_template()
    json_format = '{"Research question": the research question,"A":variable_A,"B":variable_B}'
    prompt=PromptTemplate(template = variable_template,
                      input_variables=['summary','json_format'])
    variable_chain = LLMChain(prompt=prompt, llm=llm)
    output = variable_chain.run({'summary':summary,'json_format':json_format})
    return output


def get_embedding(text, model="text-embedding-ada-002"):
   text = text.replace("\n", " ")
   return openai.Embedding.create(input = [text], model=model)['data'][0]['embedding']

import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def get_embedding(text, model="text-embedding-ada-002"):
   text = text.replace("\n", " ")
   return openai.Embedding.create(input = [text], model=model)['data'][0]['embedding']


def get_classification(paper_list,x,y):
    embed_x = get_embedding(x)
    embed_y = get_embedding(y)
    
    for element in paper_list:
        x_0=element['A']
        y_0=element['B']
        embed_x_0 = get_embedding(x_0)
        embed_y_0 = get_embedding(y_0)
        x_score = cosine_similarity([embed_x], [embed_x_0])[0][0]
        y_score = cosine_similarity([embed_y], [embed_y_0])[0][0]
        element.update({'score':{'x_score':x_score,'y_score':y_score}})
    
    s_x_s_y =[]
    s_x_d_y =[]
    d_x_s_y =[]
    d_x_d_y =[]
    
    for paper in paper_list:
        if paper['score']['x_score']>=0.82  and paper['score']['y_score']>=0.82:
            s_x_s_y.append(paper)
        else:
            if paper['score']['x_score']>=0.82 and paper['score']['y_score']<0.82:
                s_x_d_y.append(paper)
            elif paper['score']['x_score']<0.82 and paper['score']['y_score']>=0.82:
                d_x_s_y.append(paper)
            elif paper['score']['x_score']<0.82  and paper['score']['y_score']<0.82:
                d_x_d_y.append(paper)
        
    return [s_x_s_y,s_x_d_y,d_x_s_y,d_x_d_y]

def complete_the_review(paper_group,content):
    summary_group = []
    for element in paper_group:
        summary_group.append([element['summary'],'; '.join(element['author_info']['author']),element['author_info']['year']])
    new_summary_group = []
    for element in summary_group:
        new_info = "Author: " + element[1] + "Published year:" + element[2] + "Summary:" + element[0]
        new_summary_group.append(new_info)
    
    summary_group = '/n/n/n'.join(new_summary_group)
        
    
    template = """
    You are a helpful writing assistant which is good at writing literature review.
    
    Given the summary of several literatures, please write a literature review about {content} for me.
    
    The author, publish year and summary of several literature is following:
    
    {summary_group}
    
    Now, please write a concise literature review according to the summary above
    """
    
    prompt=PromptTemplate(template = template,
                      input_variables=['summary_group','content'])
    
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    
    lit_summary = llm_chain.run({'summary_group':summary_group,'content':content})

    
    return lit_summary


def
os.chdir("D:\\Singapore Management University\\SMU HACKTHON\\Literature Review")
# !python get-articles.py
!python download-pdf.py

article_details = pickle.load(open("article-details2.pkl", "rb"))
pdf_list = [element['pdf'] for element in article_details]
author_info = [{'author': element['author'],'year':element['year']} for element in article_details]
os.environ["OPENAI_API_KEY"] = ""
llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
paper_list = []
for file,info in zip(pdf_list,author_info):
    try:
        summary_paper,splitted_document = summary(file,llm)
        variable = get_variable(summary_paper,llm)
        variable_dict = json.loads(variable)
        paper_info = variable_dict
        paper_info['file'] = file
        paper_info['summary'] = summary_paper
        paper_info['splitted_document'] = splitted_document
        paper_info['author_info'] = info
        paper_list.append(paper_info)
    except:
        pass
    
classify_group = get_classification(paper_list,'political connection','accounting conservatism')

x = 'political connection'
y = 'accounting conservatism'
for paper_group in classify_group:
    if paper_group == classify_group[0]:
        content = f"The impact of {x} on {y}"
        if paper_group!=[]:
            part_review = complete_the_review(paper_group,content)
        else:
            part_review = 'No literature are in this part'
    elif paper_group == classify_group[1]:
        content = f"The impact of {x}"
        if paper_group!=[]:
            part_review = complete_the_review(paper_group,content)
        else:
            part_review = 'No literature are in this part'
    elif paper_group == classify_group[2]:
        content = f"The impact of {y}"
        if paper_group!=[]:
            part_review = complete_the_review(paper_group,content)
        else:
            part_review = 'No literature are in this part'
    elif paper_group == classify_group[3]:
        content = "Irrevevant literature on the topic of impact of {x} on {y}"
        if paper_group!=[]:
            part_review = complete_the_review(paper_group,content)
        else:
            part_review = 'No literature are in this part'
    print(content) 
    print(part_review) 

    


    
    