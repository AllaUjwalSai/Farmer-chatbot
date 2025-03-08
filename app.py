from flask import Flask, render_template, request, jsonify
import os
import autogen
import requests
import pandas as pd

app = Flask(__name__)
os.environ["OPENAI_API_KEY"] = "dummy_api_key"

# Load CSV file into a DataFrame
try:
    csv_df = pd.read_csv(r"C:\Users\ujwal\PycharmProjects\GITAM_HACKATHON\fertilizers_pesticides_india.csv")
except Exception as e:
    csv_df = None
    print("Error loading CSV file:", e)


def get_relevant_csv_data(question):
    """
    Extract CSV rows where the product name appears in the question.
    This simple substring match is used for demonstration.
    """
    if csv_df is None:
        return "CSV data not available."

    question_lower = question.lower()
    # Filter rows where the product name (in lowercase) is found in the question
    relevant_rows = csv_df[csv_df['Product Name'].str.lower().apply(lambda name: name in question_lower)]

    if not relevant_rows.empty:
        return relevant_rows.to_csv(index=False)
    return "No relevant CSV data found."


def create_extra_context(question):
    """
    Create extra context by retrieving relevant CSV data.
    """
    relevant_csv = get_relevant_csv_data(question)
    extra_context = (
            "Relevant CSV data:\n" + relevant_csv
    )
    return extra_context


# Local LLM configuration (for LM Studio)
llm_config_local = {
    "config_list": [{
        "model": "llama2",
        "base_url": "http://localhost:1234/v1",
    }]
}

# Define Assistant Agent (Bob) with farming expertise.
# Bob’s original system message remains unchanged.
bob = autogen.AssistantAgent(
    name="Bob",
    system_message="You are an expert in agriculture. Answer questions for farmers from India concisely in 2-3 sentences. When mentioning a chemical, include its details in the format: Product Name,Category,Major Sellers/Companies but reduce content to 3 sentences at max.",
    llm_config=llm_config_local
)

# Define User Proxy Agent (configured for web interaction)
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    code_execution_config={"use_docker": False},
    is_termination_msg=lambda msg: "TERMINATE" in msg.get("content", ""),
    human_input_mode="NEVER",
    llm_config=llm_config_local
)

# Updated language codes for translation to support multiple languages.
LANGUAGE_CODES = {
    "en": "en",  # English
    "hi": "hi",  # Hindi
    "bn": "bn",  # Bengali
    "te": "te",  # Telugu
    "ta": "ta",  # Tamil
    "mr": "mr",  # Marathi
    "gu": "gu",  # Gujarati
    "kn": "kn",  # Kannada
    "ml": "ml",  # Malayalam
    "pa": "pa",  # Punjabi
    "or": "or"  # Odia
}


def translate_text(text, source_lang, target_lang):
    if source_lang == target_lang:
        return text
    try:
        # Using LibreTranslate API
        url = "https://libretranslate.com/translate"
        payload = {"q": text, "source": source_lang, "target": target_lang}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get("translatedText", text)
        else:
            print("Translation error:", response.text)
            # Fallback to unofficial Google Translate API
            try:
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={text}"
                fallback_response = requests.get(url)
                if fallback_response.status_code == 200:
                    result = fallback_response.json()
                    translated = ''.join([sentence[0] for sentence in result[0]])
                    return translated
            except Exception as fallback_error:
                print("Fallback translation error:", fallback_error)
            return text
    except Exception as e:
        print("Translation exception:", e)
        return text


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    farmer_question = data.get("message", "")
    language = data.get("language", "en")
    location = data.get("location", "Unknown location")

    if not farmer_question:
        return jsonify({"error": "Empty message"}), 400

    if language not in LANGUAGE_CODES:
        return jsonify({"error": f"Unsupported language: {language}"}), 400

    language_code = LANGUAGE_CODES[language]

    # Translate the question to English if needed
    english_question = farmer_question
    if language != "en":
        english_question = translate_text(farmer_question, language_code, "en")
        print(f"Translated question from {language} to English: {english_question}")

    # Prepend location context to the question
    question_with_context = f"Farmer is located at {location}.\n{english_question}"

    # Get extra CSV context without modifying the original agent.
    extra_context = create_extra_context(question_with_context)

    # Combine the question and extra context into one message.
    final_message = f"{question_with_context}\n\n{extra_context}"

    # Initiate chat with Bob using the final message.
    user_proxy.initiate_chat(
        bob,
        message=final_message,
        max_turns=1,
        clear_history=True
    )

    # Extract Bob's response from the conversation.
    bob_response = None
    messages = user_proxy.chat_messages.get(bob, [])
    for msg in messages:
        if msg.get("name") == "Bob" and msg.get("role") == "user":
            bob_response = msg.get("content", "")
            break

    if not bob_response:
        return jsonify({"error": "No response from Bob."}), 500

    # Translate Bob's response back to the requested language if needed.
    translated_response = bob_response
    if language != "en":
        translated_response = translate_text(bob_response, "en", language_code)
        print(f"Translated response from English to {language}: {translated_response}")

    return jsonify({"message": translated_response})


if __name__ == '__main__':
    app.run(debug=True)
