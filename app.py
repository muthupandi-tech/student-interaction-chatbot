from flask import Flask, render_template, request, jsonify
import pandas as pd
import difflib

app = Flask(__name__)

# Load data from Excel file
df = pd.read_excel('chat_data.xlsx')   # or use 'chat_data.csv'

knowledge_base = {}
for _, row in df.iterrows():
    question = row['Question'].strip().lower()
    answer = row['Answer'].strip()
    aliases = [question]  # include the main question too

    if pd.notna(row['Aliases']):
        aliases += [alias.strip().lower() for alias in row['Aliases'].split(',')]

    for alias in aliases:
        knowledge_base[alias] = answer

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get', methods=['POST'])
def get_bot_response():
    user_input = request.form['msg'].strip().lower()
    best_match = difflib.get_close_matches(user_input, knowledge_base.keys(), n=1, cutoff=0.5)

    if best_match:
        return jsonify({'reply': knowledge_base[best_match[0]]})
    else:
        return jsonify({'reply': "Sorry, I couldn't find the answer. Please ask something else."})

if __name__ == '__main__':
    app.run(debug=True)
