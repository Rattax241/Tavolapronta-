import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

# --- MOTORE GRAFICO MULTI-SOLIDO ---
def genera_proiezione_ortogonale(lista_dati, premium=False):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Assi e Etichette Piani
    ax.plot([-45, 45], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-45, 45], color='black', linewidth=1)
    ax.text(-42, 1.5, "PIANO VERTICALE (P.V.)", fontsize=10, fontweight='bold', color='gray')
    ax.text(-42, -3, "PIANO ORIZZONTALE (P.O.)", fontsize=10, fontweight='bold', color='gray')
    ax.text(2, 42, "PIANO LATERALE (P.L.)", fontsize=10, fontweight='bold', color='gray')
    
    for dati in lista_dati:
        tipo = dati.get('tipo', 'solido').lower()
        L, P, H = dati.get('lunghezza', 6), dati.get('profondita', 5), dati.get('altezza', 10)
        dPV, dPL = dati.get('dist_pv', 2), dati.get('dist_pl', 3)
        lati = dati.get('lati', 4)
        rot = dati.get('rotazione', 0)
        
        angle = np.radians(rot)
        x_c, y_c = -dPL - L/2, -dPV - P/2
        
        # Raddrizzamento automatico per quadrati/rettangoli se rotazione è 0
        offset = np.pi/4 if lati == 4 and rot == 0 else 0
        
        theta = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset
        vx, vy = x_c + (L/2) * np.cos(theta), y_c + (P/2) * np.sin(theta)
        punti_po = np.column_stack([vx, vy])
        punti_chiusi = np.vstack([punti_po, punti_po[0]])

        # Disegno P.O.
        ax.plot(punti_chiusi[:, 0], punti_chiusi[:, 1], color='black', linewidth=2)
        if 'piramide' in tipo or 'cono' in tipo:
            for p in punti_po: ax.plot([x_c, p[0]], [y_c, p[1]], color='black', linewidth=0.8)

        if premium:
            x_min, x_max = np.min(vx), np.max(vx)
            y_min, y_max = np.min(vy), np.max(vy)
            
            # P.V.
            if 'piramide' in tipo or 'cono' in tipo:
                ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color='black', linewidth=2)
            else:
                ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color='black', linewidth=2)
            
            # Proiezioni Verticali
            for px in [x_min, x_max, x_c]:
                ax.plot([px, px], [y_max, H if px==x_c and ('pir' in tipo or 'con' in tipo) else 0], color='gray', linestyle=':', linewidth=0.5)
            
            # P.L. (Archi e Ribaltamento)
            t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
            punti_y = [y_min, y_max, y_c] if ('pir' in tipo or 'con' in tipo) else [y_min, y_max]
            for ry in punti_y:
                r = abs(ry)
                ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='orange', linestyle='--', linewidth=0.6)
                ax.plot([r, r], [0, H if ry==y_c and ('pir' in tipo or 'con' in tipo) else 0], color='gray', linestyle=':', linewidth=0.5)

            # Disegno P.L.
            z_min, z_max, z_c = abs(y_max), abs(y_min), abs(y_c)
            if 'piramide' in tipo or 'cono' in tipo:
                ax.plot([z_min, z_max, z_c, z_min], [0, 0, H, 0], color='black', linewidth=2)
            else:
                ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color='black', linewidth=2)
    
    if not premium:
        ax.text(20, 20, "VERSIONE MASTER RICHIESTA\nSblocca P.V. e P.L.", color='red', alpha=0.3, fontsize=18, ha='center', va='center', rotation=45)
    
    return fig

# --- UI APP ---
if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.title("💎 Area Premium")
    if not st.session_state.premium:
        st.write("Ottieni la tavola completa con proiezioni e archi di ribaltamento.")
        st.link_button("Abbonamento Mensile (4,99€)", LINK_MENSILE)
        st.link_button("Accesso Illimitato (19,99€)", LINK_LIFETIME)
        st.divider()
        code = st.text_input("Codice attivazione ricevuto:", type="password")
        if st.button("Attiva Funzioni Master"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.success("Modalità Master Attivata!")
                st.rerun()
            else:
                st.error("Codice non valido.")
    else:
        st.success("✅ LICENZA MASTER ATTIVA")
        st.info("Puoi generare tavole complete di tutti i piani.")
        if st.button("Disconnetti Licenza"):
            st.session_state.premium = False
            st.rerun()

# --- MAIN ---
st.title("📐 TavolaPronta AI")
st.markdown("Incolla la traccia del libro e genera la tua tavola di disegno tecnico in pochi secondi.")

traccia = st.text_area("Cosa vuoi disegnare?", placeholder="Esempio: Una piramide esagonale e un cubo affiancati...")

if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt_sistema = """
            Sei un ingegnere esperto. Analizza la traccia e restituisci un JSON con una lista 'solidi'.
            REGOLE: 
            - Esagono=6 lati, Pentagono=5, Quadrato=4, Triangolo=3.
            - Se rotazione non specificata, rotazione=0.
            - Usa distanze diverse per non sovrapporre i solidi.
            JSON: {"solidi": [{"tipo", "lunghezza", "profondita", "altezza", "dist_pv", "dist_pl", "rotazione", "lati"}]}
            """
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": traccia}],
                response_format={"type": "json_object"}
            )
            risultato = json.loads(res.choices[0].message.content)
            lista = risultato.get("solidi", [])
            
            st.pyplot(genera_proiezione_ortogonale(lista, premium=st.session_state.premium))
            
            if not st.session_state.premium:
                st.warning("🔒 Stai visualizzando solo il P.O. Attiva la versione Premium per sbloccare la tavola completa.")
        except:
            st.error("Errore nell'analisi della traccia. Riprova con più dettagli.")
