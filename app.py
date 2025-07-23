
import streamlit as st
from collections import Counter
import re

def extract_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    common_words = set([
        'the', 'and', 'for', 'with', 'that', 'this', 'from', 'are', 'you', 'your',
        'will', 'have', 'has', 'our', 'who', 'all', 'not', 'but', 'can', 'any',
        'may', 'job', 'role', 'we', 'as', 'to', 'of', 'in', 'on', 'a', 'an', 'is', 'be'
    ])
    keywords = [word for word in words if word not in common_words and len(word) > 2]
    return [word for word, _ in Counter(keywords).most_common(20)]

def rewrite_cv(cv_text, jd_text):
    jd_keywords = extract_keywords(jd_text)
    cv_keywords = extract_keywords(cv_text)
    missing_keywords = [kw for kw in jd_keywords if kw not in cv_keywords]
    updated_cv = cv_text.strip() + "\n\n--- Added Keywords to Match JD ---\n" + ", ".join(missing_keywords)
    return updated_cv

st.title("CV Rewriter to Match Job Description")

jd_input = st.text_area("Paste Job Description Here", height=200)
cv_input = st.text_area("Paste Your CV Here", height=200)

if st.button("Rewrite CV"):
    if jd_input and cv_input:
        updated_cv = rewrite_cv(cv_input, jd_input)
        st.subheader("Updated CV")
        st.text_area("Result", value=updated_cv, height=300)
    else:
        st.warning("Please paste both the job description and your CV.")
