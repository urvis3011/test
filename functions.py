from RPA.Browser.Selenium import Selenium
from RPA.HTTP import HTTP
import os
import re
from typing import Tuple
from selenium.common.exceptions import NoSuchElementException
from SeleniumLibrary.errors import ElementNotFound
from excel import Excel
from directories import DIRS
from logger import logger
from news_model import Model
from workitems import workitems
from time import sleep


class POSTS:

    def __init__(self) -> None:
        """Initializes the object.
            Args:
                workitem: A dictionary containing the work item data.
            Returns:
                None.
            """
        self.browser = Selenium()
        # self.phrase: str = workitem["phrase"]
        # self.section: str = workitem["section"]
        # self.months = workitem["months"]
        self.excel = Excel()
        self.http = HTTP()
        self.phrase = workitems()["phrase"]
        self.section = workitems()["section"]
        self.months = workitems()["months"]

    def open_website(self) -> None:
        """Opens the web browser and clicks on the Continue button if a pop-up window shows up.
            Parameters:
                None
            Returns:
                None.
        """
        self.browser.open_chrome_browser('https://nypost.com/')
        self.browser.maximize_browser_window()
        continue_bt = self.browser.is_element_enabled(
            '//button[text()="Dismiss"]')

        if continue_bt:
            self.browser.click_element('//button[text()="Dismiss"]')

        self.browser.wait_until_element_is_visible(
            "//button[@class='site-header__search-toggle']", timeout=20)

    def phrase_search(self) -> Tuple[str]:
        """Searches the website for the phrase and returns a msg indicating whether the news for the phrase is available or not.
            Parameters:
                phrase (str): The phrase to search for.
            Returns:
                str: A msg indicating whether the news for the phrase is available or not.
        """
        msg = ''

        self.browser.wait_until_element_is_visible(
            "//button[@class='site-header__search-toggle']", timeout=3)
        self.browser.click_element(
            "//button[@class='site-header__search-toggle']")
        self.browser.input_text(
            "//input[@id='search-input-header']", self.phrase)
        self.browser.click_element(
            "//span[contains(@class, 'search__submit-text') and text()='Search']")
        print("Search phrase done.")

        try:
            self.browser.wait_until_element_is_visible(
                "//div[@class='search-results__stories']", 20)
            available_news = True
        except AssertionError:
            msg = f"No news found for the phrase {self.phrase}"

        if self.browser.is_element_visible("//p[text()='It seems we can’t find what you’re looking for. Perhaps searching can help.']"):
            msg = f"No news found for the phrase {self.phrase}"

        return available_news, msg

    def set_dates(self) -> None:
        print("setting date.")
        date = self.months
        self.browser.scroll_element_into_view(
            "//div[@class='page page--search']")
        self.browser.wait_until_element_is_enabled(
            "//a[normalize-space()='Last Week']", timeout=5)
        if date <= 1:
            self.browser.click_element_when_clickable(
                "//a[normalize-space()='Last Week']")
        elif date == 2:
            self.browser.click_element_when_clickable(
                "//a[normalize-space()='Last 30 Days']")
        elif date == 3:
            self.browser.click_element_when_visible(
                "//a[normalize-space()='Last Year']")
        else:
            logger.info("Invalid Date range.")
        sleep(2)

    def sort_by(self):
        print("sorting")
        self.browser.scroll_element_into_view("//ul/li/a[normalize-space()='Newest']")
        self.browser.wait_until_element_is_enabled("//ul/li/a[normalize-space()='Newest']", timeout=10)
        self.browser.click_element_when_visible(
            "//ul/li/a[normalize-space()='Newest']")

    def select_sections(self):
        self.browser.scroll_element_into_view(
            "//div/nav/h3[normalize-space()='Sections']")
        self.browser.wait_until_element_is_enabled(
            "//ul/li/a[normalize-space()='All']", timeout=10)

        if self.section == '' or self.section is None:
            self.browser.click_element_when_visible(
                "//ul/li/a[normalize-space()='All']")

        elif type(self.section) == list:
            for sec in self.section:
                ele = f"//ul[@class='interior-menu__nav']/li/a[normalize-space()='{sec}']"

                if self.browser.is_element_visible(ele) or self.browser.is_element_enabled(ele):
                    self.browser.scroll_element_into_view(
                        "//div/nav/h3[normalize-space()='Sections']")
                    self.browser.wait_until_element_is_enabled(ele)
                    self.browser.click_element_when_visible(ele)
                else:
                    print(sec, ele, "not found")
                    logger.info(f"Section {sec} is not available.")

        elif type(self.section) == str:
            sections = self.section.split(",")  # Split the string by commas
            for sec in sections:
                ele = f"//ul[@class='interior-menu__nav']/li/a[normalize-space()='{sec.strip()}']"
                if self.browser.is_element_visible(ele) or self.browser.is_element_enabled(ele):
                    self.browser.scroll_element_into_view(
                        "//div/nav/h3[normalize-space()='Sections']")
                    self.browser.wait_until_element_is_enabled(ele)
                    self.browser.click_element_when_visible(ele)
                else:
                    print(sec, ele, "not found")
                    logger.info(f"Section {sec} is not available.")

        else:
            logger.info(f"Section {self.section} is not available.")
            raise AssertionError

    def get_required_data(self):

        i = 1

        ele = f"//a[normalize-space()='See More Stories']"
        print("get req data")
        sleep(3)

        if self.browser.is_element_enabled(ele):
            while True:
                try:
                    self.send_to_excel(i)
                    print(i, "page")
                    self.browser.scroll_element_into_view(ele)
                    self.browser.click_element_when_clickable(ele, timeout=10)
                    i = i+1
                except ElementNotFound:
                    logger.info("Scrapped all data scuessfully ")
                    break

        else:
            try:
                logger.info("Scrapped all data scuessfully ")

            except NoSuchElementException:
                print('error')
                logger.info(f"No News Found on {self.phrase}")

    def news_stories(self, index):
        title_list = []
        date_list = []
        description_list = []
        image_filename_list = []
        money_present_list = []
        phrase_list = []

        path = f"//div[@class='search-results__story']"
        i = len(self.browser.find_elements(path))
        print(i)
        for var in range(1, i+1):
            self.browser.scroll_element_into_view(
                f"//div[@class='search-results__story'][{var}]")
            date = self.browser.get_text(
                f"//div[@class='search-results__story'][{var}]//div/div[2]/span")
            title = self.browser.get_text(
                f"//div[@class='search-results__story'][{var}]//div/div[2]/h3/a")
            description = self.browser.get_text(
                f"//div[@class='search-results__story'][{var}]//div/div[2]/p")
            is_image = self.browser.is_element_enabled(
                f"//div[@class='search-results__story'][{var}]//div/div/a/img")
            if is_image:
                image_src = self.browser.get_element_attribute(
                    f"//div[@class='search-results__story'][{var}]//div/div/a/img", 'src')

                image_filename = f'page({index})_image-news({var}).png'
                image_path = os.path.join(DIRS.IMG_Path, image_filename)

                self.download_picture(image_src, image_path)
            else:
                image_filename = ''
            
            final_date = re.findall(r"[A-Za-z]+\s\d{1,2},\s\d{4}", date)

            money_present = self.money_status(
                title) or self.money_status(description)
            title_count = self.search_string_count(title, self.phrase)
            description_count = self.search_string_count(
                description, self.phrase)

            title_list.append(title)
            date_list.append(final_date)
            description_list.append(description)
            image_filename_list.append(image_filename)
            money_present_list.append(money_present)
            phrase_list.append(
                f'Title: {title_count}; Description: {description_count}')

        return title_list, date_list, description_list, image_filename_list, money_present_list, phrase_list

    def download_picture(self, image_src: str, image_path: str) -> None:
        """Downloads the picture from the URL and saves it to the specified path.
            Args:
                image_src (str): The URL of the image.
                image_path (str): The path to the file where the image should be saved.
            Returns:
                None.
        """
        self.http.download(url=image_src, target_file=image_path)

    def money_status(self, input_text: str) -> bool:
        """Checks if any money string is present in the given text.
            Parameters:
                input_text (str): The input string.
            Returns:
                bool: True if any money string is present in the given text, False otherwise.
        """
        pattern_of_money = r'\$\d+(?:,\d+)*(?:\.\d+)?(?:\s*(?:dollars|USD))?\b|\b\d+\s*(?:dollars|USD)\b'
        match = re.findall(pattern_of_money, input_text)
        if match:
            return True
        else:
            return False

    def search_string_count(self, input_string: str, search_string: str) -> int:
        """Returns the count of the search string in the input string.
            Parameters:
                input_string (str): The input string.
                search_string (str): The search string.
            Returns:
                int: The count of the search string in the input string.
        """
        for char in ".,;?!‘’":
            input_string = input_string.lower().replace(char, "")
        words = input_string.split()
        result = []

        for i in range(0, len(words), len(search_string.split())):
            result.append(' '.join(words[i:i+len(search_string.split())]))
        return result.count(search_string.lower())

    def send_to_excel(self, index) -> None:
        """Fetches all the news applying all the filters and exports them into an Excel sheet.
            Returns:
                None.
        """

        news_data = Model(self.news_stories(index))

        worksheet_data = {
            "Title": news_data.title_list,
            "Description":  news_data.description_list,
            "Date": news_data.date_list,
            "Image FileName": news_data.image_file_list,
            "Count of Search Phrase": news_data.count_phrase_list,
            "Money Present": news_data.money_present_list
        }
        self.excel.create_excel(worksheet_data, DIRS.File_Path, index)

p=POSTS()
p.open_website()
p.phrase_search()
p.set_dates()
p.sort_by()
p.select_sections()
p.get_required_data()