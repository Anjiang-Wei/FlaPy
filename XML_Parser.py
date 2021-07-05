#!/usr/bin/python
# coding: utf-8

# In[1]:

import os
import re
import sys
import string
import requests


from csv import writer
import keyword
import xml.etree.ElementTree as ET

# In[3]:


def append_list_as_row(file_name, list_of_elem):
	# Open file in append mode
	with open(file_name, 'a+', newline='',encoding='utf-8') as write_obj:
	   csv_writer = writer(write_obj)
	   csv_writer.writerow(list_of_elem)



List_data = []

print("***********************************************************************************************************")
print("*                                   Code coverage collection                                               ")
print("***********************************************************************************************************")
print(len(sys.argv))

print(sys.argv)
repo = sys.argv[1]
test_to_be_run = sys.argv[2]
project = sys.argv[3]



List_data.append(project)
List_data.append(test_to_be_run)
test_to_be_run = test_to_be_run.replace('/','.')


print(repo)
print(test_to_be_run)
print(project)
print(repo.split('local'))

repo_dir = 'local'+ repo.split('local')[1]
print(repo_dir)

#coverage_xml = repo_dir+"/"+project+"_coverage1"+test_to_be_run+".xml"

coverage_xml = repo_dir+"/"+"coverage.xml"
# In[12]:

tree = ET.parse(coverage_xml)
root = tree.getroot()
# all items data


# In[128]:


for c_node in root.findall('sources/source'):
    file_dir = c_node.text



source_file = repo_dir+"/"
count = 0
list_line = []
for country in root.findall('packages/package/classes/class'):
    filename = country.get('filename')
    result = {}
    if 'local/hdd/' in filename:
    	filename = 'local/hdd/'+ filename.split('local/hdd/')[1]
    	result['file'] = filename
    elif 'usr' in filename:
        result['file'] = filename
    else:
    	result['file']  = source_file + filename
    list_lines = []
    for child in country.findall('lines/line'):
        line = child.get('number')
        hits = child.get('hits')
        if int(hits) == 1 :
            list_lines.append(int(line))
    list_lines  = [i -1 for i in list_lines]
    result['lines'] = list_lines
    list_line.append(result)


# In[133]:
List_code = []
for elem in list_line:
        print(elem['file'])
        print(elem['lines'])
        try :

             file_r = open(elem['file'],'r', encoding='utf-8')
             for position, line in enumerate(file_r):
                    if position in elem['lines']:
                          print(line)
                          List_code.append(line)
        except:
             pass
code_identifers = " ".join(List_code)
print(code_identifers)


List_data.append(code_identifers)

append_list_as_row('test_coverage.csv', List_data)
