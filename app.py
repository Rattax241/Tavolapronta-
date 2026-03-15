import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq

st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

def genera_proiezione_ortogonale(lista_dati, premium=False):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect('equal')
    ax.axis('off')
    
    limit = 55
    ax.plot([-limit, limit], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-limit, limit], color='black', linewidth=1)
    ax.text(-limit+2, 2, "P.V.", fontsize=12, fontweight='bold', color='gray')
    ax.text(-limit+2, -4, "P.O.", fontsize=12, fontweight='bold', color='gray')
    ax.text(2, limit-4, "P.L.", fontsize=12, fontweight='bold', color='gray')
    
    for dati in lista_dati:
        tipo = dati.get('tipo', 'solido').lower()
        L, P, H = dati.get('lunghezza', 6), dati.get('profondita', 6), dati.get('altezza', 10)
        dPV, dPL = dati.get('dist_pv', 5), dati.get('dist_pl', 5)
        lati, rot = dati.get('lati', 4), dati.get('rotazione', 0)
        aux = dati.get('piano_ausiliario', False)
        
        angle = np.radians(rot)
        x_c, y_c = -dPL - L/2, -dPV - P/2
        offset = np.pi/4 if lati == 4 and rot == 0 else 0
        
        theta = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset
        vx, vy = x_c + (L/2) * np.cos(theta), y_c + (P/2) * np.sin(theta)
        punti_po = np.column_stack([vx, vy])
        punti_chiusi = np.vstack([punti_po, punti_po[0]])

        # 1. P.O.
        ax.plot(punti_chiusi[:, 0], punti_chiusi[:, 1], color='black', linewidth=2)
        if 'pir' in tipo or 'con' in tipo:
            for p in punti_po: ax.plot([x_c, p[0]], [y_c, p[1]], color='black', linewidth=0.8)

        if premium:
            x_min, x_max = np.min(vx), np.max(vx)
            y_min, y_max = np.min(vy), np.max(vy)
            
            # 2. P.V. e P.L.
            if 'pir' in tipo or 'con' in tipo:
                ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color='black', linewidth=2)
            else:
                ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color='black', linewidth=2)
            
            # Archi di ribaltamento PL
            t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
            for ry in [y_min, y_max, y_c]:
                r = abs(ry)
                ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='orange', linestyle='--', linewidth=0.6)

            # 3. PIANO AUSILIARIO (Solo se richiesto)
            if aux:
                angle_aux = np.radians(30) # Inclinazione piano ausiliario
                l_aux_x = np.array([20, 50])
                l_aux_y = np.array([10, 30])
                ax.plot(l_aux_x, l_aux_y, color='purple', linewidth=1.5, linestyle='-.')
                ax.text(35, 25, "P.A.", color='purple', fontweight='bold')
                # Proiezione punti su PA
                for px, py in zip(vx, vy):
                    ax.plot([px, px+15], [py, py+15], color='purple', linestyle=':', linewidth=0.5, alpha=0.5)

    if not premium:
        ax.text(0, 30, "SBLOCCA MASTER PER VISTE AUSILIARIE", color='red', alpha=0.3, fontsize=18, ha='center')
    
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    return fig

# --- UI ---
if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.title("💎 Area Master")
    if not st.session_state.premium:
        st.link_button("Mensile (4,99€)", LINK_MENSILE)
        st.link_button("Lifetime (19,99€)", LINK_LIFETIME)
        code = st.text_input("Codice licenza:", type="password")
        if st.button("Attiva Master"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
    else: st.success("✅ MODALITÀ AVANZATA ATTIVA")

st.title("📐 TavolaPronta AI Master")
traccia = st.text_area("Inserisci la traccia (es. con piano ausiliario):")

if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt = """
            Sei un ingegnere. Restituisci JSON lista 'solidi'.
            REGOLE: Se la traccia menziona 'piano ausiliario' o 'sezione inclinata', imposta 'piano_ausiliario': true.
            JSON: {"solidi": [{"tipo", "lunghezza", "profondita", "altezza", "dist_pv", "dist_pl", "rotazione", "lati", "piano_ausiliario"}]}
            """
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": traccia}],
                response_format={"type": "json_object"}
            )
            lista = json.loads(res.choices[0].message.content).get("solidi", [])
            st.pyplot(genera_proiezione_ortogonale(lista, premium=st.session_state.premium))
        except Exception as e:
            st.error(f"Errore: {e}")
