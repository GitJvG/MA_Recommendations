import warnings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
warnings.filterwarnings("ignore")
from Scripts.utils import load_config
from libreco.data import DatasetFeat, random_split, DataInfo
from libreco.algorithms import TwoTower
from keras.backend import clear_session
import tensorflow as tf
from Data import load_data
from libreco.evaluation import evaluate
from LibreStopping.LibreStopping import EarlyStopping
# Clone from 'https://github.com/GitJvG/LibreStopping'

tf.get_logger().setLevel('ERROR')

# Create a database engine
DATABASE_URI = load_config('SQL_Url')
ENGINE = create_engine(DATABASE_URI)
session = sessionmaker(bind=ENGINE)
SESSION = session()
MODEL_PATH = "Model"

def train(create_model, train_data, eval_data, data_info, model_path, model_name, patience=5, fit_model=None, monitor_metric='loss'):
    """
    Trains a model using early stopping, while delegating the logic to the EarlyStopping class.
    
    Parameters:
    - create_model: Function to create a new model.
    - train_data: The training data.
    - eval_data: The evaluation data.
    - data_info: Metadata about the dataset.
    - model_path: Path to save the best model.
    - model_name: Name of the model for saving.
    - patience: Patience for early stopping.

    Returns:
    Best trained model.
    """
    # Initialize EarlyStopping with full control over the training loop and evaluation
    early_stopping = EarlyStopping(model_path=model_path, 
                                   model_name=model_name, 
                                   data_info=data_info, 
                                   patience=patience,
                                   monitor_metric=monitor_metric
                                   )
    
    # Start training with early stopping and return the best model
    best_model = early_stopping.train_with_early_stopping(
        create_model=create_model,
        fit_model=fit_model,
        train_data=train_data,
        eval_data=eval_data,
        evaluate_model=evaluate_model  # Pass the evaluation function
    )
    
    return best_model

def fit_model(model, train_data, eval_data):
    """
    Fits the model using training and evaluation data, with specified metrics.

    Parameters:
    - model: The model to fit.
    - train_data: The training data to fit the model on.
    - eval_data: The evaluation data to monitor during training.

    Returns:
    None
    """
    model.fit(
        train_data,
        neg_sampling=True,  # Perform negative sampling
        verbose=1,  # Verbose output during fitting
        shuffle=True,
        eval_data=eval_data,
        metrics=["loss", "roc_auc", "precision", "recall", "ndcg"],
    )
        
def use_model(model_name,MODEL_PATH=MODEL_PATH):
    loaded_data_info = DataInfo.load(MODEL_PATH, model_name=model_name)
    loaded_model = TwoTower.load(MODEL_PATH, model_name=model_name, data_info=loaded_data_info)
    return loaded_data_info, loaded_model

def create_two_tower_model(data_info, n_epochs):
    tf.keras.backend.clear_session()
    """
    Create and return a TwoTower model.

    Parameters:
    - data_info: The data information used to build the model.
    - n_epochs: The number of epochs to train the model.

    Returns:
    - TwoTower model instance.
    """
    return TwoTower(
        "ranking",
        data_info,
        loss_type="softmax",
        embed_size=16,
        norm_embed=True,
        n_epochs=n_epochs,  # Set the number of epochs from the parameter
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

def rank_candidates(user_id, candidate_items, model):
    scores = model.predict(user_id, candidate_items)
    ranked_items = sorted(zip(candidate_items, scores), key=lambda x: x[1], reverse=True)
    
    return [item for item, score in ranked_items]

def train_two_tower():
    train_data, user_col, item_col, sparse_col, dense_col, eval_data = load_data()
    train_data, data_info = DatasetFeat.build_trainset(train_data, user_col, item_col, sparse_col, dense_col)
    eval_data = DatasetFeat.build_evalset(eval_data)
    train(create_two_tower_model, train_data, eval_data, data_info, model_path="Model", model_name="two_tower", patience=5, fit_model=fit_model, monitor_metric='roc_auc')

def evaluate_model(model, eval_data):
    evaluation_results = evaluate(
        model=model,
        data=eval_data,
        neg_sampling=True,
        metrics=["loss", "roc_auc", "precision", "recall", "ndcg"],
    )
    print(f"Evaluation Results: {evaluation_results}")
    return evaluation_results

if __name__ == "__main__":
    train_two_tower()