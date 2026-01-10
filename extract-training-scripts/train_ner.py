import json
import numpy as np
import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForTokenClassification, 
    TrainingArguments, 
    Trainer,
    DataCollatorForTokenClassification
)
import evaluate

# 1. Config
MODEL_NAME = "csebuetnlp/banglabert_small"
DATA_PATH = "Processed data/ner_training_data.json"
OUTPUT_DIR = "models/banglabert-address-ner"

# 2. Load Data and Labels
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# Extract unique labels
unique_labels = set()
for item in raw_data:
    for tag in item['ner_tags']:
        unique_labels.add(tag)

label_list = sorted(list(unique_labels))
label2id = {l: i for i, l in enumerate(label_list)}
id2label = {i: l for i, l in enumerate(label_list)}

# 3. Tokenizer and Alignment
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(
        examples["tokens"], 
        truncation=True, 
        is_split_into_words=True,
        padding="max_length",
        max_length=128
    )

    labels = []
    for i, label in enumerate(examples["ner_tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100) # Special tokens
            elif word_idx != previous_word_idx:
                label_ids.append(label2id[label[word_idx]])
            else:
                # For subwords, we can either use the same label or O. 
                # Usually same label (I-tag) or -100 to ignore.
                label_ids.append(label2id[label[word_idx]])
            previous_word_idx = word_idx
        labels.append(label_ids)

    tokenized_inputs["labels"] = labels
    return tokenized_inputs

# 4. Prepare Dataset
dataset = Dataset.from_list(raw_data)
tokenized_dataset = dataset.map(tokenize_and_align_labels, batched=True)
tokenized_dataset = tokenized_dataset.train_test_split(test_size=0.1)

# 5. Metrics
metric = evaluate.load("seqeval")

def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    true_predictions = [
        [label_list[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [label_list[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    results = metric.compute(predictions=true_predictions, references=true_labels)
    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }

# 6. Model and Training
model = AutoModelForTokenClassification.from_pretrained(
    MODEL_NAME, 
    num_labels=len(label_list),
    id2label=id2label,
    label2id=label2id
)

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=10,
    weight_decay=0.01,
    save_total_limit=2,
    logging_steps=100,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["test"],
    tokenizer=tokenizer,
    data_collator=DataCollatorForTokenClassification(tokenizer),
    compute_metrics=compute_metrics,
)

if __name__ == "__main__":
    trainer.train()
    trainer.save_model(f"{OUTPUT_DIR}/final")
    print(f"Model saved to {OUTPUT_DIR}/final")
