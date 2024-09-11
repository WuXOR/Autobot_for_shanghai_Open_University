# encoding= utf-8
# version= v0.1.5
import os
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import tool

self_path = os.path.dirname(os.path.abspath(__file__))
CHROME_DRIVER_PATH = self_path + '\\data\\chromedriver-win32\\chromedriver.exe'
CHROME_PATH = self_path + '\\data\\chrome-win64\\chrome.exe'


class Web:
    def __init__(self, json_data=tool.GetData(), logger=tool.Logger()) -> None:
        self.all_classes = None
        self.json_data = json_data
        self.logger = logger
        current_path = os.environ.get('PATH')
        os.environ['PATH'] = f"{CHROME_PATH};{CHROME_DRIVER_PATH};{current_path}"
        self.bowser = webdriver.Chrome()

    def get_all_windows(self):
        """
        获取浏览器的所有标签页
        :return:
        """
        return self.bowser.window_handles

    def look_at_windows_by_index(self, index):
        self.bowser.switch_to.window(self.bowser.window_handles[index])

    def login(self):
        """
        在登录界面登录data的用户
        :return:
        """
        user_data = self.json_data.data["user_data"]
        web_data = self.json_data.data["web_data"]
        self.bowser.get('https://learning.shou.org.cn/scenter?xh=310_20238310041082')
        self.wait_for_web_load()
        self.bowser.find_element(By.ID, web_data["user_input"]).send_keys(user_data["id"])
        self.bowser.find_element(By.ID, web_data["pwd_input"]).send_keys(user_data["password"])
        self.bowser.find_element(By.ID, web_data["login_button"]).click()
        self.wait_for_web_load()

    def get_all_classes(self):
        self.all_classes = [i for i in self.bowser.find_elements(By.TAG_NAME, 'a') if "学习进度" in i.text]

    def wait_for_web_load(self):
        WebDriverWait(self.bowser, 30).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )

    def open_all_list(self):
        for i in self.bowser.find_elements(By.TAG_NAME, 'a'):
            if i.get_attribute("class") == "topic_ext":
                i.click()

    def get_link_list(self):
        imgs = []
        for i in self.bowser.find_elements(By.TAG_NAME, 'img'):
            if ((i.get_attribute("title") == "未完成" or i.get_attribute("title") == "未看")
                    and i.get_attribute("class") == "warningnew1"):
                imgs.append(i)
        element_links = []
        for i in imgs:
            elements = i.find_element(By.XPATH, "..").find_element(By.XPATH, "..").find_elements(By.XPATH, ".//*")
            for j in elements:
                if j.tag_name == "a" and j.get_attribute("class") != "topic_ext":
                    element_links.append(j)
        return element_links

    def play_video(self, video_element, link_data) -> int:
        try:
            self.logger.log("INFO", "视频开始播放")
            self.logger.log("Warning", link_data[0])
            self.logger.log("Warning", link_data[1])
            self.bowser.execute_script("""
                var video = arguments[0];
                video.addEventListener('ended', function() {
                    window.videoEnded = true;
                });
            """, video_element)
            video_element.click()
            self.bowser.execute_script("arguments[0].playbackRate = 2;", video_element)
            WebDriverWait(self.bowser, timeout=float('inf')).until(
                lambda driver: driver.execute_script("return window.videoEnded === true")
            )
            self.logger.log("INFO", "视频播放完毕")
            return 0
        except Exception as e:
            self.logger.log("Warning", "视频播放出现错误")
            self.logger.log("Warning", str(e))
            print("视频过程中出现错误")
            print(link_data[0])
            print(link_data[1])
            print(e)
            return 1


JsonData: tool.GetData
Logger: tool.Logger
web: Web


def main(web, json_data, logger):
    if not web.json_data:
        return 
    web.login()
    time.sleep(json_data.data["time2wait"])
    web.wait_for_web_load()
    web.get_all_classes()
    web.all_classes = [i for i in web.all_classes if "100" not in i.text]
    for _ in range(json_data.data["try_times"]):
        logger.log("INFO", f"发现共{len(web.all_classes)}节课")
        for classes in web.all_classes:
            web.look_at_windows_by_index(0)
            classes.click()
            web.look_at_windows_by_index(1)
            web.wait_for_web_load()
            web.open_all_list()
            links = web.get_link_list()
            logger.log("INFO", f"课程下发现共{len(links)}个链接")
            for link in links:
                for _ in range(json_data.data["try_times"]):
                    web.look_at_windows_by_index(1)
                    link_data = [link.text, link.get_attribute("href")]
                    try:
                        link.click()
                    except Exception as e:
                        web.logger.log("Warning", "点击视频链接时 出现错误")
                        web.logger.log("Warning", link_data[0])
                        web.logger.log("Warning", link_data[1])
                        web.logger.log("Warning", str(e))
                        print(e)
                        print(link_data[0])
                        print(link_data[1])
                        continue
                    web.look_at_windows_by_index(2)
                    web.wait_for_web_load()
                    time.sleep(json_data.data["time2wait"])
                    videos = web.bowser.find_elements(By.TAG_NAME, 'video')
                    if len(videos) > 1:
                        print("出现复数个视频")
                        print(link_data[0])
                        print(link_data[1])
                        Logger.log("Warning", "出现复数个视频")
                        Logger.log("Warning", link_data[0])
                        Logger.log("Warning", link_data[1])
                    r = 0
                    if len(videos) == 1:
                        r = web.play_video(videos[0], link_data)
                    web.bowser.close()
                    if r == 0:
                        break
            time.sleep(json_data.data["time2wait"])
            web.look_at_windows_by_index(1)
            web.bowser.close()
        web.look_at_windows_by_index(0)
        web.get_all_classes()
        auto_end = True
        for classes in web.all_classes:
            if "100" not in classes.text:
                auto_end = False
                break
        if auto_end:
            json_data.end = True
            break


if __name__ == '__main__':
    JsonData = tool.GetData()
    JsonData.end = False
    Logger = tool.Logger()
    if JsonData.data["user_data"]["id"] == "" or \
            JsonData.data["user_data"]["password"] == "":
        print("在./data/data.json文件中 在user_data下键入你的用户名和密码")
    else:
        for _ in range(2):
            web = Web(JsonData, Logger)
            if JsonData.end:
                break
            try:
                main(web, JsonData, Logger)
            except Exception as e:
                Logger.log("Exception", "main函数出现错误")
                Logger.log("Exception", str(e))
                print(e)
            finally:
                web.bowser.quit()
