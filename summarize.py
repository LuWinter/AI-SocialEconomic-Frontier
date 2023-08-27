from langchain import PromptTemplate, OpenAI, LLMChain
from paper_framer import title_splitted_document
import os 
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA


def summary(path,llm):
    splitter_document = title_splitted_document(path = path)
    embeddings = OpenAIEmbeddings()
    docsearch = Chroma.from_documents(splitter_document, embeddings)
    summary_list = get_question_answer(docsearch,llm)
    summary = get_all_summary(summary_list,llm)

    return summary,splitter_document


def get_question_answer(docsearch,llm):
    qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=docsearch.as_retriever(search_kwargs={"k": 3}))
    result_list = []
    question_list = [
        "What problem does this article research on?",
        "What research method is this article used?,what potential issues did their research methodology circumvent?",
        "What data is this article used?",
        "What is the research finding of this article?"
    ]
    
    for query in question_list:
        result = qa.run(query)
        result_list.append(result)
        
    return result_list


def get_all_summary(output,llm):
    
    prompt_template = """
    
    You are a helpful writing assistant, you are good at writing summary of academic paper.
    
    Given the research problem, research method, the data description, research findings.
    
    Write a precise summary, which include the content mentioned above, with a clear structure and rigor logic.
    
    
    ===========
    Research problem:
    
    {research_problem}
    
    ===========
    Research_method:
    
    {research_method}
    
    ===========
    Data_description
    
    {data_description}
    
    ===========
    Research_findings
    
    {research_findings}
    
    ===========
    
    Please make sure your summary should be precise and shorter than 400 words.
    
    """
    
    prompt=PromptTemplate(template = prompt_template,
                      input_variables=['research_problem','research_method','data_description','research_findings'])
    
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    
    summary = llm_chain.run({
        'research_problem':output[0],
        'research_method':output[1],
        'data_description':output[2],
        'research_findings':output[3]})
    
    return summary
