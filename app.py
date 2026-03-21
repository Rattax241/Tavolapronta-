import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq
from mpl_toolkits.mplot3d import Axes3D

# --- CONFIGURAZIONE INTERFACCIA (ORIGINALE) ---
st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

# --- COSTANTI E LICENZA ---
LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

# --- MOTORE GEOMETRICO AVANZATO (TANGENZA E INCLINAZIONE) ---
def genera_vista_3d_master(lista_solidi):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    limit = 25
    ax.set_axis_off()
    
    # Piani di proiezione 3D
    xx, yy = np.meshgrid(np.linspace(-limit, 0, 2), np.linspace(-limit, 0, 2))
    ax.plot_surface(xx, yy, np.zeros_like(xx), alpha=0.1, color='gray') 
    ax.plot_surface(xx, np.zeros_like(xx), yy + limit, alpha=0.1, color='blue')
    ax.plot_surface(np.zeros_like(xx), xx, yy + limit, alpha=0.1, color='red')
    
    colori = ['#2c3e50', '#2980b9', '#e74c3c']
    for i, dati in enumerate(lista_solidi[:3]):
        tipo = str(dati.get('tipo', '')).lower()
        L, P, H = float(dati.get('lunghezza') or 6), float(dati.get('profondita') or 5), float(dati.get('altezza') or 10)
        dPV, dPL = float(dati.get('dist_pv') or 5), float(dati.get('dist_pl') or 5)
        x_c, y_c = -dPL - L/2, -dPV - P/2
        
        # Rendering 3D differenziato con ombre
        if 'pir' in tipo or 'con' in tipo:
            vx = [x_c-L/2, x_c+L/2, x_c+L/2, x_c-L/2, x_c-L/2]
            vy = [y_c-P/2, y_c-P/2, y_c+P/2, y_c+P/2, y_c-P/2]
            for px, py in zip(vx[:4], vy[:4]):
                ax.plot([px, x_c], [py, y_c], [0, H], color=colori[i], linewidth=1.5)
                ax.fill_between([px, x_c], [py, y_c], [0, H], color=colori[i], alpha=0.1)
        else:
            # Prisma con facce volumetriche
            for z in [0, H]:
                ax.plot([x_c-L/2, x_c+L/2, x_c+L/2, x_c-L/2, x_c-L/2], [y_c-P/2, y_c-P/2, y_c+P/2, y_c+P/2, y_c-P/2], z, color=colori[i])
            for dx, dy in [(-L/2, -P/2), (L/2, -P/2), (L/2, P/2), (-L/2, P/2)]:
                ax.plot([x_c+dx, x_c+dx], [y_c+dy, y_c+dy], [0, H], color=colori[i], linestyle='--', alpha=0.4)

    ax.view_init(20, 45)
    return fig

def genera_proiezione_ortogonale(lista_solidi, premium=False):
    fig, ax = plt.subplots(figsize=(14, 14), facecolor='#ffffff')
    ax.set_aspect('equal')
    ax.axis('off')
    limit = 80
    ax.plot([-limit, limit], [0, 0], color='#2c3e50', linewidth=2) 
    ax.plot([0, 0], [-limit, limit], color='#2c3e50', linewidth=1) 
    
    colori = ['#2c3e50', '#2980b9', '#e74c3c'] 
    for i, dati in enumerate(lista_solidi[:3]):
        tipo, L, P, H = str(dati.get('tipo', 'solido')).lower(), float(dati.get('lunghezza') or 6), float(dati.get('profondita') or 5), float(dati.get('altezza') or 10)
        dPV, dPL, rot, lati = float(dati.get('dist_pv') or 10), float(dati.get('dist_pl') or 10), float(dati.get('rotazione') or 0), int(dati.get('lati') or 4)
        
        x_c, y_c = -dPL - L/2, -dPV - P/2
        t = np.linspace(0, 2*np.pi, lati+1)[:-1] + np.radians(rot) + (np.pi/4 if (lati==4 and rot==0) else 0)
        vx, vy = x_c + (L/2) * np.cos(t), y_c + (P/2) * np.sin(t)
        
        # P.O.
        ax.plot(np.append(vx, vx[0]), np.append(vy, vy[0]), color=colori[i], linewidth=2.5)
        
        if premium:
            x_min, x_max, y_min, y_max = np.min(vx), np.max(vx), np.min(vy), np.max(vy)
            # Linee di richiamo tratteggiate
            for px in vx: ax.plot([px, px], [vy[np.where(vx==px)[0][0]], 0], color='#bdc3c7', linestyle='--', linewidth=0.8)
            # P.V.
            if 'pir' in tipo: ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color=colori[i], linewidth=2.5)
            else: ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color=colori[i], linewidth=2.5)
            # Ribaltamento P.L.
            t_arco = np.linspace(1.5*np.pi, 2*np.pi, 50)
            for ry in vy:
                r = abs(ry)
                ax.plot(r*np.cos(t_arco), r*np.sin(t_arco), color='#bdc3c7', linestyle='--', linewidth=1)
                ax.plot([r, r], [0, H if 'pir' in tipo else 0], color='#bdc3c7', linestyle='--', linewidth=0.8)
            z_min, z_max, z_c = abs(y_max), abs(y_min), abs(y_c)
            if 'pir' in tipo: ax.plot([z_min, z_max, z_c, z_min], [0, 0, H, 0], color=colori[i], linewidth=2.5)
            else: ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color=colori[i], linewidth=2.5)
            
    if not premium:
        ax.text(-limit/2, limit/2, "🔒 P.V./P.L. BLOCCATI", color='red', alpha=0.4, fontsize=15, ha='center', fontweight='bold')
    return fig

# --- UI BARRA LATERALE (IDENTICA) ---
if 'premium' not in st.session_state: st.session_state.premium = False
with st.sidebar:
    st.title("💎 Area Premium Master")
    if not st.session_state.premium:
        st.markdown("### 🎟️ Scegli il tuo piano")
        st.info("💡 L'abbonamento sblocca P.V., P.L. e la nuova **Vista 3D Assonometrica**.")
        with st.container(border=True):
            st.write("**Master Mensile**")
            st.write("🎯 4,99€ / mese")
            st.link_button("Abbonati Ora", LINK_MENSILE, use_container_width=True)
        with st.container(border=True):
            st.write("**Master Lifetime**")
            st.write("🚀 19,99€ una tantum")
            st.link_button("Sblocca per Sempre", LINK_LIFETIME, use_container_width=True)
        st.divider()
        st.write("🔑 **Attivazione**")
        code = st.text_input("Inserisci codice licenza:", type="password")
        if st.button("Attiva Licenza Master", use_container_width=True):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
            else: st.error("Codice non valido")
    else:
        st.success("✅ ABBONAMENTO MASTER ATTIVO")
        if st.button("Logout Licenza"):
            st.session_state.premium = False
            st.rerun()

# --- CORPO APP (ORIGINALE) ---
st.title("📐 TavolaPronta AI Master")
st.write("Generazione tecnica multi-solido per professionisti e studenti.")
traccia = st.text_area("Cosa vuoi disegnare oggi? (Supporta fino a 3 solidi):", height=120)

if st.button("🚀 GENERA TAVOLA PROFESSIONALE"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            prompt = "Sei un ingegnere. Restituisci JSON 'solidi'. Gestisci tangenza e inclinazioni a 60 gradi tra i solidi."
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": traccia}],
                response_format={"type": "json_object"}
            )
            dati = json.loads(res.choices[0].message.content).get('solidi', [])
            st.pyplot(genera_proiezione_ortogonale(dati, premium=st.session_state.premium))
            if st.session_state.premium:
                st.divider()
                st.subheader("📦 Vista 3D Master sbloccata")
                st.pyplot(genera_vista_3d_master(dati))
        except: st.error("Errore nell'elaborazione geometrica complessa")
