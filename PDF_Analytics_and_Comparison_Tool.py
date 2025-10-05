import streamlit as st
import pdfplumber
from collections import Counter
import re
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import pandas as pd

# Function to extract text from PDF with validation
def extract_text_from_pdf(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text is None:
                    raise ValueError("This appears to be a scanned PDF. Please upload a digital PDF with selectable text.")
                text += page_text
                
        if len(text.strip()) < 10:
            raise ValueError("Little to no text could be extracted. This may be a scanned PDF.")
            
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return None
    return text

def analyze_pdf(text):
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)
    char_count = len(text)
    common_words = Counter(words).most_common(10)
    sentence_count = len(re.split(r'[.!?]', text))
    line_count = text.count('\n')
    question_count = text.count('?')

    def flesch_kincaid_score(text):
        sentences = len(re.split(r'[.!?]', text))
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)
        syllables = sum(len(re.findall(r'[aeiouyAEIOUY]{1,2}', word.lower())) for word in words)
        if sentences == 0 or word_count == 0:
            return 0
        return 206.835 - 1.015 * (word_count / sentences) - 84.6 * (syllables / word_count)

    readability = flesch_kincaid_score(text)

    return {
        "Word Count": word_count,
        "Character Count": char_count,
        "Most Common Words": common_words,
        "Sentence Count": sentence_count,
        "Line Count": line_count,
        "Question Count": question_count,
        "Readability Score": readability,
    }

def generate_wordcloud(text):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    st.pyplot(plt)

def main():
    # Enhanced sidebar
    with st.sidebar:
        st.title("PDF Analysis and Comparison Tool")
        st.write("""
        **Comprehensive PDF Text Analysis:**
        
        ► **Core Features**
        - Full text extraction
        - Word frequency analysis
        - Readability scoring
        - Question detection
        - Visualizations
        
        ► **Comparison Tools**
        - Side-by-side metrics
        - Comparative word clouds
        - Delta differences
        
        *Supports digital PDFs with selectable text*
        """)

    st.title("PDF Analysis and Comparison Tool")
    st.subheader("Extract Insights and Compare Documents")
    st.warning("Note: Only digital PDFs with selectable text are supported.")

    option = st.radio("Select mode:", ("Single Document Analysis", "Compare Two Documents"), 
                    horizontal=True,
                    help="Choose between analyzing one file or comparing two")

    if option == "Single Document Analysis":
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

        if uploaded_file is not None:
            if uploaded_file.type != "application/pdf":
                st.error("Please upload a valid PDF file.")
                return
                
            text = extract_text_from_pdf(uploaded_file)
            if text is None:
                st.error("Failed to extract text. Please upload a digital PDF with selectable text.")
                return

            analytics = analyze_pdf(text)

            st.subheader("Document Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Word Count", analytics['Word Count'])
                st.metric("Character Count", analytics['Character Count'])
            with col2:
                st.metric("Sentence Count", analytics['Sentence Count'])
                st.metric("Line Count", analytics['Line Count'])
            with col3:
                st.metric("Questions", analytics['Question Count'])
                st.metric("Readability Score", f"{analytics['Readability Score']:.2f}")

            st.subheader("Most Frequent Words")
            common_words_df = pd.DataFrame(analytics['Most Common Words'], columns=["Word", "Count"])
            st.bar_chart(common_words_df.set_index("Word", drop=True))

            st.subheader("Word Cloud")
            with st.expander("About Word Clouds"):
                st.write("""
                Word clouds visually represent word frequency - larger words appear more often in the document.
                This helps quickly identify main themes and topics.
                """)
            generate_wordcloud(text)

            with st.expander("View Extracted Text"):
                st.text_area("Text", text, height=300, label_visibility="collapsed")

    else:  # Enhanced comparison section
        st.info("💡 Pro Tip: Compare contracts, research papers, or document versions")
        
        col1, col2 = st.columns(2)
        with col1:
            uploaded_file1 = st.file_uploader("Primary PDF", type="pdf", key="file1",
                                            help="Base document for comparison")
        with col2:
            uploaded_file2 = st.file_uploader("Comparison PDF", type="pdf", key="file2",
                                            help="Document to compare against")

        if uploaded_file1 and uploaded_file2:
            text1 = extract_text_from_pdf(uploaded_file1)
            text2 = extract_text_from_pdf(uploaded_file2)
            
            if text1 is None or text2 is None:
                st.error("One or both files couldn't be processed. Please check they are digital PDFs.")
                return

            analytics1 = analyze_pdf(text1)
            analytics2 = analyze_pdf(text2)

            # Enhanced visualization section
            st.subheader("Visual Comparison")
            
            tab1, tab2, tab3 = st.tabs(["Metrics Comparison", "Word Clouds", "Common Words"])
            
            with tab1:
                st.subheader("Comparison Results")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**{uploaded_file1.name}**")
                    st.metric("Word Count", analytics1['Word Count'], 
                             delta=analytics1['Word Count'] - analytics2['Word Count'])
                    st.metric("Readability", f"{analytics1['Readability Score']:.2f}", 
                             delta=round(analytics1['Readability Score'] - analytics2['Readability Score'], 2))

                with col2:
                    st.markdown(f"**{uploaded_file2.name}**")
                    st.metric("Word Count", analytics2['Word Count'], 
                             delta=analytics2['Word Count'] - analytics1['Word Count'])
                    st.metric("Readability", f"{analytics2['Readability Score']:.2f}", 
                             delta=round(analytics2['Readability Score'] - analytics1['Readability Score'], 2))

                st.subheader("Detailed Comparison")
                comparison_df = pd.DataFrame({
                    "Metric": ["Word Count", "Character Count", "Sentence Count", "Line Count", "Question Count", "Readability"],
                    "File 1": [
                        analytics1['Word Count'],
                        analytics1['Character Count'],
                        analytics1['Sentence Count'],
                        analytics1['Line Count'],
                        analytics1['Question Count'],
                        f"{analytics1['Readability Score']:.2f}",
                    ],
                    "File 2": [
                        analytics2['Word Count'],
                        analytics2['Character Count'],
                        analytics2['Sentence Count'],
                        analytics2['Line Count'],
                        analytics2['Question Count'],
                        f"{analytics2['Readability Score']:.2f}",
                    ]
                }).set_index("Metric")
                
                st.dataframe(comparison_df, use_container_width=True)
                
            with tab2:
                st.write("**Word Frequency Visualization**")
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"**{uploaded_file1.name}**")
                    generate_wordcloud(text1)
                with col2:
                    st.caption(f"**{uploaded_file2.name}**")
                    generate_wordcloud(text2)
                    
            with tab3:
                st.write("**Shared Vocabulary Analysis**")
                words1 = set(re.findall(r'\b\w+\b', text1.lower()))
                words2 = set(re.findall(r'\b\w+\b', text2.lower()))
                common_words = words1.intersection(words2)
                
                st.metric("Shared Unique Words", len(common_words),
                         help="Count of words appearing in both documents")
                
                if common_words:
                    common_df = pd.DataFrame(sorted(common_words), columns=["Shared Words"])
                    st.dataframe(common_df, height=300, hide_index=True)

if __name__ == "__main__":
    main()