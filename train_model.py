from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import os

# Load and encode your dataset
df = pd.read_csv("employee_behavior_dataset.csv")
label_encoder = LabelEncoder()
df['label_encoded'] = label_encoder.fit_transform(df['label'])  # Encode labels as 0, 1, 2

# Save the encoded dataset
df.to_csv("encoded_employee_behavior_dataset.csv", index=False)

# Load the dataset using Hugging Face Datasets
dataset = load_dataset("csv", data_files="encoded_employee_behavior_dataset.csv")

# Tokenize the input sentences
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

def tokenize(batch):
    return tokenizer(batch["sentence"], padding=True, truncation=True)

# Rename the label column to 'labels' for compatibility with Trainer
dataset = dataset.rename_column("label_encoded", "labels")
dataset = dataset.map(tokenize, batched=True)

# Set the format for PyTorch
dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])

# Prepare model
model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=3)

# Training setup
training_args = TrainingArguments(
    output_dir="./behavior_model",
    per_device_train_batch_size=8,
    num_train_epochs=4,
    save_total_limit=1,
    logging_dir="./logs",
    save_steps=500,  # Save the model every 500 steps
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
)

# Train model
print("Starting training...")
trainer.train()
print("Training completed successfully.")

# Save the model and tokenizer
os.makedirs("./behavior_model", exist_ok=True)
model.save_pretrained("./behavior_model")
tokenizer.save_pretrained("./behavior_model")
print("Model and tokenizer saved to ./behavior_model")

# Save the label encoder mapping for later use
label_mapping = {int(k): str(v) for k, v in zip(label_encoder.transform(label_encoder.classes_), label_encoder.classes_)}
with open("./behavior_model/label_mapping.json", "w") as f:
    import json
    json.dump(label_mapping, f)
print("Label mapping saved:", label_mapping)
