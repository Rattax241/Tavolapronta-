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
    
    # Estensione limiti per ospitare il piano ausiliario
    limit = 50
    ax.plot([-limit, limit], [0, 0], color='black', linewidth=1.5)
    ax.plot([0, 0], [-limit, limit], color='black', linewidth=1)
    ax.text(-limit+2, 2, "PIANO VERTICALE (P.V.)", fontsize=10, color='gray', fontweight='bold')
    ax.text(-limit+2, -4, "PIANO ORIZZONTALE (P.O.)", fontsize=10, color='gray', fontweight='bold')
    ax.text(2, limit-3, "PIANO LATERALE (P.L.)", fontsize=10, color='gray', fontweight='bold')
    
    # Estrazione parametri con sanificazione immediata
    tipo = str(dati.get('tipo', 'solido')).lower()
    L = float(dati.get('lunghezza') or 6)
    P = float(dati.get('profondita') or 5)
    H = float(dati.get('altezza') or 10)
    dPV = float(dati.get('dist_pv') or 2)
    dPL = float(dati.get('dist_pl') or 3)
    rot = float(dati.get('rotazione') or 0)
    lati = int(dati.get('lati') or 4)
    aux = bool(dati.get('piano_ausiliario', False))

    # 1. DISEGNO P.O. (Sempre Visibile)
    x_c, y_c = -dPL - L/2, -dPV - P/2
    angle = np.radians(rot)
    offset = np.pi/4 if lati == 4 and rot == 0 else 0
    theta = np.linspace(0, 2*np.pi, lati+1)[:-1] + angle + offset
    vx = x_c + (L/2) * np.cos(theta)
    vy = y_c + (P/2) * np.sin(theta)
    
    ax.plot(np.append(vx, vx[0]), np.append(vy, vy[0]), color='black', linewidth=2.5)
    
    if 'piramide' in tipo or 'cono' in tipo:
        for px, py in zip(vx, vy):
            ax.plot([x_c, px], [y_c, py], color='black', linewidth=1)

    # 2. LOGICA PREMIUM (P.V. e P.L.)
    if premium:
        x_min, x_max = np.min(vx), np.max(vx)
        y_min, y_max = np.min(vy), np.max(vy)

        # Disegno P.V.
        if 'piramide' in tipo or 'cono' in tipo:
            ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color='black', linewidth=2.5)
        else:
            ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color='black', linewidth=2.5)
        
        # Linee di richiamo verticali
        for px in [x_min, x_max, x_c if 'pir' in tipo else x_min]:
            ax.plot([px, px], [y_max, 0], color='gray', linestyle=':', linewidth=0.7)

        # P.L. con Archi di ribaltamento (Destra)
        t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
        for ry in [y_min, y_max]:
            r = abs(ry)
            ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='orange', linestyle='--', linewidth=0.8)
            ax.plot([r, r], [0, H], color='gray', linestyle=':', linewidth=0.7)

        # Disegno P.L. Finale
        z_min, z_max = abs(y_max), abs(y_min)
        if 'piramide' in tipo or 'cono' in tipo:
            ax.plot([z_min, z_max, abs(y_c), z_min], [0, 0, H, 0], color='black', linewidth=2.5)
        else:
            ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color='black', linewidth=2.5)

        # 3. PIANO AUSILIARIO (Quadrante Sinistro - Vera Forma)
        if aux:
            ang_pa = np.radians(135) 
            ax.plot([0, limit*np.cos(ang_pa)], [0, limit*np.sin(ang_pa)], color='blue', linewidth=1.5, linestyle='-.')
            ax.text(limit*np.cos(ang_pa)+2, limit*np.sin(ang_pa), "P.A.", color='blue', fontweight='bold')
            
            # Archi di ribaltamento verso sinistra
            t_arco_aux = np.linspace(0.5*np.pi, ang_pa, 50)
            for r_val in [abs(x_min), abs(x_max)]:
                ax.plot(-r_val*np.cos(t_arco_aux - np.pi/2), r_val*np.sin(t_arco_aux - np.pi/2), color='blue', linestyle='--', linewidth=0.6)

    else:
        ax.text(15, 15, "SBLOCCA MASTER\nPER P.V. E P.L.", color='red', alpha=0.3, fontsize=18, ha='center', va='center', rotation=45)

    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    return fig

# --- UI APP ---
if 'premium' not in st.session_state: st.session_state.premium = False

with st.sidebar:
    st.title("💎 Area Master")
    if not st.session_state.premium:
        st.link_button("Abbonamento Mensile (4,99€)", LINK_MENSILE)
        st.link_button("Accesso Illimitato (19,99€)", LINK_LIFETIME)
        code = st.text_input("Codice licenza:", type="password")
        if st.button("Attiva Master"):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
    else:
        st.success("✅ MODALITÀ MASTER ATTIVA")
        if st.button("Logout Licenza"):
            st.session_state.premium = False
            st.rerun()

st.title("📐 TavolaPronta AI Master")
traccia = st.text_area("Cosa devi disegnare?")

if st.button("🚀 GENERA TAVOLA"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt_sistema = """
            Sei un ingegnere. Estrai i dati e rispondi SOLO in JSON. 
            IMPORTANTE: Tutti i valori devono essere NUMERI.
            Se la traccia chiede 'piano ausiliario' o 'vera forma', imposta 'piano_ausiliario': true.
            JSON: {"tipo": "string", "lunghezza": 6, "profondita": 4, "altezza": 10, "dist_pv": 5, "dist_pl": 7, "rotazione": 0, "lati": 4, "piano_ausiliario": false}
            """
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": traccia}],
                response_format={"type": "json_object"}
            )
            
            dati_raw = json.loads(res.choices[0].message.content)
            
            # Sanificazione post-IA per prevenire TypeError
            dati_puliti = {
                'tipo': str(dati_raw.get('tipo', 'solido')),
                'lunghezza': float(dati_raw.get('lunghezza') or 6),
                'profondita': float(dati_raw.get('profondita') or 5),
                'altezza': float(dati_raw.get('altezza') or 10),
                'dist_pv': float(dati_raw.get('dist_pv') or 2),
                'dist_pl': float(dati_raw.get('dist_pl') or 3),
                'rotazione': float(dati_raw.get('rotazione') or 0),
                'lati': int(dati_raw.get('lati') or 4),
                'piano_ausiliario': bool(dati_raw.get('piano_ausiliario', False))
            }
            
            st.pyplot(genera_proiezione_ortogonale(dati_puliti, premium=st.session_state.premium))
        except Exception as e:
            st.error("L'IA ha avuto un problema con i numeri. Prova a riscrivere la traccia più chiaramente.")

