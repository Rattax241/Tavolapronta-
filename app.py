import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq

st.set_page_config(page_title="TavolaPronta AI Master Multi-Solido", layout="wide", page_icon="📐")

LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

def genera_proiezione_ortogonale(lista_dati, premium=False):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Assi e Scritte
    ax.plot([-40, 40], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-40, 40], color='black', linewidth=1)
    ax.text(-38, 1.5, "P.V.", fontsize=12, fontweight='bold', color='gray')
    ax.text(-38, -3, "P.O.", fontsize=12, fontweight='bold', color='gray')
    ax.text(2, 38, "P.L.", fontsize=12, fontweight='bold', color='gray')
    
    for dati in lista_dati:
        tipo = dati.get('tipo', 'solido').lower()
        L, P, H = dati.get('lunghezza', 6), dati.get('profondita', 5), dati.get('altezza', 10)
        dPV, dPL = dati.get('dist_pv', 2), dati.get('dist_pl', 3)
        lati = dati.get('lati', 4)
        
        # FORZATURA ROTAZIONE: se non specificata o se è un solido standard, la mettiamo a 0
        rot = dati.get('rotazione', 0)
        if rot is None: rot = 0
        
        angle = np.radians(rot)
        x_c, y_c = -dPL - L/2, -dPV - P/2
        
        # Correzione offset per solidi a 4 lati (per farli stare dritti)
        offset = np.pi/4 if lati == 4 and rot == 0 else 0
        
        theta = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset
        vx, vy = x_c + (L/2) * np.cos(theta), y_c + (P/2) * np.sin(theta)
        punti_po = np.column_stack([vx, vy])
        punti_chiusi = np.vstack([punti_po, punti_po[0]])

        # P.O.
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
                ax.plot([px, px], [y_max, H if px==x_c and ('pir' in tipo or 'con' in tipo) else 0], color='gray', linestyle=':', linewidth=0.6)
            
            # P.L. (Archi)
            t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
            punti_y = [y_min, y_max, y_c] if ('pir' in tipo or 'con' in tipo) else [y_min, y_max]
            for ry in punti_y:
                r = abs(ry)
                ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='orange', linestyle='--', linewidth=0.7)
                ax.plot([r, r], [0, H if ry==y_c and ('pir' in tipo or 'con' in tipo) else 0], color='gray', linestyle=':', linewidth=0.5)

            # Disegno P.L.
            z_min, z_max, z_c = abs(y_max), abs(y_min), abs(y_c)
            if 'piramide' in tipo or 'cono' in tipo:
                ax.plot([z_min, z_max, z_c, z_min], [0, 0, H, 0], color='black', linewidth=2)
            else:
                ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color='black', linewidth=2)
    
    if not premium:
        ax.text(0, 20, "VERSIONE MASTER RICHIESTA", color='red', alpha=0.4, fontsize=20, ha='center', fontweight='bold')
    
    return fig

if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.title("💎 Area Master")
    if not st.session_state.premium:
        st.link_button("Sblocca Tutto", LINK_MENSILE)
        code = st.text_input("Codice:", type="password")
        if st.button("Attiva"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
    else:
        st.success("✅ MODALITÀ ATTIVA")

st.title("📐 TavolaPronta AI")
traccia = st.text_area("Descrivi i solidi (es: piramide esagonale raggio 5 e cubo lato 4 affiancati)")

if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        prompt_sistema = """
        Sei un ingegnere. Analizza la traccia e restituisci un JSON con una lista 'solidi'.
        REGOLE: 
        - Esagono=6 lati, Pentagono=5, Quadrato=4.
        - Se non è scritta una rotazione specifica (es. 'ruotato di 30 gradi'), imposta SEMPRE 'rotazione': 0.
        - Assicura distanze dist_pv e dist_pl diverse per non sovrapporre i solidi.
        JSON: {"solidi": [{"tipo", "lunghezza", "profondita", "altezza", "dist_pv", "dist_pl", "rotazione", "lati"}]}
        """
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": traccia}],
            response_format={"type": "json_object"}
        )
        lista = json.loads(res.choices[0].message.content).get("solidi", [])
        st.pyplot(genera_proiezione_ortogonale(lista, premium=st.session_state.premium))
