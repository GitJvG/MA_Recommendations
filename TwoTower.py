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
    neg_sampling=True,  # Negative samples are created by {def generate_negative_samples(users, items)}
    verbose=2,
    shuffle=True,
    eval_data=eval_data,
    metrics=["loss", "roc_auc", "precision", "recall", "ndcg"],
    )

def use_model(model_name):
    loaded_data_info = DataInfo.load(MODEL_PATH, model_name=model_name)
    loaded_model = WideDeep.load(MODEL_PATH, model_name=model_name, data_info=loaded_data_info)

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
        n_epochs=20,
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

def rank_candidates(user_id, candidate_items, model):

    scores = model.predict(user_id, candidate_items)
    ranked_items = sorted(zip(candidate_items, scores), key=lambda x: x[1], reverse=True)
    
    return [item for item, score in ranked_items]

if __name__ == "__main__":
    Twotower()