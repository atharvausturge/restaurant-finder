import pytesseract
import os
from google import genai
from PIL import Image

def detectText(path):
    image = Image.open(path)
    return pytesseract.image_to_string(image)

def handleAI(menuText, allergies, budget, mealType):
    print("Getting client")
    client = genai.Client()
    print("Loading Response...")
    response = client.models.generate_content(
        model="gemini-3-flash-preview", contents="Summarize the following menu:" + menuText + " Give me some good options for my budget of $" + budget + ". Do your best to avoid foods that commonly have these times: " + allergies  
    )

    return (response)


def main():
    path = "image.jpg"
    allergies = ["almonds", "soy"]
    budget = 30
    mealType = "full"
    menuText = detectText(path)
    response = handleAI(menuText, allergies, budget, mealType)
    print(response)


if __name__ == "__main__":
    main()