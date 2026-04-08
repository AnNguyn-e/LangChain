from pypdf import PdfReader
from typing import List, Optional
reader = PdfReader("README.pdf ")
metadata= reader.metadata
page= reader.pages[0]
for key, value in metadata.items():
    print(f"{key}: {value}")
for  i in range(len(reader.pages)):
    page= reader.pages[i]
    print("Page "+str(i)+": "+str(page.extract_text(0)))
#All the flowwing could be None if they are not defined in the PDF file
print("Title: " + str(metadata.title))
print("Author: " + str(metadata.author))
print("Subject: " + str(metadata.subject))
print("Creator: " + str(metadata.creator))
print("Page extract:"+ str(page.extract_text(0)))
print("Page layout extract:"+ str(page.extract_text(extraction_mode="layout")))
print("page extract with objects:"+ str(page.extract_text(extraction_mode="plain")))
def replace_ligatures(text):
    ligatures = {
        "ﬁ": "fi",
        "ﬂ": "fl",
        "ﬀ": "ff",
        "ﬃ": "ffi",
        "ﬄ": "ffl",
        "ﬅ": "ft",
        "ﬆ": "st"
    }
    for ligature, replacement in ligatures.items():
        text = text.replace(ligature, replacement)
    return text
def remove_hyphenation(text):
    lines = text.splitlineS()