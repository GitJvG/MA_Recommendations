import warnings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import random
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
warnings.filterwarnings("ignore")
from app.models import UserBandPreference, Item, users as Users
from Scripts.utils import load_config
from libreco.data import DatasetFeat, random_split, DataInfo
from libreco.algorithms import WideDeep
from keras.backend import clear_session
import tensorflow as tf
tf.get_logger().setLevel('ERROR')

# Create a database engine
DATABASE_URI = load_config('SQL_Url')
ENGINE = create_engine(DATABASE_URI)
session = sessionmaker(bind=ENGINE)
SESSION = session()
MODEL_PATH ="Model"
model_name="wide_deep"

def load_data():
    # Load data from your tables
    user_band_preference_data = SESSION.query(UserBandPreference).all()
    user_dimensions = SESSION.query(Users).all()

    # User preferences
    users_preference = pd.DataFrame(
        [(pref.user_id, pref.band_id, pref.liked) for pref in user_band_preference_data],
        columns=['user', 'item', 'label']
    )
    #Subset for faster calculations
    interacted_band_ids = set(users_preference['item'])

    #User dimensions
    user_dimensions = pd.DataFrame(
        [(dim.id, dim.username, dim.Birthyear, dim.gender, dim.nationality, dim.genre1, dim.genre2, dim.genre3) for dim in user_dimensions],
        columns=['user', 'username', 'birthyear', 'gender', 'nationality', 'ugenre1', 'ugenre2', 'ugenre3']
    )
    #Only query ID's until the subset details are needed for are defined.
    band_ids = SESSION.query(Item.item).filter(Item.item.notin_(interacted_band_ids)).all()
    band_ids = pd.DataFrame(band_ids, columns=['item'])
    

    #Add randomly selected negatives for new bands to be recommended.
    negative_samples = generate_negative_samples(users_preference, band_ids)
    #Complete list of user interactions + neg samples
    users = pd.concat([users_preference, negative_samples], ignore_index=True)
    #Add user dimensions to complete user interaction list
    users = users.merge(user_dimensions, on='user')

    #Only query details for interactions and negative samples
    detailed_band_data = SESSION.query(Item).filter(Item.item.in_(users['item'])).all()
    items = pd.DataFrame(
        [(band.item, band.band_name, band.country, band.status, band.genre1, band.genre2, 
          band.genre3, band.genre4, band.theme1, band.theme2, band.theme3, band.theme4) for band in detailed_band_data],
        columns=['item', 'band_name', 'country', 'status', 'igenre1', 'igenre2', 'igenre3', 'igenre4',
                 'theme1', 'theme2', 'theme3', 'theme4']
    )
    
    #Fillna, applied on whole dataframe because of the large amount of columns that could contain nulls
    items.fillna("missing", inplace=True)

    #Create one big dataset
    data = users.merge(items, on='item')
    print(data.info())
    return data

def generate_negative_samples(users, items):
    """Generate negative samples for each user. For each user, select random bands they haven't interacted with and assign label=0."""
    negative_samples = []
    all_bands = set(items['item'])
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
    data = load_data()
    print(data.shape)


    data
    train_data, eval_data = random_split(data, multi_ratios=[0.8, 0.2], seed=42)

    # Sparse columns (categorical with many unique values)
    sparse_col = [
        "nationality", "band_name", "country", "status",
        "ugenre1", "ugenre2", "ugenre3",
        "igenre1", "igenre2", "igenre3", "igenre4",
        "theme1", "theme2", "theme3", "theme4", "gender"
    ]
    
    # Dense columns (numerical with fewer unique values)
    dense_col = ["birthyear"]  # Optional to derive 'age'

    # User columns (user attributes)
    user_col = [
        "birthyear", "gender", "nationality",
        "ugenre1", "ugenre2", "ugenre3"
    ]

    # Item columns (item attributes)
    item_col = [
        "band_name", "country", "status",
        "igenre1", "igenre2", "igenre3", "igenre4",
        "theme1", "theme2", "theme3", "theme4"
    ]

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
    data_info.save(MODEL_PATH, model_name=model_name)
    model.save(MODEL_PATH, model_name=model_name)

def update_model(new_data):
    loaded_data_info = DataInfo.load(MODEL_PATH, model_name=model_name)
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

    model.rebuild_model(path=MODEL_PATH, model_name=model_name, full_assign=True)

    #Train
    train(model, train_data, eval_data)
    #Save
    new_data_info.save(MODEL_PATH, model_name=model_name)
    model.save(MODEL_PATH, model_name=model_name)

def use_model(model_name):
    loaded_data_info = DataInfo.load(MODEL_PATH, model_name=model_name)
    loaded_model = WideDeep.load(MODEL_PATH, model_name=model_name, data_info=loaded_data_info)
    print(loaded_model.recommend_user(user=1, n_rec=10))

if __name__ == "__main__":
    use_model(model_name)