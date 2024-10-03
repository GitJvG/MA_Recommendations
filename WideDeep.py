import warnings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
warnings.filterwarnings("ignore")
from Scripts.utils import load_config
from libreco.data import DatasetFeat, random_split, DataInfo
from libreco.algorithms import WideDeep
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
model_name="wide_deep"

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
    fresh_training()
    