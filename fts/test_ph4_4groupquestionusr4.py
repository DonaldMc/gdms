# These tests are all based on the tutorial at http://killer-web-development.com/
# if registration is successful this may work but lets
# try and get user logged in first

from functional_tests import FunctionalTest, ROOT, USERS
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class AnswerQuestion (FunctionalTest):

    def setUp(self):   
        self.url = ROOT + '/default/user/login'        
        get_browser=self.browser.get(self.url)

        mailstring = USERS['USER4'] + '@user.com'
        email = WebDriverWait(self, 10).until(lambda self: self.browser.find_element_by_name("email"))
        email.send_keys(mailstring)

        password = self.browser.find_element_by_name("password")    
        password.send_keys(USERS['PASSWORD4'])    

        submit_button = self.browser.find_element_by_css_selector("#submit_record__row input")
        submit_button.click()  
        time.sleep(1)  
        
        self.url = ROOT + '/answer/get_question/quest'        
        get_browser=self.browser.get(self.url)

    def test_answer(self):
        #self.browser.find_element_by_xpath("(//input[@name='ans'])[3]").click()
        wait = WebDriverWait(self.browser, 10)
        element = wait.until(EC.element_to_be_clickable((By.XPATH, "(//input[@name='ans'])[2]")))
        element.click()
        #toclick = WebDriverWait(self, 10).until(lambda self : self.browser.find_element_by_xpath("(//input[@name='ans'])[2]"))
        #toclick.click()
        urgency = self.browser.find_element_by_id("userquestion_urgency")
        urgency.send_keys("7")
        importance = self.browser.find_element_by_id("userquestion_importance")
        importance.send_keys("8")
        self.browser.find_element_by_id("userquestion_changecat").click()
    
        category = self.browser.find_element_by_id("userquestion_category")
        category.send_keys("Strategy")
        self.browser.find_element_by_id("userquestion_changescope").click()
        
        #activescope = self.browser.find_element_by_id("userquestion_activescope")
        #activescope.select_by_visible_text("2 Continental")

        #continent = self.browser.find_element_by_id("userquestion_continent")
        #continent.select_by_visible_text("Africa (AF)")

        #self.browser.find_element_by_id("userquestion_answerreason").clear()
        self.browser.find_element_by_id("userquestion_answerreason").send_keys("the right answer selenium testing")
        #driver.find_element_by_css_selector("input.btn").click()        

        #answer.send_keys("1")

        submit_button = self.browser.find_element_by_css_selector("#submit_record__row input")
        submit_button.click()
        time.sleep(1)

        body = WebDriverWait(self, 10).until(lambda self : self.browser.find_element_by_tag_name('body'))	
        self.assertIn('This question is in progress', body.text)
        
