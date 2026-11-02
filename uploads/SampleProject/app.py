from flask import Flask, render_template, request
from spellchecker import SpellChecker
from textblob import TextBlob

app = Flask(__name__)

spell = SpellChecker()

whitelist = {"txt", "AI", "Flask", "pattern"}


def autocorrect(text):
    words = text.split()

    corrected = [
        word if word in whitelist
        else spell.correction(word) or word
        for word in words
    ]

    return " ".join(corrected)


def simplify_text(text):
    replacements = {
        "utilize": "use",
        "facilitate": "help",
        "commence": "start",
        "terminate": "end",
        "demonstrate": "show"
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text


def paraphrase_text(text):
    synonyms = {
        "good": "great",
        "bad": "poor",
        "big": "large",
        "important": "crucial"
    }

    words = text.split()
    new_words = []

    for w in words:
        new_words.append(synonyms.get(w.lower(), w))

    return " ".join(new_words)


@app.route("/", methods=["GET", "POST"])
def home():
    output_text = ""

    if request.method == "POST":
        text = request.form.get("text")
        action = request.form.get("action")

        if text:

            if action == "correct":
                output_text = autocorrect(text)

            elif action == "simplify":
                output_text = simplify_text(text)

            elif action == "paraphrase":
                output_text = paraphrase_text(text)

    return render_template("index.html", output_text=output_text)


if __name__ == "__main__":
    app.run(debug=True)