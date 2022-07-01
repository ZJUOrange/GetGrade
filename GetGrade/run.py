# daka 函数改写自 https://github.com/Tishacy/ZJU-nCov-Hitcarder/blob/master/daka.py，该脚本可以实现定点打卡
from ast import Param
import string
import pandas as pd
import os
import requests
import re
import json
import time
import getpass
import sys 
import threading
sys.path.append("..") 
from zjuam import ZJUAccount
class Course():
    def __init__(self,code,name,score,credit,five):
        self.code=code
        self.term=code[0:13]
        self.name=name
        self.credit=credit
        if(score=="缺考" or score=="弃修"):
            self.score="0"
        elif(score=="及格"):
            self.score="60"
        elif(score[0].isalpha()):
            self.score=90-(4.5-float(five))*10
            self.score=str(int(self.score))
        else :
            self.score=score
        if float(self.score)<60 :
            self.credit="0"
        self.five=float(five)
        self.four=self.fourgrade()
    def fourgrade(self):
        if(self.five>=4):
            return 4
        else :
            return self.five
    def print(self):
        if(self.five!=0):
            print(self.code+"  "+self.name+" "+self.credit+" "+"得分:"+self.score+"/"+str(self.five))
        else :
            print(self.code+"  "+self.name+" "+self.credit+" "+"得分:"+"挂科")
        
class Term():
    def __init__(self,term):
        self.term=term
        self.CourseList=[]
    def AddCourse(self,Course):
        if(Course.term==self.term):
            self.CourseList.append(Course)
    def GetGPA(self):
        totalscore_5=0
        totalscore_4=0
        totalscore=0
        totalcredit=0
        for course in self.CourseList:
            credit=float(course.credit)
            totalscore_5+=(credit*course.five)
            totalscore_4+=(credit*course.four)
            totalscore+=(credit*float(course.score))
            totalcredit+=credit
        self.GPA_5=totalscore_5*1.0/totalcredit
        self.GPA_4=totalscore_4*1.0/totalcredit
        self.GPA=totalscore*1.0/totalcredit
        self.TermCredit=totalcredit
    def print(self):
        print("============="+self.term+"=============")
        for course in self.CourseList:
            course.print()
        self.GetGPA()
        print("学期获得学分: "+str(self.TermCredit))
        print("百分制："+str(self.GPA))
        print("五分制："+str(self.GPA_5))
        print("四分制："+str(self.GPA_4))
        

class Grade():
    def __init__(self,htmldata):
        data = pd.read_html(htmldata)
        self.Data = {k: str(v).split()[8:] for k, v in data[2].groupby(0)}
        self.YearList=[]
        self.TermList=[]
    def DecodeData(self):
        i=len(self.TermList)-1
        for k,v in self.Data.items():
            if k != "选课课号" and v[1] != "合格":
                course=Course(k,v[0],v[1],v[2],v[3])
                if(i==-1 or self.TermList[i].term !=course.term):
                    self.TermList.append(Term(course.term))
                    i+=1
                self.TermList[i].AddCourse(course)
                
    def print(self,mode):
        self.DecodeData()
        if mode =="AllTerm":
            for term in self.TermList:
                term.print()
        if mode == "newest":
            self.TermList[-1].print()
def dft2(sess, headers):
    try:
        sess.get('http://jwbinfosys.zju.edu.cn/default2.aspx', headers=headers)
    except:
        pass

def Getdata(config):
    username = config["username"]
    password = config["password"]
    if not (username and password):
        print('未能获取用户名和密码，请手动输入！')
        username = input("👤 浙大统一认证用户名: ")
        password = getpass.getpass('🔑 浙大统一认证密码: ')
    zju = ZJUAccount(username, password)
    sess = zju.login()
    sess.keep_alive = True
    base_url = "http://jwbinfosys.zju.edu.cn/xscj.aspx?xh=" + username
    trialCount=0
    while trialCount < 10:
            thread = threading.Thread(target = dft2, args = (sess, sess.headers))
            thread.start()
            time.sleep(1)
            res = sess.get(url=base_url,headers=sess.headers)
            html = res.content.decode('gb2312')

            matchResult = re.search('name="__VIEWSTATE" value="(.*?)"', res.text)
            if (str(matchResult) != 'None'):
                break
            trialCount += 1
            print("[log] 尝试读取数据失败，尝试第 " + str(trialCount) + " 次")
    
    viewstate = matchResult.group(1)
    data = {
        '__VIEWSTATE': viewstate,
        'ddlXN': '',
        'ddlXQ': '',
        'txtQSCJ': '',
        'txtZZCJ': '',
        'Button2': '%D4%DA%D0%A3%D1%A7%CF%B0%B3%C9%BC%A8%B2%E9%D1%AF'
    }
    res = sess.post(url=base_url, data=data,headers=sess.headers)
    res.encoding = res.apparent_encoding
    return res
if __name__ == "__main__":
    configs = json.loads(open('./config.json', 'r').read())
    for i in range(len(configs)):
        config=configs[i]
        if(config["status"]=="on"):
            mygrade=Grade(Getdata(config).text)
            mygrade.print("AllTerm")

    