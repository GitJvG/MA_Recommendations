import warnings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
warnings.filterwarnings("ignore")
from Scripts.utils import load_config
from libreco.data import DatasetFeat, random_split, DataInfo
from libreco.algorithms import WideDeep, TwoTower
from keras.backend import clear_session
import tensorflow as tf
tf.get_logger().setLevel('ERROR')
from Data import load_data

# Create a database engine
DATABASE_URI = load_config('SQL_Url')
ENGINE = create_engine(DATABASE_URI)
session = sessionmaker(bind=ENGINE)
SESSION = session()
MODEL_PATH ="Model"

def train(model, train_data, eval_data):
    model.fit(
    train_data,
    neg_sampling=False,  # Negative samples are created by {def generate_negative_samples(users, items)}
    verbose=2,
    shuffle=True,
    eval_data=eval_data,
    metrics=["loss", "roc_auc", "precision", "recall", "ndcg"],
    )

def fresh_training(model_name):
    train_data, user_col, item_col, sparse_col, dense_col, eval_data = load_data()

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

def use_model(model_name):
    loaded_data_info = DataInfo.load(MODEL_PATH, model_name=model_name)
    loaded_model = WideDeep.load(MODEL_PATH, model_name=model_name, data_info=loaded_data_info)
    print(loaded_model.recommend_user(user=1, n_rec=10))

def Twotower():
    train_data, user_col, item_col, sparse_col, dense_col, eval_data = load_data()

    train_data, data_info = DatasetFeat.build_trainset(train_data, user_col, item_col, sparse_col, dense_col)
    eval_data = DatasetFeat.build_evalset(eval_data)

    two_tower = TwoTower(
        "ranking",
        data_info,
        loss_type="softmax",
        embed_size=16,
        norm_embed=True,
        n_epochs=75,
        lr=0.01,
        lr_decay=False,
        reg=None,
        batch_size=2048,
        num_neg=1,
        use_bn=False,
        dropout_rate=None,
        hidden_units=(128, 64, 32),
        use_correction=True,
        temperature=0.1,
        ssl_pattern=None,
        tf_sess_config=None,
    )

    train(two_tower, train_data, eval_data)
    #Save
    data_info.save(MODEL_PATH, model_name="two_tower")
    two_tower.save(MODEL_PATH, model_name="two_tower")

def generate_candidates(user_id, all_items, user_preferences, top_n=10):
    """Generate candidate items for a user based on popularity and their preferences."""
    # 1. Filter items based on user preferences (for example, genre)
    preferred_items = user_preferences[user_preferences['user'] == user_id]['item'].values
    
    # 2. Generate candidates from preferred items and popular items
    candidate_items = set(preferred_items) | set(all_items['item'].value_counts().nlargest(top_n).index)
    
    return list(candidate_items)

def rank_candidates(user_id, candidate_items, model):

    scores = model.predict(user_id, candidate_items)
    ranked_items = sorted(zip(candidate_items, scores), key=lambda x: x[1], reverse=True)
    
    return [item for item, score in ranked_items]


if __name__ == "__main__":
    Twotower()