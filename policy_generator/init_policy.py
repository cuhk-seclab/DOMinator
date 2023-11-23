from os import path
from bs4 import BeautifulSoup as BS
from urllib.parse import urlparse
from termcolor import colored
import os,json,bs4,sys,getopt

EXP_NUM=3
ROUND="0"
ROOT = os.path.dirname(os.path.realpath(__file__))
EXPPATH = os.path.join(ROOT,"Exp"+str(EXP_NUM))
SOURCE_DIR=os.path.join(EXPPATH,"special","source_logs")
POLICY_DIR=os.path.join(EXPPATH,"policy")
policy_file_name="Result.cpp"

def check_log_source(rank):
    page_file=os.path.join(SOURCE_DIR,rank,"page.html")
    tag_file=os.path.join(SOURCE_DIR,rank,"SensTag.log")
    for file in [page_file,tag_file]:
        if not os.path.isfile(file):
            return False
    return True

def get_sensitive_info(rank):
    dir=os.path.join(SOURCE_DIR,rank)
    file=os.path.join(dir,"SensTag.log")
    sens_list=list()
    if not os.path.isfile(file):
        return sens_list
    f = open(file,"r")
    lines=f.readlines()
    for line in lines:
        if line.startswith("!!!"):
            break
        sens_list.append(line.strip())

    with open(os.path.join(dir,"page.html"), 'r') as f:
        htmlstr = f.read().strip()
        soup = BS(htmlstr,"html.parser")
        html = soup.html
    num_bad,num_good=0,0
    for item in sens_list:
        nodes=html.select(item)
        if not nodes:
            print("Error: Selector Not Found " + item)
            continue
        if len(nodes)>1:
            print("Error: Not Unique Selector" + item)
            print("\n".join([str(x) for x in nodes]))
            continue
        if ' > ' in item:
            num_bad+=1
        else:
            num_good+=1
    num_list=[len(sens_list),num_good,num_bad]
    return num_list, sens_list

def build_rule_str(urls,flag):
    rules=list()
    for u in urls:
        rule_str="\"{url}\":\"{flag}\"".format(url=u,flag=flag)
        rules.append(rule_str)
    return rules

def generate_policy(policy_dir,selectors):
    policy_dir= os.path.join(POLICY_DIR,rank)
    if not os.path.exists(policy_dir):
        os.mkdir(policy_dir)
    policy_dict=dict()
    for item in selectors:
        policy_dict[item]=build_rule_str(["default"],"None")
    num=len(policy_dict)
    # print("Policy:",num)

    policy_file=os.path.join(policy_dir,policy_file_name)
    if policy_dict:
        with open(policy_file,"w") as f:
            for selector, rules in policy_dict.items():
                rules_str=','.join(rules)
                policy_str='''\
                    {selector}
                    {{policy: {{{rules}}};}}
                    '''.format(selector=selector,rules=rules_str)
                f.write(policy_str+'\n')
    return num

with open(path.join(EXPPATH,"rank2domain"), 'r') as f:
    website_list = [x.strip() for x in f.readlines()]
websites=list()
for item in website_list[0:50]:
    rank,domain,url=item.split(";")[0:3]
    websites.append((rank,domain))

for rank,url in websites:
    print("=======Running rank: ",rank, "url: ",url," ===========")
    if not check_log_source(rank):
        print("Error: No File " +rank)
        continue
    nums,selectors=get_sensitive_info(rank)
    generate_policy(rank,selectors)
    print("\tSelector: %d Good: %d Bad: %d" % tuple(nums))
