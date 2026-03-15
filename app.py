import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

# --- COSTANTI E LINK ---
LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

# --- MOTORE GRAFICO PROFESSIONALE ---
def genera_proiezione_ortogonale(dati, premium=False):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Assi principali e scritte piani
    ax.plot([-35, 35], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-35, 35], color='black', linewidth=1)
    ax.text(-32, 1.5, "PIANO VERTICALE (P.V.)", fontsize=10, color='gray', fontweight='bold')
    ax.text(-32, -2.5, "PIANO ORIZZONTALE (P.O.)", fontsize=10, color='gray', fontweight='bold')
    ax.text(2, 32, "PIANO LATERALE (P.L.)", fontsize=10, color='gray', fontweight='bold')
    
    # Estrazione parametri IA
    tipo = dati.get('tipo', 'solido').lower()
    L = dati.get('lunghezza', 6)
    P = dati.get('profondita', 5)
    H = dati.get('altezza', 10)
    dPV = dati.get('dist_pv', 2)
    dPL = dati.get('dist_pl', 3)
    rot = dati.get('rotazione', 0)
    lati = dati.get('lati', 4)

    # 1. DISEGNO P.O. (Sempre Visibile)
    x_c, y_c = -dPL - L/2, -dPV - P/2
    angle = np.radians(rot)
    
    # Generazione punti per poligoni regolari
    theta = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle
    vx = x_c + (L/2) * np.cos(theta)
    vy = y_c + (P/2) * np.sin(theta)
    punti_po = np.column_stack([vx, vy])
    punti_chiusi = np.vstack([punti_po, punti_po[0]])

    ax.plot(punti_chiusi[:, 0], punti_chiusi[:, 1], color='black', linewidth=2.5)
    
    # Spigoli della piramide (visti dall'alto)
    if 'piramide' in tipo or 'cono' in tipo:
        for p in punti_po:
            ax.plot([x_c, p[0]], [y_c, p[1]], color='black', linewidth=1)

    # 2. LOGICA PREMIUM (P.V. e P.L. con Archi)
    if premium:
        x_min, x_max = np.min(vx), np.max(vx)
        y_min, y_max = np.min(vy), np.max(vy)

        # Disegno P.V.
        if 'piramide' in tipo or 'cono' in tipo:
            ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color='black', linewidth=2.5)
        else:
            ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color='black', linewidth=2.5)
        
        # Linee di richiamo P.O. -> P.V.
        for px in [x_min, x_max, x_c]:
            ax.plot([px, px], [y_max, H if px==x_c and ('pir' in tipo or 'con' in tipo) else 0], color='gray', linestyle=':', linewidth=0.7)

        # P.L. con Archi di ribaltamento
        t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
        punti_y = [y_min, y_max, y_c] if ('pir' in tipo or 'con' in tipo) else [y_min, y_max]
        for ry in punti_y:
            r = abs(ry)
            ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='orange', linestyle='--', linewidth=0.8)
            ax.plot([r, r], [0, H if ry==y_c and ('pir' in tipo or 'con' in tipo) else 0], color='gray', linestyle=':', linewidth=0.7)
            ax.plot([ry, 0], [ry, ry], color='gray', linestyle=':', linewidth=0.7)

        # Disegno P.L. Finale
        z_min, z_max, z_c = abs(y_max), abs(y_min), abs(y_c)
        if 'piramide' in tipo or 'cono' in tipo:
            ax.plot([z_min, z_max, z_c, z_min], [0, 0, H, 0], color='black', linewidth=2.5)
        else:
            ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color='black', linewidth=2.5)
    else:
        # Overlay bloccato
        ax.text(15, 15, "CONTENUTO PREMIUM\nSblocca P.L.", color='red', alpha=0.3, fontsize=18, ha='center', va='center', rotation=45)
        ax.text(-15, 15, "CONTENUTO PREMIUM\nSblocca P.V.", color='red', alpha=0.3, fontsize=18, ha='center', va='center', rotation=45)

    return fig

# --- UI APP ---
if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.title("💎 Area Master")
    if not st.session_state.premium:
        st.info("Attualmente visualizzi solo il P.O. (Piano Orizzontale).")
        st.link_button("Abbonamento Mensile (4,99€)", LINK_MENSILE)
        st.link_button("Accesso Illimitato (19,99€)", LINK_LIFETIME)
        st.divider()
        code = st.text_input("Codice attivazione ricevuto:", type="password")
        if st.button("Attiva Funzioni Master"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
            else: st.error("Codice non valido.")
    else:
        st.success("✅ MODALITÀ MASTER ATTIVA")
        if st.button("Logout Licenza"):
            st.session_state.premium = False
            st.rerun()

st.title("📐 TavolaPronta AI Pro")
st.markdown("Genera proiezioni ortogonali perfette partendo dalla traccia del tuo libro.")
traccia = st.text_area("Cosa devi disegnare? (Es: Piramide esagonale raggio 5 altezza 12)")

if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        try:
            with st.spinner("L'IA sta elaborando la geometria..."):
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                
                # PROMPT POTENZIATO PER FORME GEOMETRICHE
                prompt_sistema = """
                Sei un ingegnere esperto. Analizza la traccia e rispondi SOLO in JSON.
                REGOLE LATI: Esagono=6, Pentagono=5, Quadrato/Rettangolo/Parallelepipedo=4, Triangolo=3.
                Se Cilindro/Cono metti lati=100.
                JSON: {tipo, lunghezza, profondita, altezza, dist_pv, dist_pl, rotazione, lati}
                """
                
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": traccia}],
                    response_format={"type": "json_object"}
                )
                dati = json.loads(res.choices[0].message.content)
                
                st.pyplot(genera_proiezione_ortogonale(dati, premium=st.session_state.premium))
                
                if not st.session_state.premium:
                    st.error("🔒 Sblocca la versione Premium per vedere P.V., P.L. e tutti i passaggi tecnici (archi e proiezioni).")
        except:
            st.error("Errore di configurazione API.")
