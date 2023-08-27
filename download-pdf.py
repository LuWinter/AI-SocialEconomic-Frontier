import os
import time
import pickle
from selenium.webdriver import Edge, EdgeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

folder_path = '/Users/winter/Documents/Python_Projects/PyTorch-NLP/LangChain/output/'
article_details = pickle.load(open("article-details.pkl", "rb"))

options = EdgeOptions()
edge_prefs = {
    "download.prompt_for_download": True,
    "plugins.always_open_pdf_externally": False,
    "download.open_pdf_in_system_reader": False,
    "profile.default_content_settings.popups": 0,
    "download.default_directory": folder_path
}
options.add_experimental_option("prefs", edge_prefs)
options.add_argument('--headless') 
options.add_argument('--disable-gpu') 


driver = Edge(executable_path="/usr/local/bin/msedgedriver", options=options)

driver.get(article_details[0]["url"])
time.sleep(5)

if driver.current_url == 'https://login2.smu.edu.sg/adfs/ls/':
    usr_element = driver.find_element(By.XPATH, '//*[@id="userNameInput"]')
    usr_element.send_keys('wentao.lu.2023@mse.smu.edu.sg')
    psw_element = driver.find_element(By.XPATH, '//*[@id="passwordInput"]')
    psw_element.send_keys('Vip9811@')
    login_button = driver.find_element(By.XPATH, '//*[@id="submitButton"]')
    login_button.click()

for idx, item in enumerate(article_details[1:]):
    print(f"Now downloading the {idx+2} article")
    driver.get(item["url"])
    time.sleep(5)

time.sleep(8)
driver.quit()



file_paths = [os.path.join(folder_path, filename) for filename in os.listdir(folder_path)]

article_details2 = []
for idx, article in enumerate(article_details):
    article["pdf"] = file_paths[idx] 
    article_details2.append(article)
# article_details2 = [article["pdf"] = file_paths[idx] for idx, article in enumerate(article_details)]
pickle.dump(article_details2, open("article-details2.pkl", "wb"))


# file_paths = [file_path for file_path in file_paths if file_path.find(".pdf") != -1]
# file_creation_times = [(file_path, os.path.getctime(file_path)) for file_path in file_paths]
# sorted_files = sorted(file_creation_times, key=lambda x: x[1])

# for idx, file_path in enumerate(file_paths):
#     new_path = folder_path + article_details[idx]["doi"].replace("/", "-") + ".pdf"
#     os.rename(file_path, new_path)
