import os
import time
from json import loads
from pickle import dump, load
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Ticket():
    def __init__(self, urls, ticket_info, driver_path):
        self.login_url = urls['login_url']      # 登录地址
        self.target_url = urls['target_url']    # 抢票地址
        self.city = ticket_info['city']         # 城市
        self.date = ticket_info['date']         # 日期
        self.session = ticket_info['session']   # 场次
        self.price = ticket_info['price']       # 价格
        self.ticket_num = ticket_info['num']    # 数量
        self.viewer = ticket_info['viewer']     # 观影人
        self.try_num = 0
        self.status = 0
        self.driver = webdriver.Chrome(service=Service(driver_path))

    def set_cookie(self):
        try:
            cookies = load(open('cookies.pkl', 'rb'))
            for cookie in cookies:
                self.driver.add_cookie(cookie_dict = {
                    'domain':'.damai.cn',
                    'name': cookie.get('name'),
                    'value': cookie.get('value')
                })
            print(u'###载入cookie###')
        except Exception as e:
            print(e)

    def get_cookie(self):
        self.driver.get(self.login_url)
        while self.driver.title == '大麦登录':
            sleep(1)
        dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
        print(u'###Cookie保存成功###')
        
    def login(self):
        print(u'###开始登录###')
        if not os.path.exists('cookies.pkl'):
            self.get_cookie()
        else:
            self.driver.get(self.target_url)
            self.set_cookie()
        print(u'###登录成功###')
    
    def __choose_city(self):
        citys = self.driver.find_elements(By.CLASS_NAME, 'cityitem')
        citys[self.city - 1].click()
        print(u'###已选择城市: {}###'.format(citys[self.city - 1].text))
   
    def __get_select(self, text):
        selects = self.driver.find_elements(By.CLASS_NAME, 'perform__order__select')
        for item in selects:
            if item.find_element(By.CLASS_NAME, 'select_left').text == text:
                return item
        return None
    
    def __choose_date(self):
        return
    
    def __choose_session(self):
        sleep(0.1)
        session = self.__get_select('场次')
        session_list = session.find_elements(By.CLASS_NAME, 'select_right_list_item')
        #print(u'\t###可选场次数量: {}###'.format(len(session_list)))
        for i in self.session:
            s = session_list[i - 1]
            k = s.find_elements(By.CLASS_NAME, 'presell')
            if len(k) > 0:
                if k[0].text == '无票':
                    continue
                elif k[0].text == '预售':
                    s.click()
                    tag = s.find_element(By.TAG_NAME, 'span')
                    print(u'###已选择场次: {}###'.format(tag.text))
                    break
                elif k[0].text == '惠':
                    s.click()
                    tag = s.find_element(By.TAG_NAME, 'span')
                    print(u'###已选择场次: {}###'.format(tag.text))
                    break
            else:
                s.click()
                tag = s.find_element(By.TAG_NAME, 'span')
                print(u'###已选择场次: {}###'.format(tag.text))
                break
    
    def __choose_price(self):
        sleep(0.1)
        price = self.__get_select('票档')
        price_list = price.find_elements(By.CLASS_NAME, 'select_right_list_item')
        #print(u'\t###可选票档数量: {}###'.format(len(price_list)))
        for i in self.price:
            p = price_list[i - 1]
            k = p.find_elements(By.CLASS_NAME, 'notticket')
            if len(k) > 0:  # 存在notticket代表存在缺货登记，跳过
                continue
            else:
                p.click()#选定好票档点击确定
                tag = p.find_element(By.CLASS_NAME, 'skuname')
                print(u'###已选择票档: {}###'.format(tag.text))
                break
    
    def __choose_ticket_num(self):
        ticket_num = self.driver.find_elements(By.CLASS_NAME, 'perform__order__price')
        if len(ticket_num) > 0:
            for i in range(1, self.ticket_num):
                add = ticket_num[0].find_element(By.CLASS_NAME, 'cafe-c-input-number-handler-up')
                add.click()
        total_price = ticket_num[1].find_element(By.CLASS_NAME, 'totol__price')
        print(u'###合计: {}###'.format(total_price.text))
    
    def __buybtn(self, buybtn):
        if buybtn.text == '立即预订' or buybtn.text == '立即购买':
            self.status = 0
        elif buybtn.text == '选座购买':
            self.status = 1
            print(u'###请自行选择位置###')
        elif buybtn.text == '提交缺货登记':
            self.status = 2
            raise Exception(u'###票已被抢完，持续捡漏中...或请关闭程序并手动提交缺货登记###')
        elif buybtn.text == '即将开抢' or buybtn.text == '即将开售':
            self.status = 3
            raise Exception(u'---尚未开售，刷新等待---')
        else:
            self.status = -1
            raise Exception(u'***购买按钮解析错误***')
    
    def open_browser(self):
        print(u'###打开浏览器，进入大麦网###')
        self.login()            # 登录

    def choose_ticket(self):
        self.driver.get(self.target_url)
        title = self.driver.find_element(By.CLASS_NAME, 'title')
        t = title.find_elements(By.TAG_NAME, 'span')
        print(u'###开始抢票: {}###'.format(t[-1].text))
        while self.driver.title.find('确认订单') == -1:
            if self.driver.current_url.find('buy.damai.cn') > 0:
                break

            self.try_num += 1
            # 确认页面刷新成功
            try:
                buybtn = WebDriverWait(self.driver, 1, 0.1).until(EC.presence_of_element_located((By.CLASS_NAME, 'buybtn')))
            except:
                raise Exception(u'***Error: 页面刷新出错***')

            # check
            self.__buybtn(buybtn)

            # 城市选择
            self.__choose_city()
            # 日期选择
            self.__choose_date()
            # 场次选择
            self.__choose_session()
            # 票档选择
            self.__choose_price()
            # 数量选择
            self.__choose_ticket_num()
            # 购买
            self.__buybtn(buybtn)
            if self.status in [0, 1]:
                buybtn.click()
    
    def check_order(self):
        if self.status not in [0, 1]:
            return
        WebDriverWait(self.driver, 1, 0.1).until(EC.presence_of_element_located((By.CLASS_NAME, 'next-btn')))

        print(u'###开始确认订单###')
        # 选择观影人
        buyer = self.driver.find_element(By.CLASS_NAME, 'buyer-list')
        viewer = buyer.find_elements(By.TAG_NAME, 'input')
        for i in self.viewer:
            if i <= len(viewer):
                viewer[i - 1].click()
                sleep(0.1)

        # 同意以上协议并提交订单
        submit = self.driver.find_element(By.CLASS_NAME, 'submit-wrapper')
        submit.find_element(By.CLASS_NAME, 'next-btn').click()
        print(u'###成功提交订单,请手动支付###')

        # 等待跳转到支付页面
        #WebDriverWait(self.driver, 3600, 0.1).until(EC.title_contains('支付宝'))

if __name__ == '__main__':
    try:
        with open('./config.json', 'r', encoding='utf-8') as f:
            config = loads(f.read())
        tk = Ticket(config['urls'], config['ticket_info'], config['driver_path'])
        print(u'###打开浏览器，进入大麦网###')
        tk.login()
        tk.choose_ticket()
        tk.check_order()
    except Exception as e:
        print(e)
        exit(1)
    
    while True:
        sleep(1)