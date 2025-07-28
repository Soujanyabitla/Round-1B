from flask import Flask, render_template, request
import fitz, os, time, json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

def extract_outline(pdf_path):
    doc = fitz.open(pdf_path)
    headings, max_size, title = [], 0, os.path.splitext(os.path.basename(pdf_path))[0]
    for page_num, page in enumerate(doc, start=1):
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text, size, font = span.get("text","").strip(), span.get("size",0), span.get("font","")
                    if not text: continue
                    if size>max_size: max_size, title = size, text
                    if size>=16 or (size>=14 and text.istitle()) or (size>=13 and "bold" in font.lower()):
                        level = "H1" if size>=16 else "H2" if size>=14 else "H3"
                        headings.append({"level":level,"text":text,"page":page_num})
    return {"title":title,"outline":headings}

def rank_sections(outlines, persona, job):
    docs, all_sections = [], []
    for file, data in outlines.items():
        for h in data["outline"]:
            docs.append(h["text"])
            all_sections.append({"doc":file,"page":h["page"],"text":h["text"]})
    if not docs: return []
    vectorizer = TfidfVectorizer().fit(docs + [persona+" "+job])
    query_vec = vectorizer.transform([persona+" "+job])
    doc_vecs = vectorizer.transform(docs)
    scores = cosine_similarity(query_vec, doc_vecs)[0]
    for i,s in enumerate(scores):
        all_sections[i]["score"] = float(s)
    return sorted(all_sections,key=lambda x:x["score"],reverse=True)

@app.route("/",methods=["GET","POST"])
def index():
    if request.method=="POST":
        persona=request.form.get("persona","")
        job=request.form.get("job","")
        files=request.files.getlist("pdfs")
        os.makedirs("/tmp/pdfs",exist_ok=True)
        outlines={}
        for f in files:
            path=os.path.join("/tmp/pdfs",f.filename)
            f.save(path)
            outlines[f.filename]=extract_outline(path)
        ranked=rank_sections(outlines,persona,job)[:10]
        result={
            "metadata":{"persona":persona,"job":job,"docs":list(outlines.keys()),"timestamp":time.ctime()},
            "sections":ranked
        }

        os.makedirs("output", exist_ok=True)
        output_file = os.path.join("output", "result.json")
        with open(output_file,"w",encoding="utf-8") as f:
            json.dump(result,f,indent=2,ensure_ascii=False)

        return render_template("result.html", data=json.dumps(result,ensure_ascii=False,indent=2))
    return render_template("index.html")

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)