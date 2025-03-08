# Ask Farmer Bhai

Ask Farmer Bhai is a chatbot designed to assist Indian farmers by answering their agriculture-related questions. It integrates a local LLM (Llama 2) with farming expertise and provides responses in multiple Indian languages. The chatbot also utilizes a dataset of fertilizers and pesticides to enhance responses.

## Features
- **Multi-language Support**: Supports translations for multiple Indian languages.
- **Geolocation-based Context**: Uses user's location to provide relevant farming advice.
- **CSV Data Integration**: Fetches relevant data from a preloaded CSV file on fertilizers and pesticides.
- **Speech Recognition & Text-to-Speech**: Allows users to ask questions using voice input and listen to responses.
- **Map-based & Manual Location Selection**: Users can set their location using a map or enter it manually.

## Installation
### Prerequisites
- Python 3.12
- Flask
- Pandas
- Requests
- Autogen

### Setup Instructions
1. Clone this repository:
   ```sh
   git clone https://github.com/your-repo/ask-farmer-bhai.git
   cd ask-farmer-bhai
