import streamlit as st
import os
import base64
import openai

# Configurazione della chiave API di OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key)

# Configura la pagina con un layout ampio per una migliore visualizzazione
st.set_page_config(layout="wide")

# Titolo principale della pagina
st.title("Pagina di Correzione")

# Creazione di due colonne di uguale dimensione per visualizzare i file PDF e i codici studenti
col1, col2 = st.columns(2)

# Funzione per eliminare un file dallo stato della sessione
def elimina_file(file_key):
    if file_key in st.session_state:
        del st.session_state[file_key]
        st.success(f"File '{file_key.replace('_', ' ')}' eliminato con successo!")
        st.rerun()

# Funzione per eliminare la cartella caricata
def elimina_cartella():
    if "cartella_codici" in st.session_state:
        del st.session_state["cartella_codici"]
        st.success("Cartella dei codici studenti eliminata con successo!")
        st.rerun()

# Funzione per mostrare un'anteprima del PDF
def mostra_pdf(file):
    if file is not None:
        base64_pdf = base64.b64encode(file.getvalue()).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

# Funzione per chiamare la LLM di OpenAI
def correggi_codice(codice, criteri):
    prompt = f"""
    Sei un assistente esperto nella correzione di codice C. 
    Correggi il seguente codice applicando questi criteri di correzione:

    Criteri:
    {criteri}

    Codice dello studente:
    {codice}

    Restituisci solo il codice corretto con eventuali commenti sulle correzioni effettuate.
    """
    try:
        risposta = client.chat.completions.create(
            model="gpt-3.5",
            messages=[
                {"role": "system", "content": "Sei un esperto di programmazione in C."},
                {"role": "user", "content": prompt}
            ]
        )
        return risposta.choices[0].message.content
    except openai.OpenAIError as e:
        return f"Errore di OpenAI: {e}"
    except Exception as e:
        return f"Errore generico: {e}"

# Sezione per la visualizzazione dei Codici Studenti
with col1:
    st.header("Codici Studenti")
    if "cartella_codici" in st.session_state and st.session_state["cartella_codici"]:
        cartella = st.session_state["cartella_codici"]
        st.write(f"\U0001F4C1 **Cartella caricata:** {cartella}")

        if not os.path.exists(cartella) or not os.listdir(cartella):
            st.warning("La cartella caricata non contiene file validi.")
        else:
            sottocartelle = [d for d in os.listdir(cartella) if os.path.isdir(os.path.join(cartella, d))]
            
            if sottocartelle:
                sottocartella_scelta = st.selectbox("Seleziona uno studente:", sottocartelle)
                percorso_cartella_scelta = os.path.join(cartella, sottocartella_scelta)
                
                file_c = None
                for file in os.listdir(percorso_cartella_scelta):
                    if file.endswith(".c"):
                        file_c = file
                        break
                
                if file_c:
                    percorso_file = os.path.join(percorso_cartella_scelta, file_c)
                    with open(percorso_file, "r") as codice_file:
                        codice = codice_file.read()
                    st.text_area(f"Contenuto di {file_c}", codice, height=200)
                    
                    cognome_nome = sottocartella_scelta.replace(" ", "_")
                    nome_file_salvato = f"{cognome_nome}_{os.path.basename(cartella)}.c"
                    st.download_button("Salva codice", codice, file_name=nome_file_salvato, mime="text/plain")
                else:
                    st.warning("Nessun file .c trovato nella cartella selezionata.")
            else:
                st.warning("Nessuna sottocartella trovata nella cartella principale.")
    else:
        st.warning("Nessuna cartella caricata per i codici studenti.")
    
    if "cartella_codici" in st.session_state and st.session_state["cartella_codici"]:
        if st.button("Elimina Cartella Codici Studenti"):
            elimina_cartella()

    testo = None
    if "criteri_correzione" in st.session_state and st.session_state["criteri_correzione"]:
        file = st.session_state["criteri_correzione"]
        testo = file.getvalue().decode("utf-8")

    if "cartella_codici" in st.session_state and testo:
        if sottocartella_scelta and file_c:
            if st.button("Correggi"):
                codice_corretto = correggi_codice(codice, testo)
                st.text_area("Correzione dell'IA", codice_corretto, height=300) 


# Sezione per la visualizzazione dei Criteri di Correzione
with col2:
    st.header("Criteri di Correzione (.txt)")
    if "criteri_correzione" in st.session_state and st.session_state["criteri_correzione"]:
        file = st.session_state["criteri_correzione"]
        st.write(f"📄 **File caricato:** {file.name}")

        # Visualizza il contenuto del file .txt
        testo = file.getvalue().decode("utf-8")
        st.text_area("Contenuto dei Criteri di Correzione", testo, height=300)

        # Pulsanti per scaricare ed eliminare il file
        st.download_button("Salva Criteri di Correzione", file.getvalue(), file_name=file.name, mime="text/plain")
        if st.button("Elimina Criteri di Correzione"):
            elimina_file("criteri_correzione")
    else:
        st.warning("Nessun file caricato per i criteri di correzione.")

# Linea di separazione tra le sezioni
st.divider()

# Creazione di una colonna centrale per il Testo d'Esame
spazio_vuoto, col3, spazio_vuoto2 = st.columns([0.5, 1, 0.5])

# Sezione per la visualizzazione del Testo d'Esame
with col3:
    st.header("Testo d'Esame")
    if "testo_esame" in st.session_state and st.session_state["testo_esame"]:
        file = st.session_state["testo_esame"]
        st.write(f"📄 **File caricato:** {file.name}")

        # Visualizza il contenuto del file in base al tipo
        if file.name.endswith(".pdf"):
            mostra_pdf(file)
        else:
            testo = file.getvalue().decode("utf-8")
            st.text_area("Contenuto del Testo d'Esame", testo, height=300)

        # Pulsanti per scaricare ed eliminare il file
        if file.name.endswith(".pdf"):
            st.download_button("Salva Testo d'Esame", file.getvalue(), file_name=file.name, mime="application/pdf")
        else:
            st.download_button("Salva Testo d'Esame", file.getvalue(), file_name=file.name, mime="text/plain")
        if st.button("Elimina Testo d'Esame"):
            elimina_file("testo_esame")
    else:
        st.warning("Nessun file caricato per il testo d'esame.")

# Aggiunge più spazio vuoto per spingere il bottone verso il basso
for _ in range(10):
    st.write("")

# Creazione di colonne per centrare il pulsante
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    if st.button("Torna alla pagina di caricamento materiali", use_container_width=True):
        st.switch_page("caricamento.py")

# Aggiunge ancora più spazio sotto il pulsante
for _ in range(5):
    st.write("")
