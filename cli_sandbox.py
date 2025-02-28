import os
import math
from llama_cpp import Llama

model_path = "/home/martin/Documents/test_cestiny_pro_LLM/LocalLLMTool/models/aya-expanse-8b-Q4_K_M.gguf"
model = Llama(model_path=model_path, n_ctx=2048, n_threads=os.cpu_count(), logits_all=True, verbose=False)

# Define input text
input_text = "Call Mr Jones at 760 458 123, ok?"
prompt = f"""You are a text anonymizer. Your task is to anonymize the following text. Replace all personal identifiable information (names, addresses, phone numbers, emails, specific locations, etc.) with generic placeholders. Maintain the meaning and structure of the text, but remove any information that could identify specific individuals or organizations.

Orignal text: 'My name is James and I live at 17 Quaker street.'
Anonymized text: 'My name is *** and I live at ***.'

Original text: '{input_text}'
Anonymized text: '"""

# Tokenize input_text using the model's tokenizer
input_tokens = model.tokenize(input_text.encode("utf-8"))
input_token_strings = [model.detokenize([token]).decode("utf-8") for token in input_tokens]

generated_output = "" # Tracking input
anonymized_output = "" # Anonymized output
last_was_placeholder = False  # Prevents duplicate placeholders

current_index = 0  # Track position in tokenized input

for _ in range(len(input_tokens)):
    response = model.create_completion(
        prompt=prompt + generated_output,
        max_tokens=1,
        logprobs=5  # Get log probabilities for top 5 tokens
    )

    predicted_token = response['choices'][0]['text']
    current_input_token = input_token_strings[current_index]

    # Print input and predicted token
    print(f"Input Token: '{current_input_token}', Predicted Token: '{predicted_token}'")

    # Extract log probabilities of top-5 tokens
    top_logprobs = response['choices'][0]['logprobs']['top_logprobs'][0]

    # Convert log probabilities to normal probabilities and print them
    print("Top-5 token probabilities:")
    for token, logprob in top_logprobs.items():
        probability = math.exp(logprob)  # Convert log probability to probability
        print(f"  Token: '{token}', Probability: {probability:.4f}")

    # Anonymization logic
    if predicted_token.strip().startswith("*"):
        if not last_was_placeholder:
            anonymized_output += predicted_token
            last_was_placeholder = True
    else:
        anonymized_output += current_input_token
        last_was_placeholder = False

    generated_output += current_input_token
    current_index += 1

print("\nFinal Anonymized Output:")
print(anonymized_output)
