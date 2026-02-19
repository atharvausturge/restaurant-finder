import pytesseract
import os
from google import genai
from PIL import Image

def detectText(path):
    image = Image.open(path)
    return pytesseract.image_to_string(image)

def handleAI(menuText):
    print("Getting client")
    client = genai.Client()
    print("Loading Response...")
    response = client.models.generate_content(
        model="gemini-3-flash-preview", contents="Summarize the following menu. Give me some good options and how much I can expect to spend: " + menuText
    )

    return (response)


def main():
    path = "image.jpg"
    menuText = detectText(path)
    response = handleAI(menuText)
    print(response)


if __name__ == "__main__":
    main()