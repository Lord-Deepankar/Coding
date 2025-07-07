#translating sentences using google translate API

from deep_translator import GoogleTranslator

text = "I am learning python"
result = GoogleTranslator(sourc="en", target="it").translate(text)
print(result)