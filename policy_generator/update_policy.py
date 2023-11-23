import os,json,shutil,getopt,sys
from bs4 import BeautifulSoup as BS
from urllib.parse import urlparse,urljoin

EXP_NUM=3
ROUND=0
ROOT = os.path.dirname(os.path.realpath(__file__))
EXPPATH = os.path.join(ROOT,"Exp"+str(EXP_NUM))

MODE_DIR=os.path.join(EXPPATH,"usability")
DATA_DIR=os.path.join(MODE_DIR,"round"+str(ROUND))
SOURCE_DIR=os.path.join(DATA_DIR,"source_logs")

OUTPUT_DIR=os.path.join(DATA_DIR,"processed_data")
vio_dir=os.path.join(OUTPUT_DIR,"violations")
num_file=os.path.join(OUTPUT_DIR,"numbers")#exception, violation

POLICY_DIR=os.path.join(EXPPATH,"policy")

rank2violations=dict()
rank2page=dict()
ranks=[list(),list(),list(),list()]
rank2url=dict()

navi_websites=set()
noupdate_websites=set()
updated=list()
notfound_websites=set()
websites_needcheck=set()

Exception_log=None
index_range=[0]
def init(round,remove_flag=True):
    global ROUND
    ROUND=round
    if round!=0:
        global index_range
        index_range=[1,2,3]
    global DATA_DIR,SOURCE_DIR,OUTPUT_DIR,vio_dir,num_file
    DATA_DIR=os.path.join(MODE_DIR,"round"+str(ROUND))
    SOURCE_DIR=os.path.join(DATA_DIR,"source_logs")

    OUTPUT_DIR=os.path.join(DATA_DIR,"processed_data")
    vio_dir=os.path.join(OUTPUT_DIR,"violations")
    num_file=os.path.join(OUTPUT_DIR,"numbers")#exception, violation
    if remove_flag and os.path.isdir(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
        
    for item in [OUTPUT_DIR,vio_dir]:
        if not os.path.isdir(item):
            os.mkdir(item)

    global Exception_log
    Exception_log=os.path.join(DATA_DIR,"update_detail_%d.log"%round)
    if remove_flag and os.path.isfile(Exception_log):
        os.remove(Exception_log)


def get_scheme_host(url):
    parsed_uri = urlparse(url)
    result = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    return result

def build_rule(rules):
    rule_str=list()
    for u,flag in rules.items():
        tmp_str="\"{url}\":\"{flag}\"".format(url=u,flag=flag)
        rule_str.append(tmp_str)
    return ",".join(rule_str)

def recordinfo(info,file):
    with open(file,"a") as f:
        f.write(info)
        f.write("\n")

def process_data(test=None):
    with open(os.path.join(EXPPATH,"rank2domain"), 'r') as f:
        website = [x.strip() for x in f.readlines()]
        website = website[0:100]
    # print(len(website))

    for item in website:
        item_list=item.split(";")
        if  len(item_list)==3:
            rank,domain,url=tuple(item_list)
        else:
            rank,domain,old_url,url=tuple(item_list)
        # if int(rank) in nopolicy_websites:
        #     continue
        if test and rank not in test:
            continue
        rank2url[rank]=url

        vio_nums=analyze_violations(rank)
        for index in index_range:
            if vio_nums[index]:
                ranks[index].append(rank)
        with open(num_file,"a") as f:
            f.write(",".join([rank]+[str(x) for x in vio_nums[1:]]))
            f.write("\n")
        # break
    print("Numbers of websites:",len(rank2url))

def analyze_violations(rank):
    dir=os.path.join(SOURCE_DIR,rank)
    output_file = rank+ '-violations.data'
    output_file = os.path.join(vio_dir, output_file)
    violations=[None]*4
    rank2violations[rank]=[None]*4
    rank2page[rank]=[None]*4
    for index in index_range:
        violation_file=os.path.join(dir,"Violation.log"+str(index))
        page_file=os.path.join(dir,"page.html"+str(index))

        violations[index]=set()
        if not os.path.isfile(violation_file):
            continue

        with open(violation_file, 'r') as input_f:
            lines=[line.strip() for line in input_f.readlines()]
            for line in lines:
                if "gremlins" in line:
                    print("gremlins")
                    continue
                try:
                    tmp=json.loads(line)
                    tmp.pop("info")
                    tmpstr=json.dumps(tmp)
                    violations[index].add(tmpstr)
                except ValueError as err:
                    print("Rank:",rank,err)
        if len(violations[index])==0:
            continue
        # print(violations)
        output_f=open(output_file, 'a')
        output_f.write("====Test %d====\n"%index)
        output_f.write("\n".join(list(violations[index])))
        output_f.write("\n\n")
        
        page_dst_file=os.path.join(vio_dir,str(rank)+"-page"+".html"+str(index))
        shutil.copy(page_file,page_dst_file)
        with open(page_dst_file,'r') as f:
            html = f.read()
        soup = BS(html,features="html.parser")
        rank2violations[rank][index]=[json.loads(x) for x in violations[index]]

        with open(os.path.join(dir,"page_old.html"+str(index)),'r') as f:
            html = f.read()
        old_soup = BS(html,features="html.parser")

        rank2page[rank][index]=soup,old_soup

    return [len(x) if x else 0 for x in violations]

def updatepolicy(rank,index):
    # print("|||||Rank: ",rank)
    recordinfo("----"+str(rank),Exception_log)

        # recordinfo("===Test "+str(index),Exception_log)
    violations=rank2violations[rank][index]
    page,old_page=rank2page[rank][index]
    if not violations or not page:
        recordinfo("Error : Lack of file",Exception_log)
        return
    soup=page.html
    node_cannotupdate,notfound,updates=0,0,0
    navi_flag,find_one_nodes=False,False
    
    actual_url=rank2url[rank]
    actual_url=urljoin(actual_url, urlparse(actual_url).path)
    for item in violations:
        url=item["Origin Url"]
        accessed_url=urljoin(url, urlparse(url).path)
        if accessed_url.rstrip("/")!= actual_url.rstrip("/"):
            # violations.remove(item)
            if not navi_flag:
                navi_flag=True
                print(accessed_url,actual_url)
    if navi_flag:
        navi_websites.add(rank)
        recordinfo("Error Navigation",Exception_log)

    # nid2data={x["NodeID"]:x for x in violations}
    nid2violations=dict()
    for x in violations:
        nid=x["NodeID"]
        values=x["ScriptUrl"],x["Access"]
        if not nid2violations.get(nid):
            nid2violations[nid]=[values]
        else:
            nid2violations[nid].append(values)
    # print(nid2violations)
    tags=list()
    for id in list(nid2violations):
        tmp=soup.find_all(attrs={"nid":str(id)})
        if not tmp:
            # print("Not found: ", nid2data[nid])
            rst_els=old_page.html.find_all(attrs={"nid":str(id)})
            if rst_els:
                recordinfo("Not found, but found in old page: "+str(id),Exception_log)
                tags.extend(rst_els)
            else:
                notfound+=1
                recordinfo("Not found: "+str(id),Exception_log)
                nid2violations.pop(id)
                notfound_websites.add(int(rank))
        # print(tmp)
        else:
            tags.extend(tmp)

    rst_policy_file=os.path.join(POLICY_DIR,str(rank),"Result_updated.cpp")
    if os.path.exists(rst_policy_file):
        policy_file=rst_policy_file
    else:
        policy_file=os.path.join(POLICY_DIR,str(rank),"Result.cpp")
    policies=dict()
    with open(policy_file,"r") as f:
        selector=None
        rule=None
        lines=[line.strip() for line in f.readlines() if line.strip()]
        for line in lines:
            if not line.startswith("{"):
                selector=line
            else:
                tmp=line.split("policy:")[1].split(";")[0].strip()
                rule=json.loads(tmp)
                policies[selector]=rule
        # print(policies)
    
    protected_nodes=list()
    for selector in policies.keys():
        try:
            nodes= soup.select(selector)
        except Exception as e:
            print("Error of ", selector, ":\t", e)
        if nodes:
            # print(nodes)
            result_nodes=[(x,selector) for x in nodes]
            protected_nodes.extend(result_nodes)
        else:
            nodes = old_page.html.select(selector)
            if nodes:
                result_nodes=[(x,selector) for x in nodes]
                protected_nodes.extend(result_nodes)
                recordinfo("Selector not exist, but found in old_page: "+selector,Exception_log)
            else:
                recordinfo("Selector not exist: "+selector,Exception_log)
    # print(protected_nodes)
    for tag in tags:
        flag=False
        nid=int(tag["nid"])
        for item in nid2violations[nid]:
            script=get_scheme_host(item[0])
            if item[1]==1:
                access="R"
            elif item[1]==2:
                access="W"
            else:
                print("Error: ",item[1])
            for nodes,selector in protected_nodes:
                # print(nodes["nid"],tag["nid"])
                if not nodes.get("nid"):
                    continue
                if nodes["nid"]==tag["nid"]:
                    flag=True
                    if not policies[selector].get(script):
                        policies[selector][script]=access
                        # print("New",access)
                        updates+=1
                    elif access not in policies[selector][script]:
                        policies[selector][script]+=access
                        # print("Add",access)
                        updates+=1
                elif nodes.find_all(attrs={"nid":str(nid)}):
                    flag=True
                    if not policies[selector].get(script):
                        policies[selector][script]=access
                        # print(access)
                        updates+=1
                    elif access not in policies[selector][script]:
                        policies[selector][script]+=access
                        # print(access)
                        updates+=1
                    # print(selector, script, access)
            if not flag:
                node_cannotupdate+=1
                # print("Not Update: ", nid2data[nid])
                websites_needcheck.add(int(rank))
                recordinfo("Not Update: "+str(item),Exception_log)
            else:
                find_one_nodes=True

    if not find_one_nodes:
        noupdate_websites.add(rank)

    if updates!=0:
        updated.append(int(rank))
        updated_policy_file=os.path.join(POLICY_DIR,str(rank),"Result_updated_day"+str(ROUND)+"_"+str(index)+".cpp")
        with open(updated_policy_file,"w") as f:
            for selector, rules in policies.items():
                rules_str=build_rule(rules)
                policy_str='''\
                    {selector}
                    {{policy: {{{rules}}};}}
                    '''.format(selector=selector,rules=rules_str)
                # print(policy_str)
                f.write(policy_str+'\n')
        shutil.copy(updated_policy_file,rst_policy_file)

    rst_list=[rank,len(violations),updates,node_cannotupdate,notfound,navi_flag]
    rst_list=[str(x) for x in rst_list]
    print(",".join(rst_list))

def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'i:r:', ['index=','round='])
    except getopt.GetoptError:
        sys.exit(2)
    round=1
    update_index=None
    for opt, arg in opts:
        if opt in ('-r', '--round'):
            round = int(arg)
        elif opt in ('-i', '--index'):
            update_index = arg
        
    if update_index:
        init(round,False)
        print("# Round",ROUND)
        print(update_index)
        indexlist=update_index.split(",")
        process_data(indexlist)

        for rank in indexlist:
            print(rank)
            for index in range(1,4):
                updatepolicy(rank,index)
        return
    init(round,True)
    print("# Round",ROUND)
    process_data()

    for index in index_range:
        print("=====Test %d===="%index)
        recordinfo("=======Test "+str(index)+"======",Exception_log)

        for i in [updated,navi_websites,noupdate_websites,notfound_websites,websites_needcheck]:
            i.clear()

        for rank in ranks[index]:
            updatepolicy(rank,index)

        print("========= Summary ======")
        print("Violations: \n",ranks[index])
        print("Updated: \n",updated)
        print("Websites with not updated violations: ",websites_needcheck)
        print("Websites with navigation: ",navi_websites)
        print("Websites without any update: ",noupdate_websites)
        print("Websites with not found violations: ",notfound_websites)
        print("Numbers: ")
        print("violations: %d, updated: %d, noupdates: %d, lognotfound: %d, navigation: %d\n"%(len(ranks[index]),len(updated),len(noupdate_websites),len(notfound_websites),len(navi_websites)))

if __name__ == '__main__':
    main(sys.argv[1:])