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

def genera_proiezione_ortogonale(lista_dati, premium=False):
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Assi e Scritte (Range aumentato per solidi multipli)
    limit = 50
    ax.plot([-limit, limit], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-limit, limit], color='black', linewidth=1)
    ax.text(-limit+2, 2, "P.V.", fontsize=12, fontweight='bold', color='gray')
    ax.text(-limit+2, -4, "P.O.", fontsize=12, fontweight='bold', color='gray')
    ax.text(2, limit-4, "P.L.", fontsize=12, fontweight='bold', color='gray')
    
    if not lista_dati:
        return fig

    for dati in lista_dati:
        tipo = dati.get('tipo', 'solido').lower()
        L = dati.get('lunghezza', 6)
        P = dati.get('profondita', L) # Se manca profondità, usa lunghezza (cubo/esagono)
        H = dati.get('altezza', 10)
        dPV = dati.get('dist_pv', 5)
        dPL = dati.get('dist_pl', 5)
        lati = dati.get('lati', 4)
        rot = dati.get('rotazione', 0)
        
        angle = np.radians(rot)
        x_c, y_c = -dPL - L/2, -dPV - P/2
        
        # Correzione per far stare dritti i quadrati se rot=0
        offset = np.pi/4 if lati == 4 and rot == 0 else 0
        
        theta = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset
        vx = x_c + (L/2) * np.cos(theta)
        vy = y_c + (P/2) * np.sin(theta)
        punti_po = np.column_stack([vx, vy])
        punti_chiusi = np.vstack([punti_po, punti_po[0]])

        # 1. P.O.
        ax.plot(punti_chiusi[:, 0], punti_chiusi[:, 1], color='black', linewidth=2)
        if 'pir' in tipo or 'con' in tipo:
            for p in punti_po: ax.plot([x_c, p[0]], [y_c, p[1]], color='black', linewidth=0.8)

        # 2. PREMIUM: P.V. e P.L.
        if premium:
            x_min, x_max = np.min(vx), np.max(vx)
            y_min, y_max = np.min(vy), np.max(vy)
            
            # P.V.
            if 'pir' in tipo or 'con' in tipo:
                ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color='black', linewidth=2)
            else:
                ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color='black', linewidth=2)
            
            # Linee di richiamo
            for px in [x_min, x_max, x_c]:
                ax.plot([px, px], [y_max, H if px==x_c and ('pir' in tipo or 'con' in tipo) else 0], color='gray', linestyle=':', linewidth=0.5)
            
            # P.L. (Archi)
            t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
            target_y = [y_min, y_max, y_c] if ('pir' in tipo or 'con' in tipo) else [y_min, y_max]
            for ry in target_y:
                r = abs(ry)
                ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='orange', linestyle='--', linewidth=0.7)
                ax.plot([r, r], [0, H if ry==y_c and ('pir' in tipo or 'con' in tipo) else 0], color='gray', linestyle=':', linewidth=0.5)

            # Disegno P.L.
            z_min, z_max, z_c = abs(y_max), abs(y_min), abs(y_c)
            if 'pir' in tipo or 'con' in tipo:
                ax.plot([z_min, z_max, z_c, z_min], [0, 0, H, 0], color='black', linewidth=2)
            else:
                ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color='black', linewidth=2)
    
    if not premium:
        ax.text(0, 25, "SBLOCCA MASTER PER VISTA COMPLETA", color='red', alpha=0.3, fontsize=20, ha='center', va='center', rotation=15)
    
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    return fig

# --- UI ---
if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.title("💎 Area Master")
    if not st.session_state.premium:
        st.link_button("Abbonamento Mensile (4,99€)", LINK_MENSILE)
        st.link_button("Accesso Illimitato (19,99€)", LINK_LIFETIME)
        st.divider()
        code = st.text_input("Codice attivazione:", type="password")
        if st.button("Attiva Funzioni Master"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
    else:
        st.success("✅ MODALITÀ MASTER ATTIVA")

st.title("📐 TavolaPronta AI")
traccia = st.text_area("Inserisci la traccia (anche complessa):")

if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt = """
            Sei un esperto di disegno tecnico. Analizza la traccia e restituisci un JSON con una lista di oggetti chiamata 'solidi'.
            REGOLE: Esagono=6 lati, Pentagono=5, Quadrato=4, Triangolo=3, Cilindro/Cono=100.
            Se la traccia ha più solidi, assegna dist_pv e dist_pl diversi per distanziarli.
            JSON: {"solidi": [{"tipo", "lunghezza", "profondita", "altezza", "dist_pv", "dist_pl", "rotazione", "lati"}]}
            """
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": traccia}],
                response_format={"type": "json_object"}
            )
            dati_ia = json.loads(res.choices[0].message.content)
            lista = dati_ia.get("solidi", [])
            
            if lista:
                st.pyplot(genera_proiezione_ortogonale(lista, premium=st.session_state.premium))
            else:
                st.error("L'IA non ha trovato solidi nella traccia.")
        except Exception as e:
            st.error(f"Errore tecnico: {e}")
