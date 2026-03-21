import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json
from groq import Groq
from mpl_toolkits.mplot3d import Axes3D

# --- CONFIGURAZIONE INTERFACCIA (PULITA) ---
st.set_page_config(page_title="TavolaPronta AI Master", layout="wide", page_icon="📐")

# --- COSTANTI E LICENZA ---
LINK_MENSILE = "https://buy.stripe.com/TUO_LINK_MENSILE"
LINK_LIFETIME = "https://buy.stripe.com/TUO_LINK_LIFETIME"
CODICE_SEGRETO = "TP-PRO-2026-99X"

# --- VISTA Assonometrica 3D MASTER (SOLO PREMIUM) ---
def genera_vista_3d_master_semplice(lista_solidi):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    limit = 35
    ax.set_axis_off()
    
    # Stanza delle proiezioni (semplificata)
    xx, yy = np.meshgrid(np.linspace(-limit, 0, 2), np.linspace(-limit, 0, 2))
    ax.plot_surface(xx, yy, np.zeros_like(xx), alpha=0.03, color='gray') # PO
    ax.plot_surface(xx, np.zeros_like(xx), yy + limit, alpha=0.03, color='blue') # PV
    ax.plot_surface(np.zeros_like(xx), xx, yy + limit, alpha=0.03, color='red') # PL
    
    colori = ['#2c3e50', '#2980b9', '#e74c3c']
    for i, dati in enumerate(lista_solidi[:3]):
        tipo = dati.get('tipo', '').lower()
        L, P, H = float(dati.get('lunghezza') or 6), float(dati.get('profondita') or 5), float(dati.get('altezza') or 10)
        dPV, dPL = float(dati.get('dist_pv') or 10), float(dati.get('dist_pl') or 10)
        x_c, y_c = -dPL - L/2, -dPV - P/2
        
        # Geometria 3D Standard appoggiata (CAD semplice)
        if 'pir' in tipo or 'con' in tipo:
            v_x, v_y, v_z = x_c, y_c, H # Vertice dritto
            base_t = np.linspace(0, 2*np.pi, int(dati.get('lati', 6))+1)
            bx, by = x_c + (L/2) * np.cos(base_t), y_c + (P/2) * np.sin(base_t)
            for x_b, y_b in zip(bx, by):
                ax.plot([x_b, v_x], [y_b, v_y], [0, v_z], color=colori[i], linewidth=1.5)
        else:
            t = np.linspace(0, 2*np.pi, 100 if 'cil' in tipo else int(dati.get('lati', 4))+1)
            for z in [0, H]:
                ax.plot(x_c + (L/2)*np.cos(t), y_c + (P/2)*np.sin(t), z, color=colori[i], linewidth=2)
            for a in np.linspace(0, 2*np.pi, 5 if 'cil' in tipo else int(dati.get('lati', 4))):
                ax.plot([x_c+(L/2)*np.cos(a), x_c+(L/2)*np.cos(a)], [y_c+(P/2)*np.sin(a), y_c+(P/2)*np.sin(a)], [0, H], color=colori[i], alpha=0.3, linestyle='--')

    ax.view_init(25, 45)
    return fig

# --- PROIEZIONI ORTOGONALI (SOTTILE E PRECISE) ---
def genera_proiezione_ortogonale(lista_solidi, premium=False):
    fig, ax = plt.subplots(figsize=(14, 14), facecolor='#ffffff')
    ax.set_aspect('equal')
    ax.axis('off')
    limit = 85
    ax.plot([-limit, limit], [0, 0], color='#2c3e50', linewidth=2) # LT
    ax.plot([0, 0], [-limit, limit], color='#2c3e50', linewidth=1) # AV
    
    # Titoli piani
    ax.text(-limit+2, 2, "P.V.", fontsize=12, fontweight='bold', color='#7f8c8d')
    ax.text(-limit+2, -5, "P.O.", fontsize=12, fontweight='bold', color='#7f8c8d')
    ax.text(2, limit-5, "P.L.", fontsize=12, fontweight='bold', color='#7f8c8d')

    colori = ['#2c3e50', '#2980b9', '#e74c3c'] 
    
    for i, dati in enumerate(lista_solidi[:3]):
        colore = colori[i]
        tipo, L, P, H = str(dati.get('tipo', 'solido')).lower(), float(dati.get('lunghezza') or 6), float(dati.get('profondita') or 5), float(dati.get('altezza') or 10)
        dPV, dPL = float(dati.get('dist_pv') or 10), float(dati.get('dist_pl') or 10)
        
        x_c, y_c = -dPL - L/2, -dPV - P/2
        t = np.linspace(0, 2*np.pi, 100 if 'cil' in tipo else int(dati.get('lati', 4))+1)
        if dati.get('lati')==4: t += np.pi/4 
        vx, vy = x_c + (L/2) * np.cos(t), y_c + (P/2) * np.sin(t)
        
        # P.O. Sempre visibile
        ax.plot(np.append(vx, vx[0]), np.append(vy, vy[0]), color=colore, linewidth=2.5)
        if 'pir' in tipo or 'con' in tipo:
            for px, py in zip(vx, vy): ax.plot([x_c, px], [y_c, py], color=colore, linewidth=0.8, alpha=0.5)

        if premium:
            x_min, x_max, y_min, y_max = np.min(vx), np.max(vx), np.min(vy), np.max(vy)
            # Linee di proiezione (ULTRALIGHT)
            for px in vx[::15]: 
                ax.plot([px, px], [vy[np.where(vx==px)[0][0]], 0], color='#dcdde1', linestyle=':', linewidth=0.6) 
            
            # P.V. (Altezza reale dritto)
            if 'pir' in tipo or 'con' in tipo:
                ax.plot([x_min, x_max, x_c, x_min], [0, 0, H, 0], color=colore, linewidth=2.5)
            else:
                ax.plot([x_min, x_max, x_max, x_min, x_min], [0, 0, H, H, 0], color=colore, linewidth=2.5)
            
            # Linee di proiezione (ULTRALIGHT)
            for ry in vy[::15]:
                r = abs(ry)
                ax.plot(r*np.cos(np.linspace(1.5*np.pi, 2*np.pi, 30)), r*np.sin(np.linspace(1.5*np.pi, 2*np.pi, 30)), color='#dcdde1', linestyle='--', linewidth=0.5)
                ax.plot([r, r], [0, H if ry==y_c and ('pir' in tipo) else 0], color='#dcdde1', linestyle='--', linewidth=0.6)

            # P.L. (Altezza reale dritto)
            z_min, z_max = abs(np.max(vy)), abs(np.min(vy))
            if 'pir' in tipo or 'con' in tipo:
                ax.plot([z_min, z_max, abs(y_c), z_min], [0, 0, H, 0], color=colori[i], linewidth=2.5)
            else:
                ax.plot([z_min, z_max, z_max, z_min, z_min], [0, 0, H, H, 0], color=colori[i], linewidth=2.5)
    return fig

# --- SIDEBAR MONETIZZATA E CHIARA ---
if 'premium' not in st.session_state: st.session_state.premium = False
with st.sidebar:
    st.title("💎 Area Premium Master")
    if not st.session_state.premium:
        st.markdown("### 🎟️ Scegli il tuo piano")
        with st.container(border=True):
            st.write("**Master Mensile**")
            st.write("🎯 4,99€ / mese")
            st.write("Sblocca P.V., P.L. e Vista 3D.")
            st.link_button("Abbonati Ora", LINK_MENSILE, use_container_width=True)
        with st.container(border=True):
            st.write("**Master Lifetime**")
            st.write("🚀 19,99€ una tantum")
            st.write("Tutti i vantaggi per sempre.")
            st.link_button("Sblocca per Sempre", LINK_LIFETIME, use_container_width=True)
        st.divider()
        st.write("🔑 **Attivazione**")
        code = st.text_input("Inserisci codice licenza:", type="password", placeholder="Codicelicenza...")
        if st.button("Attiva Licenza Master", use_container_width=True):
            if code == CODICE_SEGRETO:
                st.session_state.premium = True
                st.rerun()
            else: st.error("Codice errato")
    else:
        st.success("✅ ABBONAMENTO MASTER ATTIVO")
        if st.button("Logout Licenza"):
            st.session_state.premium = False
            st.rerun()

# --- CORPO APP (PULITO) ---
st.title("📐 TavolaPronta AI Master")
traccia = st.text_area("Cosa vuoi disegnare oggi? (Supporta fino a 3 solidi appoggiati):", height=120)

if st.button("🚀 GENERA TAVOLA PROFESSIONALE"):
    if traccia:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            messages=[{"role": "system", "content": "Sei un motore geometrico. Restituisci JSON 'solidi'. Rileva primitive (cilindro, piramide, cono, prisma) e calcola parametri per posizionamento pulito sui piani."}]
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": messages[0]['content']}, {"role": "user", "content": traccia}],
                response_format={"type": "json_object"}
            )
            dati = json.loads(res.choices[0].message.content).get('solidi', [])
            st.pyplot(genera_proiezione_ortogonale(dati, premium=st.session_state.premium))
            if st.session_state.premium:
                st.divider()
                st.subheader("[💎 MASTER CHOICE] Vista Assonometrica Sbloccata")
                st.pyplot(genera_vista_3d_master_semplice(dati))
        except: st.error("Errore geometrico. Specifica meglio le misure.")
