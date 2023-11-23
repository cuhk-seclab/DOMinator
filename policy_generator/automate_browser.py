import os,sys,getopt,time,shutil,json,signal,pickle,subprocess,random,psutil

from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities    
from selenium.webdriver.support import expected_conditions as EC 

version = '88.0.4324.27'

PROXY1="127.0.0.1:8080" #ORIGIN
PROXY2="127.0.0.1:9090" #CPP

maxtime=3

EXP_ROUND=4
ROUND=0

ROOT = os.path.dirname(os.path.realpath(__file__))
EXPPATH = os.path.join(ROOT,"Exp"+str(EXP_ROUND))
TMPDIR=""

ORGIN_CHROMIUM_BINARY="Vanilla/chrome"
CPP_CHROMIUM_BINARY="Cpp/chrome"

Current_PID=None

success_a=set()
success_b=set()

def init(phase, round=None):
    print("----------------Start %s Round %s--------------"%(phase,str(round)))
    global DATA_DIR,SOURCE_DIR,err_file,result_vio_file,ROUND
    if round:
        ROUND=round
        DATA_DIR=os.path.join(EXPPATH,phase,"round"+str(round))
    else:
        DATA_DIR=os.path.join(EXPPATH,phase)
    SOURCE_DIR=os.path.join(DATA_DIR,"source_logs")
    err_file=os.path.join(DATA_DIR,"err")
    result_vio_file=os.path.join(DATA_DIR,"result_vio")

class BrowserTimeoutError(Exception):
    pass

#handle output file
def handle_output(src,dst):
    try:
        if os.path.isfile(src):
            try:
                shutil.move(src, dst)
                # print("handle",src)
                return True
            except IOError as e:
                print("Result Error ",e)
            except OSError as e:
                pass
    except Exception as e:
        pass

def kill_child_processes(parent_pid=None, parent=None, timeout=3, sig=signal.SIGTERM, include_parent = True):
    global log_f
    #current_time = getlocaltime()
    if not parent and not parent_pid:
        return (None, None)
    try:
        if not parent and parent_pid:
            parent = psutil.Process(parent_pid)
    except (psutil.NoSuchProcess, psutil.ZombieProcess, psutil.AccessDenied):
        return (None, None)
    if parent.pid == os.getpid():
        include_parent = False
    children = parent.children(recursive=True)
    if include_parent:
        children.append(parent)
    for process in children:
        try:
            process.send_signal(sig)
        except (psutil.NoSuchProcess, psutil.ZombieProcess, psutil.AccessDenied):
            pass
    gone, alive = psutil.wait_procs(children, timeout=timeout, callback=None)
    if alive:
        for process in alive:
            try:
                process.kill() # SEND SIGKILL
            except (psutil.NoSuchProcess, psutil.ZombieProcess, psutil.AccessDenied):
                pass
        gone, alive = psutil.wait_procs(alive, timeout=timeout, callback=None)
    return (gone, alive)

def kill_processes_by_name(name):
    for process in psutil.process_iter():
        try:
            cmdline = ' '.join(process.cmdline())
            if name not in cmdline:
                continue
            kill_child_processes(parent = process)
        except (psutil.NoSuchProcess, psutil.ZombieProcess, psutil.AccessDenied):
            pass

def clean_tmp_files():
    for file_name in ["Access.log","Violation.log","Num","tmp.html"]:
        f=os.path.join(ROOT,file_name)
        if os.path.isfile(f):
            os.remove(f)

def initial(dirs):
    for item in dirs:
        if not os.path.exists(item):
            os.mkdir(item)

def recordinfo(info,file):
    with open(file,"a") as f:
        f.write(info)
        f.write("\n")

def monkey_testing(driver):
    driver.execute_script("document.navigationFlag=false;")
    try:
        script="""
        (function() {
            function callback() {
                gremlins.createHorde({
                    species: [gremlins.species.clicker(),gremlins.species.toucher(),gremlins.species.formFiller(),gremlins.species.scroller(),gremlins.species.typer()],
                    mogwais: [gremlins.mogwais.alert(),gremlins.mogwais.fps(),gremlins.mogwais.gizmo()],
                    strategies: [gremlins.strategies.allTogether({nb:3000})]
                })
                .unleash();
            }
            var s = document.createElement("script");
            s.src = "https://unpkg.com/gremlins.js";
            console.log("Script");
            if (s.addEventListener) {
                s.addEventListener("load", callback, false);
                console.log("load success")
            } 
            else if (s.readyState) {
                s.onreadystatechange = callback;
                console.log("Not Load")
                console.log(s.readyState)
            } 
            document.body.appendChild(s);
            })()
        """
        driver.execute_script(script)
    except Exception as e1:
        try:
            script="""
            gremlins.createHorde({
                species: [gremlins.species.clicker(),gremlins.species.toucher(),gremlins.species.formFiller(),gremlins.species.scroller(),gremlins.species.typer()],
                mogwais: [gremlins.mogwais.alert(),gremlins.mogwais.fps(),gremlins.mogwais.gizmo()],
                strategies: [gremlins.strategies.allTogether({nb:3000})]
            }).unleash();
            """
            driver.execute_script(script)
        except Exception as e2:
            print(e1,e2)
    time.sleep(30)

def create_browser(user_dir,proxy_flag=0,browser=True,generation_mode=False,incognito=False):
    clean_tmp_files()
    options = Options()
    options.add_argument('--disable-hang-monitor')
    options.add_argument('--no-sandbox')   
    options.add_argument('--disable-component-extensions-with-background-pages')
    options.add_argument("--disable-notifications")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--enable-logging")
    if proxy_flag==1:
        proxy=PROXY1
        options.add_argument('--proxy-server=%s' % proxy)
    elif proxy_flag==2:
        proxy=PROXY2
        options.add_argument('--proxy-server=%s' % proxy)
    
    if generation_mode:
        os.environ["G_MODE"] = "1"
    else:
        try:
            del os.environ["G_MDOE"]
        except KeyError:
            pass

    if browser:
        browser_path=CPP_CHROMIUM_BINARY
    else:
        browser_path=ORGIN_CHROMIUM_BINARY
    # if incognito:
    #     options.add_argument("--incognito")

    binary_path=os.path.join(ROOT,browser_path)

    if binary_path:
        options.binary_location= binary_path
    # if headless:
    #     options.add_argument('--headless')
    if user_dir:
        options.add_argument('--user-data-dir='+user_dir)

    browser = webdriver.Chrome(service=Service(os.path.join(ROOT,"chromedriver")),options=options) 
    browser.set_page_load_timeout(300)
    return browser

def prepare_websites(websites, output=True):
    DATA_DIR=os.path.join(EXPPATH,"Security")
    page_filename="page.html"
    tmp_page_file=os.path.join(TMPDIR,page_filename)
    sensTag_filename = "SensTag.log"
    tmp_tag_file=os.path.join(TMPDIR,sensTag_filename)

    user_dir="user-dir-auth"
    for rank,domain,url in websites:

        for f in [tmp_page_file,tmp_tag_file]:
            if os.path.isfile(f):
                os.remove(f)

        print('Running', domain, rank, flush=True)
        if "*" in domain:
            continue
        driver=create_browser(user_dir,proxy_flag=2,generation_mode=1)
        driver.get("https://"+domain)
        while True:
            try:
                _ = driver.window_handles
            except Exception as e:
                print("Browser closed")
                break
            time.sleep(1)

        output_dir = os.path.join(DATA_DIR,str(rank))
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        page_dst_file=os.path.join(output_dir,"page.html")
        handle_output(tmp_page_file,page_dst_file)

        tag_dst_file=os.path.join(output_dir,"SensTag.log")
        handle_output(tmp_tag_file,tag_dst_file)

        vio_log_filename = 'Violation.log'
        vio_log_file = os.path.join(ROOT, vio_log_filename)
        vio_dst_file = os.path.join(output_dir,vio_log_filename+"1")
        if handle_output(vio_log_file,vio_dst_file):
            print("Violation")

def get_source_access(websites):
    DATA_DIR=os.path.join(EXPPATH,"generation")
    ROUND_DIR=os.path.join(DATA_DIR, "round"+str(ROUND))
    SOURCE_DIR=os.path.join(ROUND_DIR, "source_logs")

    page_file_name="page.html"
    user_dir="user-dir-auth"
    # success,result_file,err_file=success_a,resultA_file,errA_file
    result_file=os.path.join(DATA_DIR, "access_result")
    #Initial
    dirs=[EXPPATH,DATA_DIR,ROUND_DIR,SOURCE_DIR]
    initial(dirs)

    print("--------------Start %s--------------" % "Round 0")
    violations=list()
    for rank,domain,url in websites:
        print('Running', url, rank, flush=True)

        output_dir = os.path.join(SOURCE_DIR,str(rank))
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        driver=create_browser(user_dir,proxy_flag=2,generation_mode=True)
        # driver.get(url)
        # time.sleep(5)
        accessed=False
        for i in range(maxtime):
            try:
                driver.get(url)
                accessed=True
            except TimeoutException as e:
                print('|||Timeout ',str(e).replace("\n"," "), flush=True)
                try:
                    driver.quit()
                except Exception as e:
                    print('|||Error ',str(e).replace("\n"," "),  flush=True)
                driver=create_browser(user_dir,proxy_flag=2,generation_mode=True)
                time.sleep(5)
                continue
            except Exception as e:
                if "crash" in str(e):
                    recordinfo(rank+","+url,err_file)
                    print("|||Fatal Error: When get Url", str(e).replace("\n"," "), flush=True)
                    break
                print("|||Error: ", str(e).replace("\n"," "), flush=True)
                try:
                    driver.quit()
                except Exception as e:
                    print('|||Error ',str(e).replace("\n"," "),  flush=True)
                driver=create_browser(user_dir,proxy_flag=2,generation_mode=True)
                time.sleep(5)
                continue
            break
        if not accessed:
            print("|||Error: can not get url")
            try:
                driver.quit()
            except Exception as e:
                print('|||Error ',str(e).replace("\n"," "),  flush=True)
            continue
        # print("Get Finish")
        time.sleep(5)
        WebDriverWait(driver, 60).until(lambda d: not d.current_url.startswith("chrome"))

        try:
            WebDriverWait(driver, 60).until(lambda d: d.execute_script('return document.readyState;') == 'complete')
        except TimeoutException as e:
            driver.set_page_load_timeout(20)
            try:
                webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except TimeoutException as e:
                driver.execute_script("window.stop();") # we have to use javsscript to stop page loading
        except UnexpectedAlertPresentException as e:
            alert1 = driver.switch_to_alert()
            alert1.dismiss()
        except Exception as e:
            driver.quit()
            recordinfo(rank+","+url,err_file)
            print("|||Fatal Error: when check load status",str(e).replace("\n"," "))
            continue
        time.sleep(5)

        tmp_page_file=os.path.join(ROOT,"tmp.html")

        try:
            page=driver.page_source
            if "ERR_TIMED_OUT" in page:
                print("Error!!!! ERR_TIMED_OUT")
            title=driver.title
            current_url=driver.current_url
            if current_url!= url:
                print("Info: Url Diff",current_url)
            with open(tmp_page_file, "w") as f:
                f.write(page)
            rst_str=";".join([rank,url,current_url,title])
            # success.add(rank)
            recordinfo(rst_str,result_file)
        except Exception as e:
            recordinfo(rank+","+url,err_file)
            print("|||Error when get source:",str(e).replace("\n"," "))
            try:
                driver.quit()
            except Exception as e:
                print('|||Error ',e,  flush=True)
            time.sleep(5)
            continue
        driver.quit()
            
        page_dst_file=os.path.join(output_dir,page_file_name+str(0))
        handle_output(tmp_page_file,page_dst_file)

        access_src_file=os.path.join(ROOT,"Violation.log")
        access_dst_file=os.path.join(output_dir,"Violation.log0")
        if handle_output(access_src_file,access_dst_file):
            violations.append(rank)
    print(violations)

def get_violations(websites,user_dir=None,proxy=2,browser=True,round_num=5):
    violations=set()
    ROUND_DIR=DATA_DIR
    SOURCE_DIR=os.path.join(ROUND_DIR, "source_logs")
    dirs=[DATA_DIR,ROUND_DIR,SOURCE_DIR]
    initial(dirs)
    user_dir="user-dir-auth"
    # prepare_profile(user_dir)
    for rank,domain,url in websites:

        kill_child_processes(Current_PID)
        kill_processes_by_name("disable-hang-monitor")

        print('Running', url, rank, flush=True)
        for index in range(1,round_num+1):
            print("Test", index)
            driver=create_browser(user_dir,proxy_flag=2,generation_mode=True)

            output_dir = os.path.join(SOURCE_DIR,str(rank))
            if not os.path.exists(output_dir):
                os.mkdir(output_dir)

            accessed=False
            for _ in range(maxtime):
                try:
                    driver.get(url)
                    accessed=True
                except Exception as e:
                    if "crash" in str(e):
                        recordinfo(rank+","+url,err_file)
                        print("|||Fatal Error: When get Url", str(e).replace("\n"," "), flush=True)
                        break
                    print("|||Error: ", str(e).replace("\n"," "), flush=True)
                    try:
                        driver.quit()
                    except Exception as e:
                        print('|||Error ',str(e).replace("\n"," "),  flush=True)
                    driver=create_browser(user_dir,proxy_flag=2,generation_mode=True)
                    time.sleep(5)
                    continue
                break
            if not accessed:
                print("|||Error: can not get url")
                try:
                    driver.quit()
                except Exception as e:
                    print('|||Error ',str(e).replace("\n"," "),  flush=True)
                continue
            # driver.get(url)

            try:
                WebDriverWait(driver, 60).until(lambda d: d.execute_script('return document.readyState;') == 'complete')
            except TimeoutException as e:
                driver.set_page_load_timeout(20)
                try:
                    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                except TimeoutException as e:
                    driver.execute_script("window.stop();") # we have to use javsscript to stop page loading
            except UnexpectedAlertPresentException as e:
                alert1 = driver.switch_to_alert()
                alert1.dismiss()
            
            time.sleep(5)

            tmp_page_file1=os.path.join(ROOT,"tmp1.html")
            try:
                page=driver.page_source
                # driver.quit()
                with open(tmp_page_file1, "w") as f:
                    f.write(page)
            except Exception as e:
                recordinfo(rank+","+url,err_file)
                print("|||Error when get source:",str(e).replace("\n"," "))
                try:
                    driver.quit()
                except Exception as e:
                    print('|||Error ',e,  flush=True)
                time.sleep(5)
                continue

            # time.sleep(90)
            try:
                print("monkey Testing")
                monkey_testing(driver)
            except Exception as e:
                print("Fatal Error :",e)
                driver.quit()
                continue

            print("Finish")

            tmp_page_file2=os.path.join(ROOT,"tmp2.html")
            try:
                page=driver.page_source
                driver.quit()
                with open(tmp_page_file2, "w") as f:
                    f.write(page)
            except Exception as e:
                recordinfo(rank+","+url,err_file)
                print("|||Error when get source:",str(e).replace("\n"," "))
                try:
                    driver.quit()
                except Exception as e:
                    print('|||Error ',e,  flush=True)
                time.sleep(5)
                continue

            # save output file
            debug_log_filename = 'chrome_debug.log'
            debug_log_file = os.path.join(ROOT, user_dir, debug_log_filename)
            debug_log_dst_file=os.path.join(output_dir,"exception.log"+str(index))
            handle_output(debug_log_file,debug_log_dst_file)

            vio_log_filename = 'Violation.log'
            vio_log_file = os.path.join(ROOT, vio_log_filename)
            vio_dst_file = os.path.join(output_dir,vio_log_filename+str(index))
            if handle_output(vio_log_file,vio_dst_file):
                violations.add(rank)
            page_file_name="page_old.html"
            page_dst_file=os.path.join(output_dir,page_file_name+str(index))
            handle_output(tmp_page_file1,page_dst_file)

            page_file_name="page.html"
            page_dst_file=os.path.join(output_dir,page_file_name+str(index))
            handle_output(tmp_page_file2,page_dst_file)

    print("----------------Summary Round %s --------------"%str(ROUND))
    print("Violation rank:",violations)

def performance_test(websites, user_dir=None,proxy=False,browser=True,index=1):
    DATA_DIR=os.path.join(EXPPATH,"performance")
    violation_list=list()
    # print("----------------Start Round %s--------------"%str("performance"))
    for index in range(20):
        print("==== Index %d ===="%(index))

        for item in websites:
            rank,domain,url=item
            kill_child_processes(Current_PID)
            kill_processes_by_name("disable-hang-monitor")

            print('Running', url, rank, flush=True)
            data_dirs=[os.path.join(DATA_DIR,"round_performance_origin_tmp"),os.path.join(DATA_DIR,"round_performance_origin"),os.path.join(DATA_DIR,"round_performance_sys_tmp"),os.path.join(DATA_DIR,"round_performance_sys"),os.path.join(DATA_DIR,"round_performance_cpp_tmp"),os.path.join(DATA_DIR,"round_performance_cpp")]

            for dir in data_dirs:
                source_dir=os.path.join(dir,"source_logs")
                initial([dir,source_dir])
 
            for exp in [0,1,3,5]:
                user_dir="user-dir-auth"
                if exp ==0:
                    print("origin_tmp",end=' ')
                    driver=create_browser(user_dir,1,False)
                    data_dir=data_dirs[exp]
                elif exp ==1:
                    print("origin",end=' ')
                    driver=create_browser(user_dir,1,False)
                    data_dir=data_dirs[exp]
                elif exp==2:
                    print("sys_tmp",end=' ')
                    driver=create_browser(user_dir,1,True)
                    data_dir=data_dirs[exp]
                elif exp==3:
                    print("sys",end=' ')
                    driver=create_browser(user_dir,1,True)
                    data_dir=data_dirs[exp]
                elif exp==4:
                    print("cpp_tmp",end=' ')
                    driver=create_browser(user_dir,2,True)
                    data_dir=data_dirs[exp]
                else:
                    print("cpp",end=' ')
                    driver=create_browser(user_dir,2,True)
                    data_dir=data_dirs[exp]

                output_dir = os.path.join(data_dir,"source_logs",str(rank))
                err_file=os.path.join(data_dir,"err")
                if not os.path.exists(output_dir):
                    os.mkdir(output_dir)
                time.sleep(5)

                load_end = None
                accessed=False
                load_start = time.time()
                try:
                    driver.get(url)
                    accessed=True
                except Exception as e:
                    if "crash" in str(e):
                        recordinfo(rank+","+url,err_file)
                        print("|||Fatal Error: When get Url", str(e).replace("\n"," "), flush=True)
                        break
                    print("|||Error: ", str(e).replace("\n"," "), flush=True)
                    driver.quit()
                    break
                if not accessed:
                    print("|||Error: can not get url")
                    try:
                        driver.quit()
                    except Exception as e:
                        print('|||Error ',str(e).replace("\n"," "),  flush=True)
                    continue

                # print("Get Finish").
                try:
                    WebDriverWait(driver, 60).until(lambda d: d.execute_script('return document.readyState;') == 'complete')
                except TimeoutException as e:
                    driver.set_page_load_timeout(20)
                    try:
                        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    except TimeoutException as e:
                        driver.execute_script("window.stop();") # we have to use javsscript to stop page loading
                except UnexpectedAlertPresentException as e:
                    alert1 = driver.switch_to_alert()
                    alert1.dismiss()
                
                load_end = time.time()                
                time.sleep(5)
                navigationStart = driver.execute_script("return window.performance.timing.navigationStart")
                responseStart = driver.execute_script("return window.performance.timing.responseStart")
                loadEventEnd = driver.execute_script("return window.performance.timing.loadEventEnd")
                domComplete = driver.execute_script("return window.performance.timing.domComplete")

                page_load_time = {'navi-load': loadEventEnd-navigationStart, 'navi-dom': domComplete-navigationStart, 'response-load': loadEventEnd-responseStart, 'response-dom': domComplete-responseStart, 'pure': load_end-load_start }
                time_file_name=os.path.join(output_dir,"time.log"+str(index))
                with open(time_file_name,"w") as time_file:
                    json.dump(page_load_time,time_file)
        
                mem_script_path = os.path.join(ROOT,'memory.py') #os.path.join(script_dir, logs_dir)
                memory_consumption = -1
                try:
                    memory_consumption = subprocess.check_output(['python', mem_script_path]).decode('ASCII').strip()
                except Exception as e:
                    pass
                # mem_log_file = str(rank) + '.mem'
                mem_log_file = 'mem.log'+str(index)
                mem_log_file = os.path.join(output_dir, mem_log_file)
                with open(mem_log_file, 'w') as output_f:
                    output_f.write(str(memory_consumption))
                print(domComplete-responseStart, load_end-load_start,str(memory_consumption),flush=True)

                try:
                    if("502" in driver.title):
                        recordinfo(rank+","+url,err_file)
                        print("|||Fatal Error:" ,driver.title, flush=True)
                        # Fatal_Err.append(item)
                        driver.quit()
                        continue
                except Exception as e:
                    print("|||Error ", e)

                # time.sleep(5)
                driver.quit()
                vio_log_filename = 'Violation.log'
                vio_log_file = os.path.join(ROOT, vio_log_filename)
                vio_dst_file = os.path.join(output_dir,vio_log_filename)
                if handle_output(vio_log_file,vio_dst_file):
                    violation_list.append(rank)
                num_log_filename = 'Num'
                num_log_file = os.path.join(ROOT, num_log_filename)
                num_log_dst_file = os.path.join(output_dir,"AccessNum.log"+str(index))
                handle_output(num_log_file,num_log_dst_file)
                # time.sleep(5)
    print("----------------Summary Round %s --------------"%str(ROUND))
    print("Violation rank:",violation_list)

def main(argv):
    try:
        opts, args = getopt.getopt(argv, 'hm:pcu:t:s:e:r:', ['help', 'mode','proxy', 'cpp' ,'user_dir=', 'test_url=', 'start=', 'end=','round='])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    user_dir = "user-dir"
    test_url = None
    proxy = False
    cpp = False
    # input_file = 'top-1m.csv'
    start = 1
    end = 100
    round=1

    for opt, arg in opts:
        if opt in ('-u', '--user_dir'):
            user_dir = arg
        elif opt in ('-m','--mode'):
            mode = arg
        elif opt in ('-p', '--proxy'):
            proxy = True
        elif opt in ('-c', '--cpp'):
            cpp = True
        elif opt in ('-t', '--test_url'):
            test_url = arg
        elif opt in ('-s', '--start'):
            start = int(arg)
        elif opt in ('-e', '--end'):
            end = int(arg)
        elif opt in ('-r', '--round'):
            round= int(arg)
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)

    global ROUND,Current_PID
    website_list=list()
    Current_PID = os.getpid()

    website_file=os.path.join(EXPPATH,"rank2domain")
    with open(website_file, 'r') as f:
        website = [x.strip() for x in f.readlines()]
        website = website[(start-1):end]
        for item in website:
            try:
                rank,domain,url=item.split(" ")[0:3]
            except:
                print(item)
                continue
            else:
                website_list.append((rank,domain,url))

    if mode == "init":
        get_source_access(website_list)
    if mode == "prepare":
        prepare_websites(website_list,False)
    elif mode == "update":
        init("generation",round)
        get_violations(website_list)
    elif mode == "usability":
        init(mode,round)
        get_violations(website_list)
    elif mode == "performance":
        performance_test(website_list,user_dir,True,True,index=0)
    elif mode == "clean":
        return

def usage():
    tab = '\t'
    print('Usage:')
    print((tab + 'python %s [OPTIONS]' % (__file__)))
    print((tab + '-d | --log_dir='))
    print((tab*2 + 'Log directory'))
    print((tab + '-u | --user_dir='))
    print((tab*2 + 'User directory of Chrome'))
    print((tab + '-s | --start'))
    print((tab*2 + 'Start index, default 0'))
    print((tab + '-e | --end'))
    print((tab*2 + 'End index, default number of URLs'))

if __name__ == '__main__':
    main(sys.argv[1:])