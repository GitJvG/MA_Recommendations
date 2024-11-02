import tensorflow as tf
from tensorflow.keras import layers
import numpy as np
import pandas as pd
from Data import load_data, load_item_arrays

MODEL_PATH = "model_folder_path"
all_item_features_array, item_ids = load_item_arrays()

class ModifiedTwoTower(tf.keras.Model):
    def __init__(
        self, task, data_info, embed_size=16,
        user_hidden_units=(128, 64), item_hidden_units=(256, 128),
        user_dropout_rate=0.2, item_dropout_rate=0.2, use_bn=True, l2_reg=0.01
    ):
        super(ModifiedTwoTower, self).__init__()
        self.task = task
        self.data_info = data_info
        self.embed_size = embed_size
        self.l2_reg = l2_reg
        self.use_bn = use_bn
        self.user_dropout_rate = user_dropout_rate

        self.user_embedding = layers.Embedding(
            input_dim=data_info['num_users'], output_dim=embed_size,
            embeddings_regularizer=tf.keras.regularizers.l2(l2_reg),
            name="user_embedding"
        )

        self.item_embedding = layers.Embedding(
            input_dim=data_info['num_items'], output_dim=embed_size,
            embeddings_regularizer=tf.keras.regularizers.l2(l2_reg),
            name="item_embedding"
        )

        self.user_dense_layers = self._create_dense_layers(user_hidden_units, "user")
        self.item_dense_layers = self._create_dense_layers(item_hidden_units, "item")

        self.user_output_layer = layers.Dense(embed_size, activation=None, name="user_output_layer")
        self.item_output_layer = layers.Dense(embed_size, activation=None, name="item_output_layer")

        self.output_layer = layers.Dense(1, activation='sigmoid', name="output_layer")

        self.optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)

    def _create_dense_layers(self, hidden_units, name_prefix):
        """Helper to create dense, batch norm, and dropout layers with improved structure."""
        dense_layers = []
        for i, units in enumerate(hidden_units):
            dense_layers.append(layers.Dense(
                units, kernel_regularizer=tf.keras.regularizers.l2(self.l2_reg),
                name=f'{name_prefix}_dense_{i}'
            ))
            if self.use_bn:
                dense_layers.append(layers.BatchNormalization(name=f'{name_prefix}_bn_{i}'))
            dense_layers.append(layers.LeakyReLU(name=f'{name_prefix}_leakyrelu_{i}'))  # Use LeakyReLU
            if self.user_dropout_rate > 0:
                dense_layers.append(layers.Dropout(self.user_dropout_rate, name=f'{name_prefix}_dropout_{i}'))
        return dense_layers

    def user_tower(self, user_indices):
        """Create user embeddings using the user tower."""
        user_embeds = self.user_embedding(user_indices)
        user_embeds = self.apply_dense_layers(user_embeds, self.user_dense_layers)
        return self.user_output_layer(user_embeds)

    def item_tower(self, item_indices, item_features):
        """Create item embeddings using item tower with dense layers and features."""

        item_embeds = self.item_embedding(item_indices)
        item_feature_embeds = self.apply_dense_layers(item_features, self.item_dense_layers)
        combined_item_embeds = tf.concat([item_embeds, item_feature_embeds], axis=-1)

        return self.item_output_layer(combined_item_embeds)

    def apply_dense_layers(self, inputs, layers_sequence):
        """Helper function to apply a sequence of layers to inputs."""
        x = inputs
        for layer in layers_sequence:
            x = layer(x)
        return x

    def similarity_score(self, user_indices, item_indices, item_features_array):
        """Compute similarity score between user and item embeddings."""
        user_embeddings = self.user_tower(user_indices)
        item_combined_embeddings = self.item_tower(item_indices, item_features_array)  # Updated to use the item_tower

        score = tf.reduce_sum(user_embeddings * item_combined_embeddings, axis=1)
        logits = self.output_layer(tf.expand_dims(score, axis=-1))
        return tf.squeeze(logits, axis=-1)

    def train_step(self, user_indices, item_indices, item_features_array, labels):
        """Train step with loss calculation and backpropagation."""
        with tf.GradientTape() as tape:
            logits = self.similarity_score(user_indices, item_indices, item_features_array)  # Pass item_indices
            labels = tf.cast(labels, tf.float32)
            loss = tf.keras.losses.BinaryCrossentropy()(y_true=labels, y_pred=logits)
            gradients = tape.gradient(loss, self.trainable_variables)
            self.optimizer.apply_gradients(zip(gradients, self.trainable_variables))
        
        return loss

    @tf.function(input_signature=[
        tf.TensorSpec(shape=[None], dtype=tf.int32),
        tf.TensorSpec(shape=[None, None], dtype=tf.float32),
        tf.TensorSpec(shape=[None], dtype=tf.int32)
    ])
    def infer(self, user_indices, item_features_array, item_indices):
        """Inference method to return the similarity score."""
        score = self.similarity_score(user_indices, item_indices, item_features_array)
        return {"similarity_score": score}

def train(epochs=10, batch_size=32, path=None):
    """Train the ModifiedTwoTower model with user and item preferences."""
    users_preference, user_dimensions = load_data()

    # Map user IDs (adjusting for 0 based indexing)
    user_indices = users_preference['user'].values - 1
    user_indices = np.array(user_indices, dtype=np.int32).flatten()

    item_indices = np.searchsorted(item_ids, users_preference['item'].values, side='left')
    labels = users_preference['label'].values.astype(np.float32)

    data_info = {
        'num_users': len(user_dimensions['user'].unique()),
        'num_items': len(item_ids)
    }
    model = ModifiedTwoTower(task="classification", data_info=data_info)
    dummy_user_indices = tf.constant(user_indices[:1], dtype=tf.int32)  # Just one sample
    dummy_item_indices = tf.constant(item_indices[:1], dtype=tf.int32)  # Just one sample
    dummy_item_features = tf.constant(all_item_features_array[item_indices[:1]], dtype=tf.float32)  # One sample of features
    model.similarity_score(dummy_user_indices, dummy_item_indices, dummy_item_features)

    dataset = tf.data.Dataset.from_tensor_slices((user_indices, item_indices, all_item_features_array[item_indices], labels))
    dataset = dataset.shuffle(buffer_size=len(user_indices)).batch(batch_size).prefetch(tf.data.AUTOTUNE)

    # Training loop
    for epoch in range(epochs):
        epoch_loss = 0.0
        for user_batch, item_batch, item_features_batch, label_batch in dataset:
            try:
                epoch_loss += model.train_step(user_batch, item_batch, item_features_batch, label_batch).numpy()
            except Exception as e:
                print(f"Error during training: {e}")
                continue
            
        print(f"Epoch {epoch + 1}, Loss: {epoch_loss / len(dataset):.4f}")

    tf.saved_model.save(model, path, signatures={'serving_default': model.infer})
    print("Model saved successfully.")

def test(path, test_user_id, test_item_ids):
    loaded_model = tf.saved_model.load(path)
    print("Model loaded successfully.")
    test_user_index = test_user_id - 1

    # Prepare lists for batch inference
    test_item_indices = []
    item_features_batch = []

    for test_item_id in test_item_ids:
        item_indices = np.where(item_ids == test_item_id)[0]

        if item_indices.size == 0:
            print(f"Item ID {test_item_id} not found in the training data.")
            continue  # Skip to the next item ID

        # There should be only one matching index for each item ID
        test_item_index = item_indices[0]
        test_item_indices.append(test_item_index)
        item_features_batch.append(all_item_features_array[test_item_index])

    if not test_item_indices:
        print("No valid items found for inference.")
        return

    test_item_indices = np.array(test_item_indices, dtype=np.int32)
    item_features_batch = np.array(item_features_batch)
    item_tensor = tf.constant(item_features_batch, dtype=tf.float32)
    item_index_tensor = tf.constant(test_item_indices, dtype=tf.int32)

    user_tensor = tf.constant([test_user_index] * len(test_item_indices), dtype=tf.int32)

    infer_fn = loaded_model.signatures['serving_default']
    try:
        predictions = infer_fn(user_indices=user_tensor, item_features_array=item_tensor, item_indices=item_index_tensor)
        # Print predictions for each item
        for test_item_id, score in zip(test_item_ids, predictions['similarity_score'].numpy()):
            print(f"Prediction for User {test_user_id} and Item {test_item_id}: {score}")
    except Exception as e:
        print(f"Error during batch inference: {e}")

if __name__ == "__main__":
    test(MODEL_PATH, 1, [72, 115])
    """train(10,32,MODEL_PATH)"""