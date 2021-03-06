# -*- coding: utf-8 -*-
"""
Created on Mon May 02 16:04:53 2016

@author: minxu

Question class for crawling and storing information of a question in zhihu.com.

features:
question title and topics, top answers and votes, popularity information, supports
both file and database storage type

constructor:
specify question id, session and optional MongoDB database object (default is None).
If database is specified, storage mode will be database instead of file

methods:
evaluate(): evaluate fields
flush(): flush all information for this question to file/database depending on 
the storage mode

fields:
    field = {
            'qid' : question_id,
            'url' : question_url,
            'anum' : answer_number,
            'title' : question_title,
            'question' : question_details,
            'labels' : [list_of_question_topic_labels],
            'answers' : [list_of_answers_struct {
                'agrees' : number_of_agrees,
                'text' : answer_text,
                'url' : answer_url,
                'aid' : answer_id
            }]
    }

"""
from bs4 import BeautifulSoup
import os
import os.path
import json
import pymongo
import random

__DEBUG__ = False
__LOG__ = False

main_dir = os.path.realpath('..')
zhihu_url = "https://www.zhihu.com"
subdir = '/questions/'
LOG = main_dir + '/logs/'
TIMEOUT = 20
user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0"
SLEEPTIME = 0.01


class Question:
    
    def __init__(self, qid, session, user_agents = [user_agent], proxies = None, db = None):
        self.url = zhihu_url + '/question/' + qid
        self.qid = qid
        self.session = session
        self.db = db
        self.user_agents = user_agents
        self.proxies = proxies
        if __LOG__:
            self.log = open(LOG + self.qid + '.log', 'w')
    
    #evaluate all fields from the responded html for this question
    def evaluate(self):
        connected = False
        while not connected:
            try:
                self.soup = BeautifulSoup(self.session.get(self.url, \
                    timeout = TIMEOUT, proxies = {
                        'https': random.choice(self.proxies)                    
                    }).text)
                connected = True
            except Exception as e: 
                if __DEBUG__:
                    print self.qid, e
                if __LOG__:
                    self.log.write(str(e) + '\n')
        
        try:
            self.get_title()
        except AttributeError as e:
            if __DEBUG__:
                print self.qid, e
            if __LOG__:
                self.log.write(str(e) + '\n')
            self.title = '404'
        
        if self.title is not '404':
            self.get_question()
            self.get_labels()
            self.get_answers()
            self.get_anum()
        else:
            self.question, self.labels, self.answers, self.anum = '404', [], [], 0
    
    #wrapper for flush all information for this question to file/database 
    #depending on the storage mode 
    def flush(self):
        if self.db is None:
            self.flush_to_file()
        else:
            self.flush_to_db()
        if __LOG__:
            self.log.close()
    
    #flush data to database
    def flush_to_db(self):
        try:
            self.db.questions.insert_one(self.construct_data())        
        except pymongo.errors.DuplicateKeyError:
            self.db.questions.delete_one({'_id' : self.qid})
            self.db.questions.insert_one(self.construct_data())
    
    #flush data to file in json format
    def flush_to_file(self):
        json_dict = self.construct_data()
        with open(main_dir + subdir + self.qid + '.json', 'w') as f:
            json.dump(json_dict, f, indent=4)
    
    #construct data in dictionary type
    def construct_data(self):
        data = {
            '_id' : self.qid, #for MongoDB
            'qid' : self.qid,
            'url' : self.url,
            'anum' : self.anum,
            'title' : self.title,
            'question' : self.question,
            'labels' : self.labels,
            'answers' : self.answers
        }
        return data
    
    #get number of answers
    def get_anum(self):
        qn = self.soup.find('h3', id = "zh-question-answer-num")
        if qn is not None:
            self.anum = int(qn['data-num'])
        else:
            self.anum = len(self.answers)
    
    #get the question title text
    def get_title(self):
        self.title = self.soup.find('h2', class_ = \
            "zm-item-title zm-editable-content").find(text = True).strip()
        
    #get the question details text
    def get_question(self):
        qd = self.soup.find('div', id = "zh-question-detail"). \
            find('div', class_ = "zm-editable-content")
        if qd is not None:
            self.question = qd.text.strip()
        else:
            self.question = self.soup.find('div', id = "zh-question-detail"). \
                find('textarea', class_ = "content").text.strip()
            
    #get a list of topic labels associated
    def get_labels(self):
        self.labels = []
        lbs = self.soup.find('div', class_ = "zm-tag-editor-labels zg-clear")
        if lbs is not None:
            ls = lbs.findAll('a')
            for l in ls:
                self.labels.append(l.find(text = True))
    
    #get a list of answers structure, with number of agrees, text, url and id
    def get_answers(self):
        self.answers = []
        for a in self.soup.findAll('div', class_ = 'zm-item-answer  zm-item-expanded'):
            url = a.find('link', itemprop="url")['href']
            aid = url.split('/')[4]
            url = zhihu_url + url
            agrees = a.find('div', class_ = "zm-votebar").find('span', class_ = "count").text
            if 'K' in agrees:
                agrees = float(agrees[0:-1]) * 1e3
            agrees = int(agrees)
            ts = a.find('div', class_ = "zm-editable-content clearfix")
            if ts is not None:
                text = ts.text
                answer = {
                    'agrees' : agrees,
                    'text' : text,
                    'url' : url,
                    'aid' : aid
                }
                self.answers.append(answer)

#check if this question object exists in database or file
def check_question(qid, db = None):
    if db is None:
        return os.path.exists(main_dir + subdir + qid + '.json')
    else:
        return db.questions.find({'_id' : qid}).count() != 0

#crawl the question with given qid to disk, return the dictionary for this question
def crawl_question(qid, session, user_agents = [user_agent], proxies = None, db = None):
    if not check_question(qid, db):
        print 'creating question ' + qid
        q = Question(qid, session, user_agents, proxies, db)
        q.evaluate()
        q.flush()
        print 'created question ' + qid
            
    if db is not None:
        return db.questions.find_one({"_id" : qid})
    else:
        with open(main_dir + subdir + qid + '.json') as f: 
            return json.load(f)