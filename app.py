import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from htmlTemplates import css, bot_template, user_template
import requests
import io
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.chrome import service as fs



st.set_page_config(
    page_title='Mie AI',
    page_icon="🤖",
    layout="wide",
)


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1024,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def get_conversation_chain(vectorstore):
    system_template = """du er en ekspert innenfor eiendomsmeglerbransjen, utrustet med en dyp forståelse av alle begreper, og praksis relatert til eiendomshandel. Du kan tolke og forstå ethvert eiendomsrelatert dokument og gi innsikt basert på det. Brukere kan laste opp dokumenter relatert til eiendom, og din oppgave er å analysere disse dokumentene, gjenkjenne viktig informasjon, og gi svar på spørsmål som berører innholdet i disse dokumentene. Husk, din kunnskap dekker hele spekteret av eiendomsmegling, fra kontraktsforhandlinger til boligvurderinger og juridiske formaliteter. Gjør ditt beste for å gi presise, klare, og informative svar basert på dokumentene som presenteres for deg.\n\nSom en eiendomsmegler må du kunne tolke og analysere en rekke dokumenter, fra eiendomskontrakter og skjøter til vurderingsrapporter og finansieringsavtaler. Din rolle som ekspert innenfor dette området innebærer å forstå alle de ulike terminologiene, begrepene og praksisene som er involvert i eiendomstransaksjoner. Du må også ha en dyp forståelse av juridiske og økonomiske aspekter ved eiendomsmegling.\n\nNår du mottar dokumentene fra brukerne, bør du først lese gjennom dem nøye og sørge for at du forstår innholdet og implikasjonene. Deretter kan du begynne å analysere dokumentene for å gjenkjenne viktig informasjon. Dette kan inkludere informasjon om eiendommens størrelse, beliggenhet, historikk, eventuelle pågående konflikter eller juridiske problemer, og ikke minst verdien av eiendommen.\n\nNegative sapekter/info om boligen så finner du ofte under Tg1, Tg2 og Tg3. men ord som slitt, bør gjøres noe med, gammelt og bør utbedres og også under noe negativt om boligen.\n\nsvar kort og konsist! \n\nQ: Jeg skal se på en bolig der badet er gammelt men det er lagt flis på flis hva bør jeg være obs på da ? \nA: Det er viktig å sjekke om flisene er lagt på en riktig måte, og om det er eventuelle lekkasjer eller fuktskader under de gamle flisene. Det kan også være lurt å sjekke om det er gjort riktige tilpasninger ved rør og sluk.
    ----------------
    {context}"""

    messages = [
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template("{question}")
    ]
    qa_prompt = ChatPromptTemplate.from_messages(messages)

    #llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0.8)
    llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0.8, openai_api_key=st.secrets["OPENAI_API_KEY"])


    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)

    combine_docs_chain_kwargs = {
        "prompt": qa_prompt
    }

    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory,
        combine_docs_chain_kwargs=combine_docs_chain_kwargs
    )

    return conversation_chain

def handle_userinput(user_question):
    if st.session_state.conversation is not None:
        try:
            response = st.session_state.conversation({'question': user_question})
            st.session_state.chat_history = response['chat_history']
            reversed_chat_history = list(reversed(st.session_state.chat_history))
            for i, message in enumerate(reversed_chat_history):
                if i % 2 != 0:
                    st.write(user_template.replace(
                        "{{MSG}}", message.content), unsafe_allow_html=True)
                else:
                    st.write(bot_template.replace(
                        "{{MSG}}", message.content), unsafe_allow_html=True)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please upload a PDF before asking questions.")


def get_pdf_url(url):  
    options = webdriver.ChromeOptions()
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
    options.add_argument('--user-agent=' + ua)
    options.add_argument("--headless")
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    chrome_service = fs.Service(executable_path=ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())

    driver = webdriver.Chrome(options=options,service=chrome_service)
    
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 30)
        button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.max-w-full.w-full.button.button--primary')))
        driver.execute_script("arguments[0].click();", button)  # JavaScript click
        
        # Wait for the next page to load
        driver.implicitly_wait(30)
        
        # Get the current URL after the button click
        current_url = driver.current_url
        
        if 'eie.' in current_url:
            try:
                pdf_link_element_selector = 'a.link.clickEvent[href^="https://api.eie.no/files/v2/pdf/"]'
                pdf_link_element = driver.find_element(By.CSS_SELECTOR, pdf_link_element_selector)
                pdf_url = pdf_link_element.get_attribute('href')  # Get the PDF URL
                return pdf_url  # Return the PDF URL for EIE
            except Exception as e:
                print(f"Exception for EIE: {e}")
                pass  # If this attempt fails, it will print the exception and continue
        elif 'dnb' in current_url:
            pdf_link_element_selector = 'a.dnb-button.dnb-button--primary.dnb-button--has-text.dnb-space__left--small.theme-dark__button__secondary.dnb-anchor--has-icon.dnb-a'
        elif 'krogsveen' in current_url:
            pdf_link_element_selector = 'a.css-urve0f'
        elif 'notar' in current_url:
            pdf_link_element_selector = 'a.btn.btn-normal[href^="/upload_images/prospekt_pdf"]'

        else:
            return None  # Return None if the URL does not match any of the above conditions

        pdf_link_element = driver.find_element(By.CSS_SELECTOR, pdf_link_element_selector)
        if pdf_link_element:
            return pdf_link_element.get_attribute('href')
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        driver.quit()

def get_pdf_text_from_url(pdf_url):
    response = requests.get(pdf_url)
    if response.status_code == 200:
        pdf_content = response.content
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        text = ""
        for page in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page].extract_text()
        return text
    else:
        return None


row1_col1, row1_col2, row1_col3 , row1_col4, row1_col5 = st.columns([0.95,2,1,1.5,5.5])
row2_col1, row2_col2 = st.columns([4,7])

gif = """
        <div style="display: flex; justify-content: center;">
            <img src="https://raw.githubusercontent.com/MouadhBelgaied/Chatbot/main/sleeping.gif" alt="sleeping.gif" style="width: 500px; height: 500px;">
        </div>
        """

#load_dotenv()
st.write(css, unsafe_allow_html=True)

if "conversation" not in st.session_state:
    st.session_state.conversation = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = None

if "pdf_link" not in st.session_state:
    st.session_state.pdf_link = None


with row2_col2:
    user_question = st.text_input("Still et spørsmål om dokumentet ditt:")
    if user_question:
        with st.expander("Samtalehistorikk", expanded=True):
            handle_userinput(user_question)
        gif ="""
                <div style="display: flex; justify-content: center;">
                    <img src="https://raw.githubusercontent.com/MouadhBelgaied/Chatbot/main//glad.gif" alt="glad.gif" style="width: 500px; height: 500px;">
                </div>
                """


with row1_col4:
    options = ["Finn-link", "Last opp PDF"]
    selected_option = st.selectbox("⚙️ Opplastingsalternativ:", options)

with row1_col5:
    if selected_option == "Last opp PDF":
        pdf_docs = st.file_uploader(
                "Last opp PDF-filer her og klikk på Behandle:", accept_multiple_files=True)

        if pdf_docs and not user_question:
            gif = """
                            <div style="display: flex; justify-content: center;">
                                <img src="https://raw.githubusercontent.com/MouadhBelgaied/Chatbot/main//welcoming.gif" alt="welcoming.gif" style="width: 500px; height: 500px;">
                            </div>
                            """

        if st.button("Upload"):
            with st.spinner("Behandling..."):
                gif = """
                        <div style="display: flex; justify-content: center;">
                            <img src="https://raw.githubusercontent.com/MouadhBelgaied/Chatbot/main//reading.gif" alt="reading.gif" style="width: 500px; height: 500px;">
                        </div>
                        """

                if pdf_docs:
                    try:
                        # get pdf text
                        raw_text = get_pdf_text(pdf_docs)

                        # get the text chunks
                        text_chunks = get_text_chunks(raw_text)

                        # create vector store
                        vectorstore = get_vectorstore(text_chunks)

                        # create conversation chain
                        st.session_state.conversation = get_conversation_chain(vectorstore)

                        st.success("Opplastet og behandlet vellykket!")

                        gif ="""
                                <div style="display: flex; justify-content: center;">
                                    <img src="https://raw.githubusercontent.com/MouadhBelgaied/Chatbot/main//glad.gif" alt="glad.gif" style="width: 500px; height: 500px;">
                                </div>
                                """
                    except Exception as e:
                        gif = """
                            <div style="display: flex; justify-content: center;">
                                <img src="https://raw.githubusercontent.com/MouadhBelgaied/Chatbot/main//crying.gif" alt="crying.gif" style="width: 500px; height: 500px;">
                            </div>
                            """
                        st.error(f"Det oppstod en feil under behandling av PDF-filer: {str(e)}")
                else:
                    gif = """
                            <div style="display: flex; justify-content: center;">
                                <img src="https://raw.githubusercontent.com/MouadhBelgaied/Chatbot/main//crying.gif" alt="crying.gif" style="width: 500px; height: 500px;">
                            </div>
                            """
                    st.warning("Vennligst last opp én eller flere PDF-er før du klikker på Behandle.")
    else:
        url = st.text_input("Skriv inn nettstedets URL og klikk på Hent PDF:")
        if st.button("Search"):
            if url:
                with st.spinner("Behandling..."):
                    gif = """
                        <div style="display: flex; justify-content: center;">
                            <img src="https://raw.githubusercontent.com/MouadhBelgaied/Chatbot/main//reading.gif" alt="reading.gif" style="width: 500px; height: 500px;">
                        </div>
                        """
                    pdf_link = get_pdf_url(url)
                    st.session_state.pdf_link = pdf_link
                    if pdf_link:
                        
                        gif ="""
                                        <div style="display: flex; justify-content: center;">
                                            <img src="https://raw.githubusercontent.com/MouadhBelgaied/Chatbot/main//glad.gif" alt="glad.gif" style="width: 500px; height: 500px;">
                                        </div>
                                        """
                        pdf_text = get_pdf_text_from_url(pdf_link)
                        if pdf_text is not None:
                            try:
                                # get the text chunks
                                text_chunks = get_text_chunks(pdf_text)

                                # create vector store
                                vectorstore = get_vectorstore(text_chunks)

                                # create conversation chain
                                st.session_state.conversation = get_conversation_chain(vectorstore)
                                
                                st.success("Lastet opp og behandlet vellykket!")

                                gif ="""
                                        <div style="display: flex; justify-content: center;">
                                            <img src="https://raw.githubusercontent.com/MouadhBelgaied/Chatbot/main//glad.gif" alt="glad.gif" style="width: 500px; height: 500px;">
                                        </div>
                                        """
                            except Exception as e:

                                gif = """
                                    <div style="display: flex; justify-content: center;">
                                        <img src="https://raw.githubusercontent.com/MouadhBelgaied/Chatbot/main//crying.gif" alt="crying.gif" style="width: 500px; height: 500px;">
                                    </div>
                                    """
                                st.error(f"Det oppstod en feil under behandling av PDF-filer: {str(e)}")
                        else:

                            gif = """
                                    <div style="display: flex; justify-content: center;">
                                        <img src="https://raw.githubusercontent.com/MouadhBelgaied/Chatbot/main//crying.gif" alt="crying.gif" style="width: 500px; height: 500px;">
                                    </div>
                                    """
                            st.error("Kunne ikke hente PDF fra nettadressen.")
                    else:
                        gif = """
                                    <div style="display: flex; justify-content: center;">
                                        <img src="https://raw.githubusercontent.com/MouadhBelgaied/Chatbot/main//crying.gif" alt="crying.gif" style="width: 500px; height: 500px;">
                                    </div>
                                    """
                        st.error("PDF-lenke ikke funnet.")
            else:
                gif = """
                                <div style="display: flex; justify-content: center;">
                                    <img src="https://raw.githubusercontent.com/MouadhBelgaied/Chatbot/main//crying.gif" alt="crying.gif" style="width: 500px; height: 500px;">
                                </div>
                                """
                st.warning("Vennligst skriv inn lenken før du klikker på Upload.")
        
    
with row1_col2:
    pdf_link = st.session_state.pdf_link
    if pdf_link:      
        st.markdown(f"""
        <a href="{pdf_link}" target="_self">
            <div style="display: flex;
                        justify-content: center;
                        align-items: center;
                        width: 100%;
                        height: 100%;
                        padding: 0.5em 1em;
                        color: #FFFFFF;
                        background-color: #00A36C;
                        border-radius: 3px;
                        text-decoration: none;
                        cursor: pointer;
                        border: none;
                        font-size: 1rem;
                        outline: none;">
                Se salgsoppgave
            </div>
        </a>
        """,
        unsafe_allow_html=True
        )
        st.success("PDF-lenken er klar!")
    else:
        st.markdown(f"""
        <div style="display: flex;
                    justify-content: center;
                    align-items: center;
                    width: 100%;
                    height: 100%;
                    padding: 0.5em 1em;
                    color: #FFFFFF;
                    border-radius: 3px;
                    text-decoration: none;
                    background-color: #00A36C;
                    cursor: pointer;
                    border: none;
                    font-size: 1rem;
                    outline: none;">
            Se salgsoppgave
        </div>
        """,
        unsafe_allow_html=True
        )


with row2_col1:
    st.write(gif, unsafe_allow_html=True)


