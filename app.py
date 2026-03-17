import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(page_title="TavolaPronta AI Master Multi-Solido", layout="wide", page_icon="📐")

# --- COSTANTI E LINK ---
LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

# --- MOTORE GRAFICO MULTI-SOLIDO ---
def genera_proiezione_ortogonale(lista_dati, premium=False):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Assi principali e scritte piani
    ax.plot([-35, 35], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-35, 35], color='black', linewidth=1)
    ax.text(-32, 1.5, "PIANO VERTICALE (P.V.)", fontsize=10, color='gray', fontweight='bold')
    ax.text(-32, -2.5, "PIANO ORIZZONTALE (P.O.)", fontsize=10, color='gray', fontweight='bold')
    ax.text(2, 32, "PIANO LATERALE (P.L.)", fontsize=10, color='gray', fontweight='bold')
    
    for dati in lista_dati:
        tipo = dati.get('tipo', 'solido').lower()
        L = dati.get('lunghezza', 6)
        P = dati.get('profondita', 5)
        H = dati.get('altezza', 10)
        dPV = dati.get('dist_pv', 2)
        dPL = dati.get('dist_pl', 3)
        rot = dati.get('rotazione', 0)
        lati = dati.get('lati', 4)

        # 1. DISEGNO P.O.
        x_c, y_c = -dPL - L/2, -dPV - P/2
        angle = np.radians(rot)
        theta = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle
        vx, vy = x_c + (L/2) * np.cos(theta), y_c + (P/2) * np.sin(theta)
        punti_po = np.column_stack([vx, vy])
        punti_chiusi = np.vstack([punti_po, punti_po[0]])
        ax.plot(punti_chiusi[:, 0], punti_chiusi[:, 1], color='black', linewidth=2)
        
        if 'piramide' in tipo or 'cono' in tipo:
            for p in punti_po: ax.plot([x_c, p[0]], [y_c, p[1]], color='black', linewidth=0.8)

        # 2. LOGICA PREMIUM
        if premium:
            x_min, x_max = np.min(vx), np.max(vx)
            y_min, y_max = np.min(vy), np.max(vy)
            # P.V.
            if 'piramide' in tipo or 'cono' in tipo:
                ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color='black', linewidth=2)
            else:
                ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color='black', linewidth=2)
            # Proiezioni
            for px in [x_min, x_max, x_c]:
                ax.plot([px, px], [y_max, H if px==x_c and ('pir' in tipo or 'con' in tipo) else 0], color='gray', linestyle=':', linewidth=0.5)
            # P.L. con Archi
            t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
            for ry in [y_min, y_max, y_c]:
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
        ax.text(15, 15, "VERSIONE MASTER RICHIESTA\nSblocca P.V. e P.L.", color='red', alpha=0.3, fontsize=18, ha='center', va='center', rotation=45)
    return fig

# --- UI APP ---
if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.title("💎 Area Master")
    if not st.session_state.premium:
        st.link_button("Abbonamento Mensile (4,99€)", LINK_MENSILE)
        st.link_button("Accesso Illimitato (19,99€)", LINK_LIFETIME)
        code = st.text_input("Codice attivazione:", type="password")
        if st.button("Attiva Funzioni Master"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
    else:
        st.success("✅ MODALITÀ MULTI-SOLIDO ATTIVA")

st.title("📐 TavolaPronta AI Master")
traccia = st.text_area("Descrivi l'esercizio (anche con più solidi):", placeholder="Esempio: Una piramide esagonale raggio 5 altezza 12 e un cubo di lato 4 affiancato...")

if st.button("🚀 GENERA TAVOLA COMPLESSA"):
    if traccia:
        try:
            with st.spinner("L'IA sta scomponendo i solidi..."):
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                prompt_sistema = """
                Sei un ingegnere esperto. Analizza la traccia e restituisci una LISTA di oggetti JSON denominata 'solidi'.
                REGOLE LATI: Esagono=6, Pentagono=5, Quadrato=4, Triangolo=3, Cilindro/Cono=100.
                Assicurati che ogni solido abbia coordinate dist_pv e dist_pl diverse se la traccia dice che sono affiancati.
                FORMATO: {"solidi": [{"tipo", "lunghezza", "profondita", "altezza", "dist_pv", "dist_pl", "rotazione", "lati"}]}
                """
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": traccia}],
                    response_format={"type": "json_object"}
                )
                risultato = json.loads(res.choices[0].message.content)
                lista_solidi = risultato.get("solidi", [])
                
                st.pyplot(genera_proiezione_ortogonale(lista_solidi, premium=st.session_state.premium))
                if not st.session_state.premium: st.error("🔒 Sblocca Master per vedere la tavola completa.")
        except:
            st.error("Errore nell'elaborazione dei solidi multipli.")
