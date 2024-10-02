from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import random
import warnings
from app.models import UserBandPreference, DIM_Band, DIM_Lyrics
from Scripts.utils import load_config
from libreco.data import DatasetFeat, random_split
from Analysis.CleanGenre import simple_clean2
warnings.filterwarnings("ignore")
from libreco.algorithms import WideDeep
from libreco.data import DataInfo
from keras.backend import clear_session

# Create a database engine
DATABASE_URI = load_config('SQL_Url')
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()
model_path ="Model"
model_name="wide_deep"

def load_data():
    # Load data from your tables
    user_band_preference_data = session.query(UserBandPreference).all()
    dim_band_data = session.query(DIM_Band).all()
    lyrical_data = session.query(DIM_Lyrics).all()
    # Create user DataFrame
    users = pd.DataFrame(
        [(pref.user_id, pref.band_id, pref.liked) for pref in user_band_preference_data],
        columns=['user', 'item', 'label']
    )

    # Create items DataFrame
    items = pd.DataFrame(
        [(band.Band_ID, band.Band_Name, band.Country, band.Genre, band.Status) for band in dim_band_data],
        columns=['item', 'band_name', 'country', 'genre', 'status']
    )

    items['cleaned_genre'] = items['genre'].apply(simple_clean2)
    # Split the cleaned genres by commas into separate columns
    genres_split = items['cleaned_genre'].str.split(r',\s*', expand=True).fillna('missing')
    genres_split = genres_split.iloc[:, :4]
    # Rename columns for the split genres
    genres_split.columns = [f'genre{i+1}' for i in range(genres_split.shape[1])]

    # Concatenate the split genres back to the original DataFrame
    items = pd.concat([items, genres_split], axis=1)

    # Drop the original 'genre' and 'cleaned_genre' columns if desired
    items.drop(columns=['genre', 'cleaned_genre'], inplace=True)

    lyrics = pd.DataFrame(
        [(lyr.Themes, lyr.Band_ID) for lyr in lyrical_data],
        columns=['theme', 'item']
    )

    themes_split = lyrics['theme'].str.split(',', expand=True)
    themes_split = themes_split.fillna('missing')
    #limit it to max 6 themes
    themes_split = themes_split.iloc[:, :4]
    # Optionally rename columns before concatenation
    themes_split.columns = [f'theme{i+1}' for i in range(themes_split.shape[1])]

    # Concatenate the split themes back to the original DataFrame
    lyrics = pd.concat([lyrics, themes_split], axis=1)

    # Drop the original 'Themes' column
    lyrics.drop(columns=['theme'], inplace=True)

    # Complete band set, used separately later on as well
    all_items = items.merge(lyrics, on='item')

    #Add randomly selected negatives for new bands to be recommended.
    negative_samples = generate_negative_samples(users, all_items)
    users = pd.concat([users, negative_samples], ignore_index=True)
    users['nationality'] = "Dutch"
    users['sex'] = "Male"
    users['age'] = 20
    #Create one big dataset
    data = users.merge(all_items, on='item')

    return data, users

def generate_negative_samples(users, items):
    """Generate negative samples for each user. For each user, select random bands they haven't interacted with and assign label=0."""
    all_bands = set(items['item'])  # All available bands
    negative_samples = []

    for user_id in users['user'].unique():
        interacted_bands = set(users[users['user'] == user_id]['item'])
        non_interacted_bands = all_bands - interacted_bands

        sampled_negative_bands = random.sample(non_interacted_bands, min(len(non_interacted_bands), len(interacted_bands)))
        
        for band in sampled_negative_bands:
            negative_samples.append((user_id, band, 0))  # label=0 for negative samples

    negative_samples_df = pd.DataFrame(negative_samples, columns=['user', 'item', 'label'])
    return negative_samples_df

def train(model, train_data, eval_data):
    model.fit(
    train_data,
    neg_sampling=False,  # Negative samples are created by {def generate_negative_samples(users, items)}
    verbose=2,
    shuffle=True,
    eval_data=eval_data,
    metrics=["loss", "roc_auc", "precision", "recall", "ndcg"],
    )

def fresh_training():
    data, users = load_data()
    print(data.shape)
    print(users.shape)

    data
    train_data, eval_data = random_split(data, multi_ratios=[0.8, 0.2], seed=42)

    # Sparse columns (categorical with many unique values)
    sparse_col = ["sex", "nationality", "band_name", "country", "status", "genre1", "genre2", "genre3", "genre4", "theme1", "theme2", "theme3", "theme4"]
    # Dense columns (numerical with fewer unique values)
    dense_col = ["age"]
    # User columns (user attributes)
    user_col = ["sex", "age", "nationality"]
    # Item columns (item attributes)
    item_col = ["band_name", "country", "status", "genre1", "genre2", "genre3", "genre4", "theme1", "theme2", "theme3", "theme4"]

    train_data, data_info = DatasetFeat.build_trainset(train_data, user_col, item_col, sparse_col, dense_col)
    eval_data = DatasetFeat.build_evalset(eval_data)

    model = WideDeep(
        task="ranking",
        data_info=data_info,
        embed_size=16,
        n_epochs=10,
        loss_type="cross_entropy",
        lr={"wide": 0.05, "deep": 7e-4},
        batch_size=100,
        use_bn=True,
        hidden_units=(128, 64, 32),
    )
    #Train
    train(model, train_data, eval_data)
    #Save
    data_info.save(model_path, model_name=model_name)
    model.save(model_path, model_name=model_name)

def update_model(new_data):
    loaded_data_info = DataInfo.load(model_path, model_name=model_name)
    train_data, eval_data = random_split(new_data, multi_ratios=[0.8, 0.2])
    train_data, new_data_info = DatasetFeat.merge_trainset(train_data, loaded_data_info, merge_behavior=True)
    eval_data = DatasetFeat.merge_evalset(eval_data, new_data_info)

    clear_session()

    model = WideDeep(
    task="ranking",
    data_info=new_data_info,  # pass new_data_info
    embed_size=16,
    n_epochs=2,
    loss_type="cross_entropy",
    lr={"wide": 0.01, "deep": 1e-4},
    batch_size=2048,
    use_bn=True,
    hidden_units=(128, 64, 32),
    )

    model.rebuild_model(path=model_path, model_name=model_name, full_assign=True)

    #Train
    train(model, train_data, eval_data)
    #Save
    new_data_info.save(model_path, model_name=model_name)
    model.save(model_path, model_name=model_name)

def use_model(model_name):
    loaded_data_info = DataInfo.load(model_path, model_name=model_name)
    loaded_model = WideDeep.load(model_path, model_name=model_name, data_info=loaded_data_info)
    print(loaded_model.recommend_user(user=1, n_rec=10))

if __name__ == "__main__":
    use_model(model_name)