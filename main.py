#ALL iports from here

import streamlit as st 
from PIL import Image
import pytesseract
import pandas as pd
from PyPDF2 import PdfReader
import fitz
import io
import google.generativeai as genai
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

#requried setups for apiand text extraction

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

genai.configure(api_key="${{secrets.MY_API_KEY}}")
model = genai.GenerativeModel("gemini-2.5-flash")

#code below 
st.title("Notes Summarizer")
st.subheader("Summarize your notes in seconds")
st.write("Enter your text below and click the button to summarize.")
file=st.file_uploader("Upload your notes",type=["pdf","jpg","jpeg","csv"])  #taking input file from user
notes_type=st.radio("Select the type of notes you want to summarize:", ("Typed Notes","Handwritten Notes"),horizontal=True)

#Extracting text 
full_text=""
if file is not None:
    st.success("File uploaded successfully, file type: "+file.type)

    if notes_type=="Typed Notes":
        if file.type in ["image/jpg", "image/png", "image/jpeg"]:
            st.image(file, caption="Uploaded Image", width=max(100,300))
            image=Image.open(file)
            text=pytesseract.image_to_string(image)
            st.write("Extracted Text:")
            st.write(text)
            full_text=text+"\n"


        elif file.type in ["text/csv"]:
            data=pd.read_csv(file)
            st.write("CSV Data:")
            st.dataframe(data)
            full_text=data.to_string()+"\n"

        elif file.type == "application/pdf":
            try:
                pdf=fitz.open(stream=file.read(), filetype="pdf")
                text=""
                for page in pdf:
                    text += page.get_text("text")
                st.text_area("Extracted Text:", value=text, height=350)
                #     pix=page.get_pixmap()
                #     img=Image.open(io.BytesIO(pix.tobytes("png")))
                #     text = pytesseract.image_to_string(img)
                #     full_text=text+"\n"
                # st.text_area("Extracted Text:", value=full_text, height=300)
                full_text=text+"\n"

            except Exception as e:
                st.error(e)

        else:
            st.write("Unsupported file type. Please upload a PDF, image, or CSV file.")

    if notes_type=="Handwritten Notes":
        if file.type in ["image/jpg", "image/png", "image/jpeg"]:
            st.image(file, caption="Uploaded Image", width=max(100,300))
            image=Image.open(file)
            text = model.generate_content([
                    "Extract all handwritten text exactly as written.",
                    image
                    ]) 
            st.write("Extracted Text:")
            st.write(text.text)
            full_text=text.text+"\n"

        elif file.type == "application/pdf":
            try:
                pdf=fitz.open(stream=file.read(), filetype="pdf")
                text=""
                for page in pdf:
                    pix=page.get_pixmap()
                    img=Image.open(io.BytesIO(pix.tobytes("png")))
                    response = model.generate_content([
                    "Extract all handwritten text exactly as written.",
                    img
                    ]) 
                st.text_area("Extracted Text:", value=response.text, height=300)
                full_text=response.text+"\n"

            except Exception as e:
                st.error(e)

        else:
            st.write("Unsupported file type. Please upload a PDF or image file.")

#AI Summarization
prompt=f'''You are an expert study assistant.

Analyze the following notes carefully.

Your tasks are:
1. Correct obvious spelling mistakes without changing the meaning.
2. Remove duplicate or unnecessary information.
3. Keep all important facts.
4. Write the summary in simple, easy-to-understand English.
5. Organize the summary using clear headings and bullet points.
6. Highlight important terms in bold.
7. Preserve formulas, equations, and technical terms exactly.
8. Do not invent information that is not present in the notes.

Notes:
{full_text}'''

response = ""
try:
    response = model.generate_content(prompt)
    st.text_area("Summary:", value=response.text, height=350)
except Exception as e:
    st.write(":red[Daily limit exceeded. Please try again later.]")

def create_pdf(text,filename="Summary.pdf"):
    doc=SimpleDocTemplate(filename,pagesize=letter)
    styles=getSampleStyleSheet()
    story=[]
    for line in text.split("\n"):
        story.append(Paragraph(line,styles["BodyText"]))

    doc.build(story)

    return filename

try:
    pdf_file=create_pdf(response.text,"summary_file")
    with open(pdf_file, "rb") as f:
        st.download_button(
            "Download PDF",
            f,
            "Summary.pdf",
            "application/pdf"
        )
except Exception as e:
    pass

