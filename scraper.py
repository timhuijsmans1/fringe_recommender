import pandas as pd
import re

from bs4 import BeautifulSoup
from helpers import random_string_generator, results_url_compiler
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class Scraper:

    def __init__(self):
        self.unique_descriptions = set()
        self.all_shows_df = pd.DataFrame()

    def source_loader(self, url, driver_path):
        s = Service(driver_path)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=s, options=chrome_options)
        self.driver.get(url)
        self.driver.implicitly_wait(4)
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        return soup

    def description_processing(self, raw_description):
        star_review_pattern = r'\*+'
        text_review_pattern = r'\"[\w\s!?]+\"'
        raw_description = raw_description.replace('‘', '\"')
        raw_description = raw_description.replace('’', '\"')
        star_reviews = re.findall(star_review_pattern, raw_description)
        if star_reviews:
            first_star_review = star_reviews[0]
            text_and_star_review_pattern = r"%s %s" % (text_review_pattern, star_review_pattern)
            text_and_star_reviews = re.findall(
                text_and_star_review_pattern, raw_description
            )
            if text_and_star_reviews:
                first_review = text_and_star_reviews[0]
            else:
                first_review = first_star_review
        else:
            text_reviews = re.findall(text_review_pattern, raw_description)
            if text_reviews:
                first_review = text_reviews[0]
            else:
                first_review = random_string_generator()
        
        description, first_review, _ = raw_description.partition(first_review)

        return description

    def description_collector(self, div):
        description_div = div.find('span', {'class': 'search-event-description'})
        description = description_div.find('p')

        if description:
            processed_description = self.description_processing(description.getText())
            # read more does not occur in all descriptions, but this assures removal
            processed_description = processed_description.replace('... Read more', ' ')
        else:
            processed_description = None

        return processed_description
    
    def show_url_collector(self, div):
        button = div.find('a', class_="btn btn-default pull-right")
        url = button["href"]
        return url
    
    def title_collector(self, div):
        title = div['data-event-name']
        return title

    def category_genre_collector(self, div):
        category_and_genre = div.find('h4').getText()
        category, genres = category_and_genre.split('(')
        genres = genres.strip(')(').split(', ')
        return category, genres

    def description_is_valid(self, description):
        if description not in self.unique_descriptions and description != None:
            self.unique_descriptions.add(description)
            return True
        else:
            return False

    def single_page_collector(self, soup):
        all_shows_on_page = []

        # find each show's card, and store as list
        divs = soup.find_all("div", class_="event clearfix")
        
        for div in divs:
            description = self.description_collector(div)
            if self.description_is_valid(description):
                url = self.show_url_collector(div)
                title = self.title_collector(div)
                category, genres = self.category_genre_collector(div)
                show_data = {
                    'title': title, 
                    'description': description, 
                    'url': url,
                    'category': category,
                    'genres': genres,
                }
                all_shows_on_page.append(
                    show_data
                )

        return all_shows_on_page

    def dataframe_appending(self, page_data):
        page_df = pd.DataFrame(page_data)
        self.all_shows_df = pd.concat([self.all_shows_df, page_df], ignore_index=True)

    def quit_driver_window(self):
        self.driver.quit()
            

def main():
    scraper = Scraper()
    for i in range(0, 3581, 10):
        print(f'{int(i / 10)} / 358')
        url = results_url_compiler(BASE_URL, i)
        soup = scraper.source_loader(url, DRIVER_PATH)
        scraper.quit_driver_window()
        page_data = scraper.single_page_collector(soup)
        scraper.dataframe_appending(page_data)
        print(scraper.all_shows_df)
        


if __name__ == '__main__':
    BASE_URL = 'https://tickets.edfringe.com/whats-on#q=*%3A*&start='
    DRIVER_PATH = '../fringe_env/bin/chromedriver'
    main()

