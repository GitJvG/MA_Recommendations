import pandas as pd
from MA_Scraper.Scripts.utils import Parallel_processing, fetch
from MA_Scraper.Env import Env
from bs4 import BeautifulSoup as bs4
env = Env.get_instance()

def reviews_df(soup, album_id):
    reviews = []

    for review_box in soup.find_all("div", class_="reviewBox"):
        review_id = review_box["id"].replace("reviewBox_", "")
        title = review_box.find("h3", class_="reviewTitle").text.strip()
        
        username_tag = review_box.find("a", class_="profileMenu")
        username = username_tag.text.strip() if username_tag else None
        
        review_text_tag = review_box.find("p", id=f"reviewText_{review_id}")
        review_text = review_text_tag.get_text(" ", strip=True) if review_text_tag else None
        
        reviews.append({
            "album_id": album_id,
            "review_id": review_id,
            "title": title,
            "username": username,
            "review_text": review_text
        })

    df_reviews = pd.DataFrame(reviews)
    return df_reviews

def get_reviews(album_id):
    """Main function to fetch band data, using helper functions."""
    album_url = f'{env.url_reviews}{album_id}'
    try:
        html_content = fetch(album_url, headers=env.head)

        if html_content is None:
            return None
        
        soup = bs4(html_content, 'html.parser')
        df = reviews_df(soup, album_id)

        return df

    except Exception as e:
        print(f"Error fetching band data for {album_id}: {e}")
        return None
    
def main():
    df = pd.read_csv(env.disc)
    df = df[~df['review_count'].isnull()]
    album_ids = set(df['album_id'])
    existing_ids = set(pd.read_csv(env.reviews)['album_id'].drop_duplicates())

    missing_ids = list(album_ids - existing_ids)

    Parallel_processing(missing_ids, env.batch_size, env.reviews, get_reviews)
    
if __name__ == '__main__':
    main()
