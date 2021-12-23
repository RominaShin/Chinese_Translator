#!/usr/bin/env python
#-*- coding: utf-8 -*-

#!pip install transformers[all]
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
#import magic
#import shlex
import os
import re
import pickle
import fileinput
import sys

zh2en_model = AutoModelForSeq2SeqLM.from_pretrained('Helsinki-NLP/opus-mt-zh-en')
zh2en_tokenizer = AutoTokenizer.from_pretrained('Helsinki-NLP/opus-mt-zh-en')

saved_model = pickle.dumps(zh2en_model)
saved_tokenizer = pickle.dumps(zh2en_tokenizer)



def translate_text(ch_text):
  """
  pass your chinese text and it returns its english translation
  """

  zh2en_model = pickle.loads(saved_model)
  zh2en_tokenizer = pickle.loads(saved_tokenizer)
  zh2en_translation = pipeline('translation_zh_to_en',
                      model=zh2en_model,
                      tokenizer=zh2en_tokenizer)
  return zh2en_translation(ch_text)

comment_format_start = {'html':['<!--'],'htm':['<!--'],'xml':['<!--'],'js':['//','/*'],'java':['//','/*'],'py':['#']}
comment_format_end = {'html':'-->','htm':'-->','xml':'-->','js':'*/','java':'*/'}

def replace_text(line):
  """
  pass line you want to change and the text before to replace new line
  in new text
  """

  if re.search('[\u4e00-\u9fff]',line) != None:
    #line = line.replace('Hello', 'import')
    #sys.stdout.write(line)

    changes = line.replace(line, translate_text(line)[0]['translation_text'])
    return changes

  else:
    return line

def parse_python(f,replacement):
  closed = True
  for line in f.readlines():
    #print(line)
    if closed:

      if line.strip().startswith('#') :
        replacement.append("#" + replace_text(line.split('#')[1]))

      if len(line.strip().split('#'))>1 and line.strip().split('#')[0] != "" :
        replacement.append(line.strip().split('#')[0]+"{}".format('#')+replace_text(line.strip().split('#')[1]))

      if line.strip().startswith('"""') :
        closed = False
        if line.strip().endswith('"""') and len(line.split('"""'))>2:
          #print(line)
          #replacement.append('"""' +replace_text( line.strip().split('"""')[1] )+ '"""')
          replacement.append(re.findall("^ *",line)[0]+'"""\n' +re.findall("^ *",line)[0] + replace_text( line.strip().split('"""')[1] )+
                             '\n'+re.findall("^ *",line)[0] + '"""\n')
          #print('here')
          closed = True
        else:
          replacement.append(line)

      #

      #re.findall("""(['"])(?:(?=(\\?))\2([\u4e00-\u9fff\d\s\W]))*?\1""",'df_arts["考室30---+-号56451"    " 考 2 zzz  135 "] = "号abc"')

      #if line.strip().startswith('\'') :
        #replacement.append('\'' + replace_text(line.split('\'')[1]))
        #while line.find('\'') == -1:
         # replacement.append(replace_text(line.split('\'')[1]))

        #replacement.append( replace_text(line.split('\'')[1])+'\'' )


      #if line.strip().startswith('\"') :
        #replacement.append('\"' + replace_text(line.split('\"')[1]))
        #while line.find('\"') == -1:
         # replacement.append(replace_text(line.split('\"')[1]))

        #replacement.append( replace_text(line.split('\"')[1])+'\"' )

      else:
        replacement.append(line)

    else:
      #should i add this?
      #replacement.append( replace_text(line.split('"""')[1])+'"""' )
      #print('Im here')
      replacement.append(replace_text(line)+'\n')
      if line.strip().startswith('"""') or line.strip().endswith('"""'):
        #print('im here')
        closed = True

  return replacement


def parse_text(file_type, comment_format_s, f, replacement):
  if file_type == 'py':
    return parse_python(f, replacement)

  else:
    # flag to check if a multiple line comment is done or not
    comment_closed = True

    # flag to check if line is the first line of file
    first_line = True

    if comment_format_end.get(file_type) != None:
      comment_format_e = comment_format_end[file_type]

    if comment_format_s != None:
      # read file line by line
      for line in f.readlines():
        # for mark,line in enumerate(f.readlines()):
        # print(line)

        # checks if it's in the multiple line comment,
        # if not, one line comment cases should be checked
        if comment_closed:

          # for file types containing different comment characters
          for i in comment_format_s:

            # if the comment started from first of line
            if line.strip().startswith(i):
              # replacement.append("{}".format(i) + replace_text(line.strip().split(i)[1]))
              replacement.append(i + replace_text(line.strip().split(i)[1]))
              # print('startswith{}'.format(i),mark)
              # try:

              # if the line hasn't been ended with ending comment character, next lines should be considered as comment
              if not line.endswith(comment_format_e) and len(comment_format_s) > 1:
                if i == comment_format_s[1]:
                  comment_closed = False
              # except NameError:
              else:
                print('one line comment')

            # if comment started from middle of line
            if len(line.strip().split(i)) > 1 and line.strip().split(i)[0] != "":
              replacement.append(line.strip().split(i)[0] + "{}".format(i) + replace_text(line.strip().split(i)[1]))
              # print('contains one line comment',mark)

            # else:
          # if it's first line translate it by the way
          if first_line:
            if len(line.split(comment_format_s[1])) > 1:
              replacement.append(replace_text(line.split(comment_format_s[1])[1]))
            else:
              replacement.append(replace_text(line))

          # append the line to new text if it's not repeated
          if len(replacement) > 0:
            # print(mark)
            if replacement[-1] != line[:line.index('\n')]:
              replacement.append(line)
              # print('no comment found')

        # We are in a multiple line comment, so it should translate it all till it sees ending comment character
        else:
          replacement.append(replace_text(line))
          # print('comment continues',mark)

          if line.find(comment_format_e):
            comment_closed = True

        first_line = False
    # except NameError:

    # file doesn't contain comments and we should search for chinese characters whole th file
    else:
      # print('This file doesnt contain comment')
      for line in f.readlines():
        replacement.append(replace_text(line))

    return replacement


def process_text(input_path):
  f = open(input_path,'a')
  f.write('\n\n\n')
  f.close()
  try:
    f = open(input_path,'r')
    #get type of file based on its name (name.type)
    file_name, file_type = os.path.splitext(input_path)
    file_type = file_type[1:].lower()

    #new text file to be written
    replacement = []

    #try:

    #if the file type contains comment or not (like .md or .txt files)
    #if the file is comment included, checks all possible comment formats
    if comment_format_start.get(file_type) != None:
      comment_format_s = comment_format_start[file_type]
      #print(comment_format_s)
    else:
      comment_format_s =None

    #searches for ending comment character, if the file type supports
    if comment_format_end.get(file_type) != None :
      comment_format_e = comment_format_end[file_type]

    replacement = parse_text(file_type,comment_format_s,f,replacement)

    f.close()
    #write new text in a translated file
    if len(replacement) != 0:
      fout = open("{}_translated.{}".format(file_name,file_type), "w")
      fout.writelines(replacement)
      fout.close()

  except IOError:
    print('No File Found')

def process_text(input_path):
  f = open(input_path,'a')
  f.write('\n\n\n')
  f.close()
  try:
    f = open(input_path,'r')
    #get type of file based on its name (name.type)
    file_name, file_type = os.path.splitext(input_path)
    file_type = file_type[1:].lower()

    #new text file to be written
    replacement = []

    #try:

    #if the file type contains comment or not (like .md or .txt files)
    #if the file is comment included, checks all possible comment formats
    if comment_format_start.get(file_type) != None:
      comment_format_s = comment_format_start[file_type]
      #print(comment_format_s)
    else:
      comment_format_s =None

    #searches for ending comment character, if the file type supports
    if comment_format_end.get(file_type) != None :
      comment_format_e = comment_format_end[file_type]

    replacement = parse_text(file_type,comment_format_s,f,replacement)

    f.close()
    #write new text in a translated file
    if len(replacement) != 0:
      fout = open("{}_translated.{}".format(file_name,file_type), "w")
      fout.writelines(replacement)
      fout.close()

  except IOError:
    print('No File Found')

path = input('Enter your file path, translated file will be saved in same directory: ')
process_text(path)
