##获取文件夹文件
import re
from fuzzywuzzy import fuzz
from langchain import PromptTemplate, OpenAI, LLMChain
from langchain.chat_models import ChatOpenAI
from PyPDF2 import PdfFileReader
import os
from langchain.document_loaders import UnstructuredPDFLoader
from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyMuPDFLoader


###第一项总策略
def pdf_outline_strategy(pdf_path):
    outline,section,metainfo,layer=get_pdf_outline(pdf_path)
    if outline == []:
        return None,None
    else:
        title_list = get_pdf_title_element(pdf_path)
        true_title,true_layer = outline_match(outline,title_list,layer)
        if true_title == "None":
            return None,None
        else:
            true_title,true_layer = only_one_check(true_title,true_layer)
        return true_title,true_layer
    

## 获取PDF标题碎片
from langchain.document_loaders import UnstructuredPDFLoader
def get_pdf_title_element(pdf_path):
    loader = UnstructuredPDFLoader(pdf_path,mode="elements")
    data = loader.load()
    title = []
    
    for element in data:
        title.append(element.page_content)
            
    
    
    return title


###读取源标题,返回标题名，标题全信息，文档源信息，标题层级数
def get_pdf_outline(pdf_path):
    with open(pdf_path, 'rb') as f:
        pdf = PdfFileReader(f)
        text_outline_list = pdf.getOutlines()
        metainfo = pdf.getDocumentInfo()
        section,layer = outline_process(text_outline_list)
        if section!= []  and section[0]['Page'] != 'None' and section[0]['Page']>100:
            outline = section
            outline.pop(0)
            layer.pop(0)
            outline = [element['Title'] for element in outline]
        else:
            outline = [element['Title'] for element in section]
        return outline,section,metainfo,layer


def bookmark_listhandler(outline,section,count,layer):
    count = count+1
    for message in outline:
        if isinstance(message, dict):
            section.append({'Title':message['/Title'],'Page':get_page(message)})
            layer.append(count)
        else:
            bookmark_listhandler(message,section,count,layer)
    return section,layer


#section是标题名，layer是标题层级
def outline_process(outline):
    
    count = 0
    section = []
    layer = []
    section,layer = bookmark_listhandler(outline,section,count,layer)
    
    return section,layer


def get_page(message):
    try:
        page = message['/Page']
        if "/Annots" in message['/Page'].keys():
            str_page = str(message['/Page']['/Annots'][0])
        elif "/Contents" in message['/Page'].keys():
            str_page = str(message['/Page']['/Contents'])
        else:
            str_page = "None"
        page_number = re.search(r'\((\d+)', str_page)
        if page_number:
            number = page_number.group(1)
            return int(number)
        else:
            return 'None'
    except Exception as e:
        number = 'None'
        return number
    
    
####模糊匹配，找出真标题，并将匹配失败的结果传出
def outline_match(outline,title_list,layer):
    ##直接匹配
    true_title = []
    for element in outline:
        score = []
        for title in title_list:
            similarity = fuzz.ratio(title,element)
            score.append(similarity)
        highest = max(score)
        if highest>=70:
            true_title.append(title_list[score.index(highest)])
        else:
            #直接匹配失败，则统一大小写和空格匹配
            element = element.replace(" ","").lower()
            second_score = []
            for title in title_list:
                title = title.replace(" ", "").lower()
                similarity = fuzz.ratio(title,element)
                second_score.append(similarity)
            second_highest = max(second_score)
            if second_highest>=70:
                true_title.append(title_list[second_score.index(second_highest)])
            else:
                true_title.append("Miss")
   #检测超标             
    ratio = miss_check(true_title)
    if ratio>=0.5:
        true_title = "None"
        true_layer = "None"
    else:
        positions = [index for index, value in enumerate(true_title) if value == "Miss"]
        for index in positions:
            layer[index] = "remove"
        true_layer = [element for element in layer if element != "remove"]
        true_title = [element for element in true_title if element != "Miss"]
        
                
            
    return true_title,true_layer


###检测Miss是否超标
def miss_check(true_title):
    count = true_title.count("Miss")
    ratio = count/len(true_title)
    
    return ratio


##检查是否true_title里存在重复,并输出无重复组合
def only_one_check(true_title,true_layer): 
    element_positions={}
    repeat_list = []
    remove_index = []
    for index, value in enumerate(true_title):
        if value in element_positions:
            element_positions[value].append(index)
        else:
            element_positions[value] = [index]
    for element, positions in element_positions.items():
        if len(positions) > 1:
            repeat_list.append({element:positions})
    for repeat_element in repeat_list:
        new_index = list(repeat_element.values())[0][1:]
        remove_index.append(new_index)
    remove_index = [element for elements in remove_index for element in elements]
    for index in remove_index:
        true_layer[index]="|||||"
    true_layer = [element for element in true_layer if element != "|||||"]
    seen = set()
    ### 如果and前面没有判定成功则不会执行，如果判定成功，由于seen.add返回为None,因此not None永远为True，因此一定会被执行
    true_title = [item for item in true_title if item not in seen and not seen.add(item)]
    
    return true_title,true_layer  
    

    ##第二项总策略
def alter_outline_strategy(pdf):
    candidate = block_information_extract(pdf)
    true_title = similar_title_strategy(candidate)
    true_title = fake_title_cleaned(true_title)
    if true_title ==None:
        return None
    else:
        true_title = remove_name(true_title)
        
    return true_title


## 抽取模块的信息
import fitz
import os
def block_information_extract(pdf_path):
    #先获取PDF每个模块的字体大小；字体格式；字体；内容
    doc = fitz.open(pdf_path)
    block_list = []
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block["type"] ==0:
                for line in block["lines"]:
                    for span in line["spans"]:
                        block_list.append({"Size":span["size"],"Flags":span['flags'],"Font":span['font'],"Text":span["text"]})

    return block_list


## 类标题匹配策略
def similar_title_strategy(candidate):
    true_title = title_strategy(candidate,'reference')
    if true_title == None:
        true_title = title_strategy(candidate,'introduction')
        if true_title == None:
            true_title = title_strategy(candidate,'conclusion')
    return true_title
        

##reference匹配策略
def title_strategy(candidate,title_name):
    score = []
    for x in candidate:
        similarity = fuzz.ratio(title_name,x['Text'].lower())
        score.append(similarity)
    
    highest = max(score)
    if highest>=80:
        title = candidate[score.index(highest)]
    else:
        return None
    true_title_list = []
    for y in candidate:
        if y['Font'] == title['Font'] and y['Flags'] == title['Flags'] and y['Size'] == title['Size']:
            true_title_list.append(y)
    if len(true_title_list) <=3:
        return None
    else:
        return true_title_list


def fake_title_cleaned(true_title):
    if true_title == None:
        return None
    #长度清洗
    true_title = [element for element in true_title if len(element['Text']) >= 6 and len(element['Text']) <= 120]
    #去除图表,标题,https
    clean_title = []
    for element in true_title:
        table_similarity = fuzz.ratio('table',element['Text'].replace(" ","").lower())
        figure_similarity = fuzz.ratio('figure',element['Text'].replace(" ","").lower())
        if table_similarity <70 and figure_similarity <70 and "https" not in element['Text']:
            clean_title.append(element)
    if len(clean_title)>20 or len(clean_title)<=4:
        return None
    for element in clean_title:
        if len(element['Text'])>70:
            return None
        
    return clean_title
        
    
###删除标题中的异物内容和检测是否是标题


def combine_title(true_title):
    true_title = "/n/n".join(true_title)
    
    return true_title


#去除其中的名字
def remove_name(true_title):
     os.environ["OPENAI_API_KEY"] = ""
     llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
      
     true_title= [element['Text'] for element in true_title]
     str_title = combine_title(true_title)
    
     
     
     prompt_template = """
     
     You are a helpful assistant which good at finding out the author names in the text.
     
     First, I will show you some examples of author name:
     1.Giovanni Dell’Ariccia
     2.and Damiano Sandri
     3.Anton Skrobotov
     4.Guo Feng
     5.Eyal Zamir
     
     Given the text, please return the author name in the text through following steps:
     Step1:
     Check if there are any author name in the text. If there are author names in the text, go to Step 2. Otherwise, return None.
     
     Step2:
     Only return all the author name in the text, and split them by /n.
     
     The text given is following:
     {true_title}
     
     Please return None or the author name. You can not return other things.

     """
     prompt=PromptTemplate(template = prompt_template,input_variables=['true_title'])
                          
     llm_chain = LLMChain(prompt=prompt, llm=llm)
     remove = llm_chain.run({'true_title':str_title})
        
     if remove == "None":
        return true_title
     else:
        remove_name = remove.split('/n/n')
        for x in remove_name:
            if x in true_title:
                true_title.remove(x)
        return true_title


def need_extract(pdf_path):
    with open(pdf_path, 'rb') as f:
        pdf = PdfFileReader(f)
        text_outline_list = pdf.getOutlines()
        if text_outline_list ==[]:
            return pdf_path
        

def extract_list(path):
    extract_list = []
    path_list = os.listdir(path)
    for pdf_path in path_list:
        extract_list.append(need_extract(pdf_path))
    extract_list = [element for element in extract_list if element != None]
    return extract_list


###切分程序
def first_split_document(path,true_title):
    loader = UnstructuredPDFLoader(path)
    data = loader.load()
    page_content = data[0].page_content
    meta_data = data[0].metadata
    
    document = {}
    count = 0 
    for title in true_title:
        part_content = page_content.split(title)[0]
        page_content = page_content.split(title)[1:]
        if page_content == []:
            page_content = part_content
            count = count+1
            continue
        else:
            if len(page_content)>1:
                page_content = "".join(page_content)
            else:
                if page_content !=[]:
                    page_content=page_content[0]
            if count == 0:
                key = "Front"
                document[key]=part_content
            elif count == len(true_title)-1:
                key_1 = true_title[-2]
                key_2 = true_title[-1]
                document[key_1]=part_content
                document[key_2]=page_content
            else:
                key = true_title[count-1]
                document[key]=part_content
            count = count+1
    
    full_document = {"document":document,"metadata":meta_data}
        
        
    
    return full_document


###层级key
def layer_key_name_first_strategy(document_title_no_layer,true_layer):
    count = 0
    update_title = []
    layer_count = true_layer[0]
    last_name = []
    for original in document_title_no_layer[:-1]:     
        if true_layer[count+1] == layer_count:
            update_title.append('-'.join(last_name) + " - " +document_title_no_layer[count])
        elif true_layer[count+1] > layer_count:
            update_title.append('-'.join(last_name) + " - " +document_title_no_layer[count])
            last_name.append(document_title_no_layer[count])
            layer_count = layer_count+1
        elif true_layer[count+1]<layer_count:
            update_title.append('-'.join(last_name) + " - " + document_title_no_layer[count])
            while true_layer[count+1]!=layer_count:
                last_name.pop()
                layer_count = layer_count-1
        count = count+1
    new_update_title = []
    for element in update_title:
        if element[0] == '-':
            new_update_title.append(element[1:])
        else:
            new_update_title.append(element)
        
    return new_update_title


## 原始切分程序
def old_splitter(path):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 5500,
                                               chunk_overlap  = 300,
                                               length_function = len)
    docs = PyMuPDFLoader(path).load()
    page_content = ''
    metadata = docs[0].metadata
    for doc in docs:
        page_content = page_content+doc.page_content
    docs = [Document(page_content = page_content,metadata=metadata)]
    split_text = text_splitter.split_documents(docs)
        
    return split_text


###对大文本再切分
def secondary_split_document(splitter_document):
    new_splitter_document = splitter_document
    for element in splitter_document:
        if word_count(element)> 1500:
            long_document_list = split_long_document(element)
            new_splitter_document[new_splitter_document.index(element)] = long_document_list
    splitter_document = []
    for element in new_splitter_document:
        if isinstance(element, list):
            for x in element:
                splitter_document.append(x)
        else:
            splitter_document.append(element)
    return splitter_document


##统计每个document的字数
def word_count(document):
    content = document.page_content
    count = len(split_text_with_multiple_delimiters(content,' ', '/n'))
    
    return count


##单字符串多字符切分
def split_text_with_multiple_delimiters(text, delimiter1, delimiter2):
    # 将两个分隔符合并成一个正则表达式
    combined_delimiter = f"{re.escape(delimiter1)}|{re.escape(delimiter2)}"
    
    # 使用正则表达式进行分割
    parts = re.split(combined_delimiter, text)
    
    return parts


###对字数过多的document切分
def split_long_document(document):
    content = document.page_content
    content_list = split_text_with_multiple_delimiters(content,' ', '/n')
    long_document_list = []
    current_document = ['']
    for element in content_list:
        if len(current_document) <=1000:
            current_document.append(element)
        else:
            long_document_list.append(Document(page_content = ' '.join(current_document),metadata = document.metadata))
            current_document = ['']
        if element == content_list[-1]:
            long_document_list.append(Document(page_content = ' '.join(current_document),metadata = document.metadata))
            
    return long_document_list


##替换列表多元素
def replace_element_with_list(original_list, index_to_replace, replacement_list):
    # 确保索引有效
    if 0 <= index_to_replace < len(original_list):
        # 在原列表中用切片分割，然后用替换列表拼接
        new_list = original_list[:index_to_replace] + replacement_list + original_list[index_to_replace+1:]
        return new_list
    else:
        print("Invalid index to replace")
        return original_list


###错误检查类

# 检查title内是否有重复

def fake_double_check(true_title):
    if true_title == None:
        return None
    for element in true_title:
        if len(element) > 100:
            return None
    return true_title

## 检查总共有多少字数
def check_total_str(splitter_document):
    total_count = 0
    for element in splitter_document:
        total_count = total_count+ len(element.page_content)
    return total_count


def title_splitted_document(path):
    true_title, true_layer= pdf_outline_strategy(path)
    true_title = fake_double_check(true_title)
    if true_title == None:
        true_title = alter_outline_strategy(path)
        if true_title ==None:
            print(f"Failed_path:{path}")
            splitter_document = old_splitter(path)
            return splitter_document
        else:
            ###这一部分的分级部分识别策略存在问题，先暂时跳过
            document = first_split_document(path,true_title)
            splitter_document = []
            for element in document['document'].keys():
                splitter_document.append(Document(page_content = document['document'][element],metadata={'Section':element,'Source':document['metadata']['source']}))
            splitter_document = secondary_split_document(splitter_document) 
            return splitter_document
    else:
        document = first_split_document(path,true_title)
        #层级信息重组，生成Document_list
        document_title_no_layer = [key for key in document['document'].keys()]
        true_layer.insert(0, true_layer[0])
        document_title_with_layer = layer_key_name_first_strategy(document_title_no_layer,true_layer)
        another_document = {}
        for old_key,new_key in zip(document['document'].keys(),document_title_with_layer):
            another_document[new_key] = document['document'][old_key]
        document['document'] = another_document
        splitter_document = []
        for element in document['document'].keys():
            splitter_document.append(Document(page_content = document['document'][element],metadata={'Section':element,'Source':document['metadata']['source']}))
        ##检查字数并对大字数组再切片
        splitter_document = secondary_split_document(splitter_document)
        return splitter_document
    
