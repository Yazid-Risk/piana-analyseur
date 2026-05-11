"""
Analyseur de solvabilité et de crédit — Piana v8
=================================================
pip install streamlit plotly
python -m streamlit run analyse_credit.py
"""

import streamlit as st
import plotly.graph_objects as go
import math, os, base64, hashlib

st.set_page_config(page_title="Analyseur de solvabilité · Piana", page_icon="📊", layout="wide")

# ── Logo Piana ────────────────────────────────────────────────────────────────
def _logo_b64():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "piana_logo.png")
    if os.path.exists(p):
        with open(p, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

LOGO = _logo_b64()
LOGO_HTML = f'<img src="data:image/png;base64,{LOGO}" style="height:28px;vertical-align:middle">' if LOGO else '<b style="font-size:18px;color:#1e3a5f">Piana</b>'
LOGO_IMG   = f'<img src="data:image/png;base64,{LOGO}" style="height:44px">' if LOGO else '<span style="font-size:28px;font-weight:700;color:#1e3a5f">piana</span>'

# ── Authentification ──────────────────────────────────────────────────────────
def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def _get_users() -> dict:
    """Lit les utilisateurs depuis st.secrets ou retourne des defaults."""
    try:
        return dict(st.secrets["users"])
    except Exception:
        # Fallback local (à NE PAS utiliser en production)
        return {"admin": _hash("piana2024")}

def _login_page():
    """Page de connexion centrée avec branding Piana."""
    st.markdown("""<style>
    .stApp{background:linear-gradient(135deg,#1e3a5f 0%,#2d5282 100%)!important}
    </style>""", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown(f"""
        <div style='background:white;border-radius:16px;padding:40px 36px;
             box-shadow:0 20px 60px rgba(0,0,0,.25);margin-top:60px;text-align:center'>
          <div style='margin-bottom:28px'>{LOGO_IMG}</div>
          <h2 style='color:#1e3a5f;font-size:18px;font-weight:700;margin:0 0 6px'>Analyseur de solvabilité</h2>
          <p style='color:#9ca3af;font-size:13px;margin:0 0 28px'>Connectez-vous pour accéder à l'outil</p>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            username = st.text_input("Identifiant", placeholder="votre.prenom",
                                     label_visibility="collapsed")
            password = st.text_input("Mot de passe", type="password",
                                     placeholder="Mot de passe",
                                     label_visibility="collapsed")
            login_btn = st.button("Se connecter →", type="primary", use_container_width=True)

            if login_btn:
                users = _get_users()
                if username in users and users[username] == _hash(password):
                    st.session_state["logged_in"]  = True
                    st.session_state["username"]   = username
                    st.rerun()
                elif username and password:
                    st.error("Identifiant ou mot de passe incorrect.")

        st.markdown("<p style='text-align:center;color:#d1d5db;font-size:11px;margin-top:16px'>Piana · Accès restreint</p>", unsafe_allow_html=True)

    st.stop()

# Vérification auth — bloque tout si non connecté
if not st.session_state.get("logged_in", False):
    _login_page()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""<style>
.stApp{background:#f5f6fa}
.main .block-container{padding-top:1.2rem;padding-bottom:2rem}
[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #e5e7eb}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{font-size:11px;color:#6b7280}
.stNumberInput label,.stSelectbox label{font-size:12px!important;font-weight:500!important}
.stButton>button{border-radius:7px;font-weight:600;font-size:13px;transition:opacity .15s}
.stButton>button:hover{opacity:.88}
.stTabs [data-baseweb="tab-list"]{gap:4px;background:transparent}
.stTabs [data-baseweb="tab"]{padding:10px 20px;border-radius:8px 8px 0 0;font-weight:500;font-size:14px;color:#6b7280}
.stTabs [aria-selected="true"]{color:#1e3a5f!important;background:white!important}
footer{display:none}
</style>""", unsafe_allow_html=True)

# ── Constantes ────────────────────────────────────────────────────────────────
PEPEL = dict(ac=2_499_784,sk=60_576,tr=103_052,ta=18_234_077,
             cp=7_278_554,df=10_064_035,dct=2_800_983,td=10_955_523,
             ca=1_427_349,va=983_716,eb=247_832,rn=-282_795,cf=469_171,da=296_649)
KEYS = list(PEPEL.keys())

HELP = {
    "ac":"📍 Bilan Actif → **Total Actif Circulant** (colonne Nette)\n\nStocks + Créances clients + Trésorerie + Autres actifs CT.\nCERFA : sous-total II (Net N)",
    "sk":"📍 Bilan Actif → **Stocks et en-cours** (valeur nette)\n\nMarchandises, matières premières, en-cours.\nPour un service ou holding : souvent ≈ 0.\nCERFA : Ligne BF (Net)",
    "tr":"📍 Bilan Actif → **Disponibilités**\n\nComptes bancaires + caisse + placements CT.\nC'est l'argent disponible immédiatement.\nCERFA : Ligne BT (Net)",
    "ta":"📍 Bilan Actif → **Total Général** (dernière ligne)\n\nÉgal au Total Passif — même chiffre.\nCERFA : Ligne BX",
    "cp":"📍 Bilan Passif → **Total Capitaux Propres**\n\nCapital + réserves + report + résultat.\n⚠️ Peut être **négatif** si pertes > capital.\nCERFA : Ligne DL",
    "df":"📍 Bilan Passif → **Emprunts bancaires uniquement**\n\nPas les dettes fournisseurs, URSSAF, TVA.\nSommez toutes les lignes Emprunts (16xxx).\nCERFA : Lignes DT à DX",
    "dct":"📍 Bilan Passif → dettes exigibles à **< 1 an**\n\nEmprunts CT + fournisseurs + URSSAF + TVA + autres CT.\n**Estimez :** Total dettes − Dettes LT\nCERFA : colonnes 'À moins d'1 an'",
    "td":"📍 Bilan Passif → **Total Dettes** (dernière ligne section Dettes)\n\n**Calculez :** Total Actif − Capitaux Propres\nCERFA : Ligne EE",
    "ca":"📍 Compte de résultat → **Chiffre d'affaires net** HT\n\nOu SIG : **Total Activité HT**\nCERFA : Ligne FL",
    "va":"📍 SIG → ligne **VALEUR AJOUTÉE**\n\nOu : CA − Achats consommés − Charges externes\n⚠️ Non disponible dans un bilan standard.",
    "eb":"📍 SIG → ligne **EXCÉDENT BRUT D'EXPLOITATION**\n\nOu : Valeur ajoutée − Charges personnel − Taxes\n⚠️ Non disponible dans un bilan standard.",
    "rn":"📍 Compte de résultat → **Résultat de l'exercice** (dernière ligne)\n\n✅ Positif = bénéfice · ❌ Négatif = perte\nCERFA : Ligne HN",
    "cf":"📍 Compte de résultat → **Total Charges financières**\n\nIntérêts sur emprunts + agios + frais bancaires.\nPrend le total de la section.\nCERFA : Ligne GF",
    "da":"📍 Compte de résultat → **Dotations aux amortissements**\n\nDépréciation comptable des actifs. PAS une sortie de cash.\nCERFA : Lignes 6811 + 6812",
}

BORDER={"good":"#16a34a","warn":"#d97706","danger":"#dc2626"}
BG    ={"good":"#f0fdf4","warn":"#fffbeb","danger":"#fef2f2"}
TX    ={"good":"#15803d","warn":"#b45309","danger":"#b91c1c"}
BADGE ={"good":"#dcfce7","warn":"#fef3c7","danger":"#fee2e2"}
IC    ={"good":"✓ bon","warn":"⚠ moyen","danger":"✗ alerte"}

# ── Session state ─────────────────────────────────────────────────────────────
for k in KEYS: st.session_state.setdefault(f"inp_{k}", 0.0)

# ── Guide ─────────────────────────────────────────────────────────────────────
GUIDE = [
    {"name":"Liquidité générale","emoji":"💧","definition":"L'entreprise peut-elle payer ses dettes CT avec ses actifs CT ?","num":"Actif circulant","den":"Total dettes CT","op":"÷","seuils":[("🔴 < 1,0","danger","Actif insuffisant — risque de défaut immédiat."),("🟡 1,0 – 1,5","warn","Juste équilibré, peu de marge."),("🟢 ≥ 1,5","good","Pour 1€ de dette CT, ≥1,50€ d'actifs.")],"astuce":"Premier ratio à vérifier pour toute ligne de crédit CT."},
    {"name":"Liquidité réduite","emoji":"🔵","definition":"Idem, sans les stocks (moins liquides).","num":"Actif circ. − Stocks","den":"Total dettes CT","op":"÷","seuils":[("🔴 < 0,7","danger","Insuffisant même sans les stocks."),("🟡 0,7 – 1,0","warn","Acceptable, dépend des créances."),("🟢 ≥ 1,0","good","Dettes CT couvertes sans vendre les stocks.")],"astuce":"Pour les sociétés de services ≈ liquidité générale (stocks ≈ 0)."},
    {"name":"Liquidité immédiate","emoji":"💵","definition":"L'argent en banque aujourd'hui couvre-t-il les dettes CT ?","num":"Trésorerie","den":"Total dettes CT","op":"÷","seuils":[("🔴 < 0,1","danger","Tréso quasi-nulle — tout imprévu = défaut."),("🟡 0,1 – 0,3","warn","Limitée — vérifier prélèvements à 7j."),("🟢 ≥ 0,3","good","Cash confortable.")],"astuce":"Pour prélèvement à 7 jours : CE ratio EN PRIORITÉ."},
    {"name":"Autonomie financière","emoji":"🏛️","definition":"Part des dettes couverte par les fonds propres.","num":"Capitaux propres","den":"Total dettes","op":"÷","seuils":[("🔴 < 0,25","danger","Très dépendante des créanciers."),("🟡 0,25 – 0,5","warn","Dépendance modérée."),("🟢 ≥ 0,5","good","Bonne indépendance.")],"astuce":"Capitaux propres négatifs = ratio négatif = situation grave."},
    {"name":"Levier d'endettement","emoji":"⚖️","definition":"Combien de fois la dette dépasse les fonds propres ?","num":"Dettes financières","den":"Capitaux propres","op":"÷","seuils":[("🟢 ≤ 1,0","good","Structure saine."),("🟡 1,0 – 3,0","warn","Plus endetté que les fonds propres."),("🔴 > 3,0","danger","Très fortement endetté.")],"astuce":"En immobilier 2-3x courant. En dehors >2 alarmant."},
    {"name":"Solvabilité globale","emoji":"🏢","definition":"En vendant tout, l'entreprise rembourserait-elle toutes ses dettes ?","num":"Total actif","den":"Total dettes","op":"÷","seuils":[("🔴 < 1,5","danger","Actifs insuffisants pour couvrir les dettes."),("🟡 1,5 – 2,0","warn","Couverture limitée."),("🟢 ≥ 2,0","good","2€ d'actifs pour 1€ de dette.")],"astuce":"Actifs à valeur comptable — souvent sous-évalués pour l'immobilier."},
    {"name":"Couverture des intérêts","emoji":"💳","definition":"L'EBE couvre-t-il les intérêts ? Si <1 : impossible de payer les intérêts.","num":"EBE","den":"Charges financières","op":"÷","seuils":[("🔴 < 1,0","danger","EBE insuffisant — situation intenable."),("🟡 1,0 – 3,0","warn","Intérêts couverts mais marge faible."),("🟢 ≥ 3,0","good","EBE couvre largement les intérêts.")],"astuce":"Les banques (DSCR) bloquent souvent sous 1,2."},
    {"name":"CAF","emoji":"🔄","definition":"Cash réellement généré pour rembourser ou investir.","num":"Résultat net + Dotations","den":"(€ absolus)","op":"=","seuils":[("🔴 Négative","danger","Consomme du cash — s'appauvrit."),("🟡 0 – 50 K€","warn","CAF quasi-nulle — très fragile."),("🟢 > 50 K€","good","Génère assez de cash.")],"astuce":"Les dotations s'ajoutent car ce sont des charges, pas des sorties de cash."},
    {"name":"Dettes nettes / CAF","emoji":"⏱️","definition":"En combien d'années pourrait-elle rembourser ses dettes avec sa CAF ?","num":"Dettes financières","den":"CAF","op":"÷","seuils":[("🟢 ≤ 3 ans","good","Remboursement rapide."),("🟡 3 – 7 ans","warn","Long mais possible."),("🔴 > 7 ans","danger","Quasi-impossible à rembourser.")],"astuce":"CAF négative → ratio = ∞. Banques bloquent souvent >5-7 ans."},
    {"name":"Rentabilité nette","emoji":"📈","definition":"Sur 100€ de CA, combien reste-t-il en bénéfice ?","num":"Résultat net","den":"CA HT × 100","op":"÷","seuils":[("🔴 < 0%","danger","Perte."),("🟡 0% – 5%","warn","Bénéficiaire mais fragile."),("🟢 ≥ 5%","good","Bonne rentabilité.")],"astuce":"Moyenne française : 2-5%. Deux années négatives = signal fort."},
    {"name":"Taux valeur ajoutée","emoji":"🏭","definition":"Richesse créée après paiement des fournisseurs.","num":"Valeur ajoutée","den":"CA HT × 100","op":"÷","seuils":[("🔴 < 30%","danger","Peu de valeur créée."),("🟡 30% – 50%","warn","Correct — typique industrie."),("🟢 ≥ 50%","good","Élevé — typique services.")],"astuce":"Pour holdings et services, naturellement élevé."},
    {"name":"Taux EBE","emoji":"💰","definition":"Sur 100€ de CA, combien avant intérêts et amortissements ?","num":"EBE","den":"CA HT × 100","op":"÷","seuils":[("🔴 < 5%","danger","Marge insuffisante."),("🟡 5% – 15%","warn","Correct."),("🟢 ≥ 15%","good","Bonne marge opérationnelle.")],"astuce":"EBE positif + résultat négatif = sain opérationnellement mais écrasé par la dette."},
]

# ── Utilitaires ───────────────────────────────────────────────────────────────
def safe(a,b): return a/b if b!=0 else math.inf
def fmt_x(v,d=2): return f"{v:.{d}f}" if math.isfinite(v) else "∞"
def fmt_p(v): return f"{v:.1f} %" if math.isfinite(v) else "—"
def fmt_eur(v):
    if not math.isfinite(v): return "—"
    a=abs(v); s="-" if v<0 else ""
    if a>=1e6: return f"{s}{a/1e6:.2f} M€"
    if a>=1e3: return f"{s}{a/1e3:.1f} K€"
    return f"{s}{a:.0f} €"
def tier(v,hi,lo,rev=False):
    if not math.isfinite(v): return "danger"
    if rev: return "good" if v<=hi else "warn" if v<=lo else "danger"
    return "good" if v>=hi else "warn" if v>=lo else "danger"

def card(name,val,t,formula,threshold):
    return (f"<div style='background:white;border-radius:9px;padding:14px 16px;"
            f"border-left:4px solid {BORDER[t]};box-shadow:0 1px 4px rgba(0,0,0,.07);margin-bottom:10px'>"
            f"<div style='display:flex;justify-content:space-between;align-items:flex-start;gap:6px;margin-bottom:6px'>"
            f"<span style='font-size:12px;font-weight:600;color:#374151'>{name}</span>"
            f"<span style='font-size:10px;padding:2px 9px;border-radius:12px;background:{BADGE[t]};color:{TX[t]};font-weight:700;white-space:nowrap'>{IC[t]}</span>"
            f"</div><div style='font-size:26px;font-weight:700;color:{TX[t]};margin-bottom:4px'>{val}</div>"
            f"<div style='font-size:11px;color:#9ca3af;margin-bottom:2px'>{formula}</div>"
            f"<div style='font-size:10px;color:#d1d5db'>{threshold}</div></div>")

def _a(s):
    """Remplace les caracteres accentues pour compatibilite PDF."""
    return (s.replace('\xe9','e').replace('\xe8','e').replace('\xea','e').replace('\xeb','e')
             .replace('\xe0','a').replace('\xe2','a').replace('\xf4','o').replace('\xf9','u')
             .replace('\xfb','u').replace('\xee','i').replace('\xef','i').replace('\xe7','c')
             .replace('\xc9','E').replace('\xc8','E').replace('\xca','E').replace('\xc0','A')
             .replace('\xc2','A').replace('\xd4','O').replace('\xdb','U').replace('\xce','I')
             .replace('\u2265','>=').replace('\u2264','<=').replace('\xf7','/').replace('\xd7','x')
             .replace('\u221e','inf').replace('\u2013','-').replace('\u2014','-')
             .replace('\u2019',"'").replace('\u2018',"'")
             .replace('\u2713','OK').replace('\u26a0','!').replace('\u2717','X').replace('\u2022','-'))

def generate_pdf_report(client_name, score, vc, vt, vb, RATIOS, vigilance,
                         rec_duree, rec_delai, rv, rl,
                         has_sim, montant, duree, delai, enc,
                         dep_min, dep_rec, dep_max,
                         taux, rev_trans, rev_annuel, profit_net, renouvellements):
    from fpdf import FPDF
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    import tempfile, os
    from datetime import datetime

    NAVY=(30,58,95); GREEN=(21,128,61); ORANGE=(180,83,9); RED=(185,28,28)
    LGRAY=(249,250,251); DGRAY=(55,65,81); MGRAY=(107,114,128)
    T_COL={"good":GREEN,"warn":ORANGE,"danger":RED}
    T_LBL={"good":"Bon","warn":"Moyen","danger":"Alerte"}

    # Radar chart (matplotlib)
    fig=plt.figure(figsize=(4,4),facecolor='white')
    ax=fig.add_subplot(111,polar=True)
    N=len(rl); angles=np.linspace(0,2*np.pi,N,endpoint=False).tolist()
    rv2=rv+[rv[0]]; ang2=angles+[angles[0]]
    ax.plot(ang2,rv2,'o-',lw=2,color='#1e3a5f')
    ax.fill(ang2,rv2,alpha=0.15,color='#1e3a5f')
    ax.set_xticks(angles)
    ax.set_xticklabels([_a(l) for l in rl],size=7)
    ax.set_ylim(0,100); ax.set_yticks([25,50,75,100])
    ax.set_yticklabels(['','50','','100'],size=6,color='gray')
    ax.grid(True,alpha=0.3); ax.set_facecolor('white')
    radar_tmp=tempfile.mktemp(suffix='.png')
    plt.savefig(radar_tmp,dpi=120,bbox_inches='tight',facecolor='white'); plt.close()

    # Logo temp
    logo_tmp=None
    if LOGO:
        logo_tmp=tempfile.mktemp(suffix='.png')
        with open(logo_tmp,'wb') as f: f.write(base64.b64decode(LOGO))

    class PDF(FPDF):
        def header(self):
            if logo_tmp: self.image(logo_tmp,10,8,38)
            self.set_font('Helvetica','B',13); self.set_text_color(*NAVY)
            self.set_y(8)
            self.cell(0,6,'Analyse de Solvabilite et de Credit',0,1,'R')
            self.set_font('Helvetica','',8); self.set_text_color(*MGRAY)
            now=datetime.now().strftime('%d/%m/%Y a %H:%M')
            cli=f'  |  {_a(client_name)}' if client_name else ''
            self.cell(0,4,f'Genere le {now}{cli}',0,1,'R')
            self.ln(2)
            self.set_draw_color(*NAVY); self.set_line_width(0.4)
            self.line(10,self.get_y(),200,self.get_y()); self.ln(4)
        def footer(self):
            self.set_y(-13); self.set_font('Helvetica','I',7)
            self.set_text_color(*MGRAY)
            self.cell(0,8,f'Piana  |  Outil d\'aide a la decision  |  Page {self.page_no()}',0,0,'C')

    pdf=PDF(orientation='P',unit='mm',format='A4')
    pdf.set_auto_page_break(auto=True,margin=15)
    pdf.add_page()

    # Score banner
    sc=T_COL[vc]
    pdf.set_fill_color(*sc); pdf.set_text_color(255,255,255)
    pdf.set_font('Helvetica','B',26); pdf.cell(22,14,str(score),0,0,'C',True)
    pdf.set_text_color(*DGRAY); pdf.set_font('Helvetica','B',12)
    pdf.cell(0,7,f'  {_a(vt)}',0,1)
    pdf.set_x(32); pdf.set_font('Helvetica','',9); pdf.set_text_color(*MGRAY)
    pdf.cell(0,5,f'  {_a(vb)}',0,1); pdf.ln(4)

    # Ratios table
    pdf.set_font('Helvetica','B',9); pdf.set_text_color(*NAVY)
    pdf.cell(0,5,'DETAIL DES 12 RATIOS',0,1); pdf.ln(1)
    # Header
    pdf.set_fill_color(*NAVY); pdf.set_text_color(255,255,255); pdf.set_font('Helvetica','B',7.5)
    pdf.cell(78,5.5,'  Ratio',0,0,'L',True); pdf.cell(22,5.5,'Valeur',0,0,'C',True)
    pdf.cell(60,5.5,'Formule · Seuil',0,0,'C',True); pdf.cell(0,5.5,'Statut',0,1,'C',True)
    # Rows
    for i,(name,val,t,formula,threshold) in enumerate(RATIOS):
        bg=LGRAY if i%2==0 else (255,255,255)
        tc=T_COL[t]
        pdf.set_fill_color(*bg); pdf.set_text_color(*DGRAY)
        pdf.set_font('Helvetica','',7.5)
        pdf.cell(78,5.2,f'  {_a(name)}',0,0,'L',True)
        pdf.set_font('Helvetica','B',7.5); pdf.set_text_color(*tc)
        pdf.cell(22,5.2,_a(val),0,0,'C',True)
        pdf.set_text_color(*MGRAY); pdf.set_font('Helvetica','',6.5)
        combined=f'{_a(formula)}  |  {_a(threshold)}'
        pdf.cell(60,5.2,combined[:42],0,0,'C',True)
        pdf.set_text_color(*tc); pdf.set_font('Helvetica','B',7)
        pdf.cell(0,5.2,T_LBL[t],0,1,'C',True)
    pdf.ln(4)

    # Radar + recommendations (2 columns)
    y0=pdf.get_y()
    pdf.set_font('Helvetica','B',9); pdf.set_text_color(*NAVY)
    pdf.cell(90,5,'PROFIL DE RISQUE',0,0); pdf.cell(0,5,'RECOMMANDATIONS',0,1)
    radar_y=pdf.get_y()
    pdf.image(radar_tmp,10,radar_y,78)

    # Recommendations column
    rx=92
    # Ligne recommandée
    rc=T_COL["good"] if score>=65 else T_COL["warn"] if score>=40 else T_COL["danger"]
    pdf.set_xy(rx,radar_y)
    pdf.set_fill_color(*rc); pdf.set_text_color(255,255,255); pdf.set_font('Helvetica','B',8)
    pdf.cell(108,5.5,f'Ligne {_a(rec_duree)}  |  Delai {_a(rec_delai)}',0,1,'C',True)
    pdf.ln(2)
    for t,titre,txt in vigilance[:5]:
        tc=T_COL[t]
        pdf.set_x(rx); pdf.set_text_color(*tc); pdf.set_font('Helvetica','B',7)
        pdf.cell(108,4,_a(titre[:52]),0,1)
        pdf.set_x(rx); pdf.set_text_color(*MGRAY); pdf.set_font('Helvetica','',6.8)
        txt2=_a(txt[:75]+('...' if len(txt)>75 else ''))
        pdf.multi_cell(108,3.5,txt2); pdf.ln(1)
    pdf.set_y(max(pdf.get_y(),radar_y+80)); pdf.ln(4)

    # Page 2: Simulateur
    if has_sim:
        pdf.add_page()
        pdf.set_font('Helvetica','B',9); pdf.set_text_color(*NAVY)
        pdf.cell(0,5,'SIMULATEUR D\'ENCOURS',0,1); pdf.ln(2)

        sim_rows=[
            ('Montant de la ligne',f'{montant:,.0f} EUR'),
            ('Duree',f'{duree} jours'),
            ('Delai de paiement',f'{delai} jours'),
            ('Consommation / jour',f'{montant/duree:,.2f} EUR'),
            ('Encours total expose',f'{enc:,.0f} EUR'),
            ('Duree d\'exposition totale',f'{duree+delai} jours'),
        ]
        if taux>0:
            sim_rows+=[
                ('Taux par ligne',f'{taux:.2f}%'),
                (f'Revenu par ligne ({duree}j)',f'{rev_trans:,.2f} EUR'),
                (f'Revenu annuel ({renouvellements} lignes/an)',f'{rev_annuel:,.0f} EUR'),
                ('Profit net estime (risque deduit)',f'{profit_net:,.0f} EUR'),
            ]
        cw=95
        for i in range(0,len(sim_rows),2):
            pdf.set_fill_color(*LGRAY)
            l1,v1=sim_rows[i]
            pdf.set_text_color(*MGRAY); pdf.set_font('Helvetica','',8)
            pdf.cell(cw//2,5.5,_a(l1),0,0,'L',True)
            pdf.set_text_color(*DGRAY); pdf.set_font('Helvetica','B',8)
            pdf.cell(cw//2,5.5,v1,0,0,'R',True)
            if i+1<len(sim_rows):
                l2,v2=sim_rows[i+1]
                pdf.set_text_color(*MGRAY); pdf.set_font('Helvetica','',8)
                pdf.cell(cw//2,5.5,_a(l2),0,0,'L',True)
                pdf.set_text_color(*DGRAY); pdf.set_font('Helvetica','B',8)
                pdf.cell(cw//2,5.5,v2,0,1,'R',True)
            else: pdf.ln()
        pdf.ln(5)

        # Dépôt de garantie
        pdf.set_font('Helvetica','B',9); pdf.set_text_color(*NAVY)
        pdf.cell(0,5,'DEPOT DE GARANTIE RECOMMANDE',0,1); pdf.ln(2)
        dep_rows=[
            ('Minimum acceptable',f'{dep_min:,.0f} EUR',GREEN),
            ('Recommande',f'{dep_rec:,.0f} EUR',ORANGE),
            ('Maximum justifiable',f'{dep_max:,.0f} EUR',RED),
            ('Encours net apres depot (rec.)',f'{enc-dep_rec:,.0f} EUR',NAVY),
        ]
        for label,val,col in dep_rows:
            pdf.set_fill_color(*LGRAY)
            pdf.set_text_color(*MGRAY); pdf.set_font('Helvetica','',9)
            pdf.cell(130,6,_a(label),0,0,'L',True)
            pdf.set_text_color(*col); pdf.set_font('Helvetica','B',9)
            pdf.cell(60,6,val,0,1,'R',True)

    # Cleanup
    try:
        os.remove(radar_tmp)
        if logo_tmp: os.remove(logo_tmp)
    except: pass

    return bytes(pdf.output())

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    if LOGO:
        st.image("piana_logo.png", width=120)
    else:
        st.markdown("**Piana**")
    st.markdown("---")
    client_name = st.text_input("🏢 Nom du client", placeholder="Ex: PEPEL SAS",
                                 key="client_name",
                                 help="Apparaît sur le rapport PDF exporté")
    st.markdown("---")
    c1,c2=st.columns(2)
    with c1:
        if st.button("📥 Démo PEPEL",use_container_width=True):
            for k,v in PEPEL.items(): st.session_state[f"inp_{k}"]=float(v)
            st.rerun()
    with c2:
        if st.button("🗑 Effacer",use_container_width=True):
            for k in KEYS: st.session_state[f"inp_{k}"]=0.0
            st.rerun()
    st.markdown("---")
    st.markdown("#### 📋 Actif (valeurs nettes)")
    ac  = st.number_input("Actif circulant €",           step=1000.0,key="inp_ac", format="%0.0f",help=HELP["ac"])
    sk  = st.number_input("  dont Stocks €",             step=1000.0,key="inp_sk", format="%0.0f",help=HELP["sk"])
    tr  = st.number_input("  dont Trésorerie €",         step=1000.0,key="inp_tr", format="%0.0f",help=HELP["tr"])
    ta  = st.number_input("Total actif €",               step=1000.0,key="inp_ta", format="%0.0f",help=HELP["ta"])
    st.markdown("#### 🏦 Passif")
    cp  = st.number_input("Capitaux propres €",          step=1000.0,key="inp_cp", format="%0.0f",help=HELP["cp"])
    df  = st.number_input("Dettes financières totales €",step=1000.0,key="inp_df", format="%0.0f",help=HELP["df"])
    dct = st.number_input("Total dettes CT (toutes) €",  step=1000.0,key="inp_dct",format="%0.0f",help=HELP["dct"])
    td  = st.number_input("Total dettes €",              step=1000.0,key="inp_td", format="%0.0f",help=HELP["td"])
    st.markdown("#### 📊 Compte de résultat")
    ca  = st.number_input("CA HT €",                     step=1000.0,key="inp_ca", format="%0.0f",help=HELP["ca"])
    va  = st.number_input("Valeur ajoutée €",            step=1000.0,key="inp_va", format="%0.0f",help=HELP["va"])
    eb  = st.number_input("EBE €",                       step=1000.0,key="inp_eb", format="%0.0f",help=HELP["eb"])
    rn  = st.number_input("Résultat net €",              step=1000.0,key="inp_rn", format="%0.0f",help=HELP["rn"])
    cf  = st.number_input("Charges financières €",       step=1000.0,key="inp_cf", format="%0.0f",help=HELP["cf"])
    da  = st.number_input("Dotations amortissements €",  step=1000.0,key="inp_da", format="%0.0f",help=HELP["da"])
    st.markdown("---")
    st.caption("💡 Cliquez sur **?** à côté de chaque champ pour savoir où le trouver dans votre document.")
    st.markdown("---")
    # Utilisateur connecté + déconnexion
    user = st.session_state.get("username", "")
    cu1, cu2 = st.columns([2, 1])
    with cu1:
        st.markdown(f"<p style='font-size:12px;color:#6b7280;margin:4px 0'>👤 <b>{user}</b></p>", unsafe_allow_html=True)
    with cu2:
        if st.button("Déco.", use_container_width=True, help="Se déconnecter"):
            st.session_state["logged_in"] = False
            st.session_state["username"]  = ""
            st.rerun()

# ── Calculs (avant tabs, pour disponibilité partout) ─────────────────────────
has_data = any([ac, cp, ca])
score, vc, vt, vb = 0, "warn", "", ""
lg=lr=li=aut=lev=sol=cov=caf=dnc=ret=tva=teb = 0.0
RATIOS = []

if has_data:
    lg=safe(ac,dct); lr=safe(ac-sk,dct); li=safe(tr,dct)
    aut=safe(cp,td); lev=safe(df,cp);    sol=safe(ta,td)
    cov=safe(eb,cf); caf=rn+da;          dnc=safe(df,caf) if caf>0 else math.inf
    ret=(rn/ca*100) if ca>0 else 0.0
    tva=(va/ca*100) if ca>0 else 0.0
    teb=(eb/ca*100) if ca>0 else 0.0

    RATIOS=[
        ("Liquidité générale",   fmt_x(lg),  tier(lg,1.5,1.0),        "Actif circ. ÷ Dettes CT",    "≥1.5 bon · ≥1.0 moyen"),
        ("Liquidité réduite",    fmt_x(lr),  tier(lr,1.0,0.7),        "(Actif−Stocks) ÷ Dettes CT", "≥1.0 bon · ≥0.7 moyen"),
        ("Liquidité immédiate",  fmt_x(li),  tier(li,0.3,0.1),        "Trésorerie ÷ Dettes CT",     "≥0.3 bon · ≥0.1 moyen"),
        ("Autonomie financière", fmt_x(aut), tier(aut,0.5,0.25),      "Cap. propres ÷ Total dettes","≥0.5 bon · ≥0.25 moyen"),
        ("Levier d'endettement", fmt_x(lev), tier(lev,1.0,3.0,True), "Dettes fin. ÷ Cap. propres", "≤1.0 bon · ≤3.0 moyen"),
        ("Solvabilité globale",  fmt_x(sol), tier(sol,2.0,1.5),       "Total actif ÷ Total dettes", "≥2.0 bon · ≥1.5 moyen"),
        ("Couverture intérêts",  fmt_x(cov), tier(cov,3.0,1.0),       "EBE ÷ Charges financières",  "≥3.0 bon · ≥1.0 moyen"),
        ("CAF",fmt_eur(caf),"good" if caf>50000 else "warn" if caf>0 else "danger","Résultat + Dotations","Positive requise"),
        ("Dettes nettes / CAF",
            (fmt_x(dnc,1)+"x") if (math.isfinite(dnc) and dnc>0) else "∞",
            tier(dnc,3.0,7.0,True) if (math.isfinite(dnc) and dnc>0) else "danger",
            "Dettes fin. ÷ CAF","≤3x bon · ≤7x moyen"),
        ("Rentabilité nette",    fmt_p(ret), tier(ret,5,0),           "Résultat ÷ CA HT",           "≥5% bon · ≥0% moyen"),
        ("Taux valeur ajoutée",  fmt_p(tva), tier(tva,50,30),         "VA ÷ CA HT",                 "≥50% bon · ≥30% moyen"),
        ("Taux EBE",             fmt_p(teb), tier(teb,15,5),          "EBE ÷ CA HT",                "≥15% bon · ≥5% moyen"),
    ]
    W=[2,1.5,2,1.5,1,1,2,1,2,1.5,1,1]; S={"good":2,"warn":1,"danger":0}
    score=round(sum(S[r[2]]*W[i] for i,r in enumerate(RATIOS))/sum(2*w for w in W)*100)
    if score>=65: vc,vt,vb="good","✅ Dossier favorable","Profil acceptable pour une ligne de crédit."
    elif score>=40: vc,vt,vb="warn","⚠️ Dossier sous conditions","Risque modéré — garanties et suivi mensuel requis."
    else: vc,vt,vb="danger","🔴 Dossier risqué","Refus recommandé ou garanties très solides requises."

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='background:white;border-radius:12px;padding:16px 24px;margin-bottom:16px;
     box-shadow:0 1px 4px rgba(0,0,0,.06);border:1px solid #e5e7eb;
     display:flex;align-items:center;justify-content:space-between'>
  <div style='display:flex;align-items:center;gap:16px'>
    <div style='font-size:32px'>📊</div>
    <div>
      <h1 style='margin:0;font-size:20px;color:#1e3a5f;font-weight:700'>Analyseur de solvabilité et de crédit</h1>
      <p style='margin:3px 0 0;color:#6b7280;font-size:12px'>12 ratios · Guide pédagogique · Simulateur d'encours</p>
    </div>
  </div>
  <div>{LOGO_HTML}</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊  Analyse financière", "📚  Guide des ratios", "💡  Simulateur d'encours"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANALYSE + RECOMMANDATIONS
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    if not has_data:
        st.markdown("""<div style='background:white;border-radius:12px;padding:40px;text-align:center;
             border:2px dashed #e5e7eb;margin-top:16px'>
          <div style='font-size:40px;margin-bottom:12px'>👈</div>
          <p style='font-size:16px;font-weight:600;color:#374151;margin:0 0 6px'>Saisissez les données dans le panneau gauche</p>
          <p style='font-size:13px;color:#9ca3af;margin:0'>Ou cliquez sur <b>Démo PEPEL</b> pour voir un exemple complet</p>
          </div>""", unsafe_allow_html=True)
    else:
        # Score banner
        crit=[r[0] for r in RATIOS if r[2]=="danger"]
        db=BADGE["danger"]; dtx=TX["danger"]
        badges="".join(f"<span style='font-size:11px;padding:3px 10px;border-radius:12px;background:{db};color:{dtx};font-weight:600'>{p}</span>" for p in crit)
        crit_html=f"<div style='margin-top:10px;display:flex;flex-wrap:wrap;gap:6px'>{badges}</div>" if crit else ""

        st.markdown(f"""
        <div style='background:white;border-radius:12px;padding:20px 24px;
             border-left:5px solid {BORDER[vc]};box-shadow:0 2px 8px rgba(0,0,0,.07);margin-bottom:20px'>
          <div style='display:flex;align-items:center;gap:16px'>
            <div style='width:60px;height:60px;border-radius:50%;background:{BORDER[vc]};
                 display:flex;align-items:center;justify-content:center;flex-shrink:0'>
              <span style='font-size:22px;font-weight:700;color:white'>{score}</span>
            </div>
            <div style='flex:1'>
              <p style='font-size:18px;font-weight:700;color:#1f2937;margin:0'>{vt}</p>
              <p style='font-size:13px;color:#6b7280;margin:4px 0 0'>{vb}</p>
            </div>
            <div style='text-align:right'>
              <p style='font-size:11px;color:#9ca3af;margin:0'>Score solvabilité</p>
              <p style='font-size:28px;font-weight:700;color:{BORDER[vc]};margin:0'>{score}<span style='font-size:14px;color:#9ca3af'>/100</span></p>
            </div>
          </div>
          {f"<p style='font-size:11px;color:#6b7280;margin:12px 0 4px;font-weight:600'>Points critiques :</p>{crit_html}" if crit else ""}
        </div>""", unsafe_allow_html=True)

        # Ratio cards
        st.markdown("#### Détail des 12 ratios")
        cols=st.columns(3)
        for i,(name,val,t,formula,threshold) in enumerate(RATIOS):
            with cols[i%3]: st.markdown(card(name,val,t,formula,threshold),unsafe_allow_html=True)

        st.markdown("---")

        # Radar + seuils
        def norm(v,lo,hi): return max(0.,min(100.,(v-lo)/(hi-lo)*100)) if math.isfinite(v) else 0.
        rv=[norm(lg,0,3),norm(li,0,0.4),norm(aut,0,1),
            norm(cov if math.isfinite(cov) else 0,0,5),norm(ret+20,0,40),
            norm(max(0,10-dnc) if (math.isfinite(dnc) and dnc>0) else 0,0,10)]
        rl=["Liq. générale","Liq. immédiate","Autonomie","Couv. intérêts","Rentabilité","Cap. remb."]
        fig=go.Figure(go.Scatterpolar(r=rv+[rv[0]],theta=rl+[rl[0]],fill="toself",
            fillcolor="rgba(30,58,95,0.12)",line=dict(color="#1e3a5f",width=2.5),
            marker=dict(size=6,color="#1e3a5f",line=dict(color="white",width=1.5))))
        fig.update_layout(polar=dict(bgcolor="white",
            radialaxis=dict(visible=True,range=[0,100],tickfont=dict(size=9,color="#9ca3af"),gridcolor="#f3f4f6"),
            angularaxis=dict(tickfont=dict(size=11,color="#374151"),gridcolor="#f3f4f6")),
            showlegend=False,margin=dict(t=30,b=30,l=30,r=30),height=340,
            paper_bgcolor="white",plot_bgcolor="white")
        cr,ct=st.columns([1,1])
        with cr:
            st.markdown("<div style='background:white;border-radius:12px;padding:12px;border:1px solid #e5e7eb'>",unsafe_allow_html=True)
            st.markdown("##### Profil de risque")
            st.plotly_chart(fig,use_container_width=True)
            st.markdown("</div>",unsafe_allow_html=True)
        with ct:
            rows=[("Liquidité générale","≥1.5","≥1.0","<1.0"),("Liquidité réduite","≥1.0","≥0.7","<0.7"),
                  ("Liquidité immédiate","≥0.3","≥0.1","<0.1"),("Autonomie financière","≥0.5","≥0.25","<0.25"),
                  ("Levier d'endettement","≤1.0","≤3.0",">3.0"),("Solvabilité globale","≥2.0","≥1.5","<1.5"),
                  ("Couverture intérêts","≥3.0","≥1.0","<1.0"),("Dettes / CAF","≤3x","≤7x",">7x"),
                  ("Rentabilité nette","≥5%","≥0%","<0%"),("Taux EBE","≥15%","≥5%","<5%")]
            tbl="<div style='background:white;border-radius:12px;padding:16px 20px;border:1px solid #e5e7eb'>"
            tbl+="<p style='font-weight:600;color:#1e3a5f;margin:0 0 10px;font-size:14px'>Seuils de référence</p>"
            tbl+="<table style='width:100%;border-collapse:collapse;font-size:12px'>"
            tbl+="<tr style='background:#f9fafb'><th style='text-align:left;padding:5px 8px;color:#6b7280;font-weight:600'>Ratio</th><th style='padding:5px 6px;color:#15803d'>🟢</th><th style='padding:5px 6px;color:#b45309'>🟡</th><th style='padding:5px 6px;color:#b91c1c'>🔴</th></tr>"
            for n,g,w,d in rows:
                tbl+=f"<tr style='border-top:1px solid #f3f4f6'><td style='padding:5px 8px;color:#374151;font-weight:500'>{n}</td><td style='padding:5px 6px;text-align:center;color:#15803d;font-weight:600'>{g}</td><td style='padding:5px 6px;text-align:center;color:#b45309;font-weight:600'>{w}</td><td style='padding:5px 6px;text-align:center;color:#b91c1c;font-weight:600'>{d}</td></tr>"
            tbl+="</table></div>"
            st.markdown(tbl,unsafe_allow_html=True)

        # ── RECOMMANDATIONS ───────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 📋 Recommandations pour l'octroi de crédit")

        # Ligne recommandée
        if score>=65 and li>=0.3:
            rec_duree,rec_delai,rec_t="30 jours","jusqu'à 15 jours","good"
            rec_txt="Profil solide. Ligne 30 jours avec délai jusqu'à 15 jours accordable."
        elif score>=65:
            rec_duree,rec_delai,rec_t="15 jours","7 jours","warn"
            rec_txt="Bon score mais liquidité immédiate faible. Préférer 15 jours, délai 7 jours."
        elif score>=40:
            rec_duree,rec_delai,rec_t="15 jours","7 jours","warn"
            rec_txt="Risque modéré. Ligne 15 jours maximum, délai 7 jours. Suivi mensuel obligatoire."
        else:
            rec_duree,rec_delai,rec_t="15 jours","0 – 7 jours","danger"
            rec_txt="Dossier risqué. Si accordé : 15 jours max, délai 0 ou 7 jours, garanties solides."

        rc1,rc2,rc3=st.columns(3)
        with rc1:
            st.markdown(f"""<div style='background:white;border-radius:10px;padding:16px;border-left:4px solid {BORDER[rec_t]};box-shadow:0 1px 3px rgba(0,0,0,.06)'>
            <p style='font-size:11px;font-weight:600;color:#6b7280;margin:0 0 4px'>LIGNE RECOMMANDÉE</p>
            <p style='font-size:20px;font-weight:700;color:{BORDER[rec_t]};margin:0 0 2px'>{rec_duree}</p>
            <p style='font-size:12px;color:#6b7280;margin:0'>Délai : {rec_delai}</p>
            </div>""", unsafe_allow_html=True)
        with rc2:
            pd_pct = 3 if score>=65 else 10 if score>=40 else 25
            st.markdown(f"""<div style='background:white;border-radius:10px;padding:16px;border-left:4px solid #6366f1;box-shadow:0 1px 3px rgba(0,0,0,.06)'>
            <p style='font-size:11px;font-weight:600;color:#6b7280;margin:0 0 4px'>PROBABILITÉ DE DÉFAUT ESTIMÉE</p>
            <p style='font-size:20px;font-weight:700;color:#4f46e5;margin:0 0 2px'>{pd_pct} %</p>
            <p style='font-size:12px;color:#6b7280;margin:0'>Basée sur le score {score}/100</p>
            </div>""", unsafe_allow_html=True)
        with rc3:
            enc_ref=10000
            dep_base=0.0 if score>=65 else 0.15 if score>=40 else 0.25
            dep_adj=0.0
            if li<0.1: dep_adj+=0.10
            if caf<0: dep_adj+=0.10
            if math.isfinite(cov) and cov<1: dep_adj+=0.05
            dep_rate=min(0.50,dep_base+dep_adj)
            dep_ref=round(enc_ref*dep_rate,-1)
            dep_txt=f"≈ {dep_rate*100:.0f}% de l'encours" if dep_rate>0 else "Non requis"
            dep_col="#1e3a5f" if dep_rate==0 else BORDER["warn"] if dep_rate<=0.15 else BORDER["danger"]
            st.markdown(f"""<div style='background:white;border-radius:10px;padding:16px;border-left:4px solid {dep_col};box-shadow:0 1px 3px rgba(0,0,0,.06)'>
            <p style='font-size:11px;font-weight:600;color:#6b7280;margin:0 0 4px'>DÉPÔT DE GARANTIE</p>
            <p style='font-size:20px;font-weight:700;color:{dep_col};margin:0 0 2px'>{dep_txt}</p>
            <p style='font-size:12px;color:#6b7280;margin:0'>Calculer montant → onglet Simulateur</p>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"<div style='background:{BG[rec_t]};border-radius:8px;padding:12px 16px;margin:12px 0;border-left:4px solid {BORDER[rec_t]}'><p style='font-size:13px;color:{TX[rec_t]};margin:0'>{rec_txt}</p></div>",unsafe_allow_html=True)

        # Points de vigilance spécifiques
        vigilance=[]
        if li<0.1: vigilance.append(("danger","Liquidité immédiate critique","Vérifier les relevés bancaires des 30 derniers jours avant toute décision. Risque de refus de prélèvement."))
        if math.isfinite(cov) and cov<1.0: vigilance.append(("danger","Couverture des intérêts < 1","L'EBE ne couvre pas les charges financières. Structure de financement intenable à moyen terme."))
        if caf<0: vigilance.append(("danger","CAF négative","L'entreprise consomme du cash chaque année. Risque de dégradation continue de la trésorerie."))
        if math.isfinite(dnc) and dnc>7: vigilance.append(("danger","Désendettement quasi-impossible","Dettes financières > 7 ans de CAF. Dépendance structurelle aux créanciers."))
        if score<40 and li>0.1: vigilance.append(("warn","Trésorerie disponible mais structure fragile","La trésorerie couvre l'encours à court terme mais la situation financière globale est préoccupante."))
        if score>=40 and caf<50000 and caf>0: vigilance.append(("warn","CAF faible","La capacité d'autofinancement est insuffisante. Un exercice difficile peut la faire basculer en négatif."))
        if score>=65: vigilance.append(("good","Profil globalement sain","Continuer à surveiller l'évolution de la trésorerie et du résultat annuellement."))

        if vigilance:
            st.markdown("**Points de vigilance :**")
            for t,titre,txt in vigilance:
                st.markdown(f"<div style='background:{BG[t]};border-radius:8px;padding:10px 14px;margin-bottom:8px;border-left:3px solid {BORDER[t]}'><p style='font-size:12px;font-weight:600;color:{TX[t]};margin:0 0 3px'>{titre}</p><p style='font-size:12px;color:{TX[t]};margin:0;opacity:.9'>{txt}</p></div>",unsafe_allow_html=True)

        # ── EXPORT PDF ────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 📄 Export du rapport")
        ep1, ep2 = st.columns([3, 1])
        with ep1:
            st.markdown(f"""<div style='background:white;border-radius:10px;padding:14px 18px;border:1px solid #e5e7eb'>
            <p style='font-size:13px;font-weight:600;color:#1e3a5f;margin:0 0 4px'>Rapport PDF complet</p>
            <p style='font-size:12px;color:#6b7280;margin:0'>Inclut : score · 12 ratios · profil de risque · recommandations{" · simulateur · dépôt de garantie" if has_data else ""}</p>
            </div>""", unsafe_allow_html=True)
        with ep2:
            from datetime import datetime
            # Gather simulator vars (use defaults if not set)
            _montant  = st.session_state.get("_sim_montant", 10000.0)
            _duree    = st.session_state.get("_sim_duree",   15)
            _delai    = st.session_state.get("_sim_delai",   0)
            _enc      = _montant + (_montant/_duree)*_delai
            _dep_min  = st.session_state.get("_dep_min",  0.0)
            _dep_rec  = st.session_state.get("_dep_rec",  0.0)
            _dep_max  = st.session_state.get("_dep_max",  0.0)
            _taux     = st.session_state.get("_sim_taux", 0.0)
            _renouvellements = 24 if _duree==15 else 12
            _rev_trans  = _montant*_taux/100 if _taux>0 else 0
            _rev_annuel = _rev_trans*_renouvellements
            _pd         = 3 if score>=65 else 10 if score>=40 else 25
            _profit_net = _rev_annuel - (_pd/100*_enc)
            _has_sim    = st.session_state.get("_sim_configured", False)

            try:
                pdf_bytes = generate_pdf_report(
                    client_name=st.session_state.get("client_name",""),
                    score=score, vc=vc, vt=vt, vb=vb,
                    RATIOS=RATIOS, vigilance=vigilance,
                    rec_duree=rec_duree, rec_delai=rec_delai,
                    rv=rv, rl=rl,
                    has_sim=_has_sim,
                    montant=_montant, duree=_duree, delai=_delai, enc=_enc,
                    dep_min=_dep_min, dep_rec=_dep_rec, dep_max=_dep_max,
                    taux=_taux, rev_trans=_rev_trans, rev_annuel=_rev_annuel,
                    profit_net=_profit_net, renouvellements=_renouvellements,
                )
                fname = f"rapport_{(st.session_state.get('client_name','client') or 'client').replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                st.write("")
                st.download_button("📥 Télécharger PDF", data=pdf_bytes,
                                   file_name=fname, mime="application/pdf",
                                   use_container_width=True, type="primary")
            except Exception as ex:
                st.error(f"Erreur PDF : {ex}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — GUIDE
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(f"""<div style='background:white;border-radius:12px;padding:20px 24px;margin-bottom:20px;border:1px solid #e5e7eb;display:flex;align-items:center;justify-content:space-between'>
      <div><h2 style='margin:0 0 4px;color:#1e3a5f;font-size:18px'>📚 Guide pédagogique des ratios</h2>
      <p style='margin:0;color:#6b7280;font-size:13px'>Ce que ça mesure · Comment calculer · Comment interpréter</p></div>
      <div>{LOGO_HTML}</div></div>""", unsafe_allow_html=True)
    for i,r in enumerate(GUIDE):
        with st.expander(f"{r['emoji']}  {r['name']}",expanded=(i==0)):
            c1,c2=st.columns([1,1])
            with c1:
                st.markdown(f"**🎯 Ce que ça mesure**\n\n*{r['definition']}*")
                st.markdown("**🧮 Formule**")
                if r['op']=='=':
                    st.markdown(f"<div style='background:#eff6ff;padding:8px 16px;border-radius:7px;font-weight:600;font-size:13px;color:#1e40af;display:inline-block'>{r['num']}</div>",unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:6px 0'><div style='background:#eff6ff;padding:8px 14px;border-radius:7px;font-weight:600;font-size:13px;color:#1e40af'>{r['num']}</div><div style='font-size:20px;color:#6b7280;font-weight:700'>{r['op']}</div><div style='background:#eff6ff;padding:8px 14px;border-radius:7px;font-weight:600;font-size:13px;color:#1e40af'>{r['den']}</div></div>",unsafe_allow_html=True)
                st.markdown(f"💡 *{r['astuce']}*")
            with c2:
                st.markdown("**📏 Interprétation**")
                for label,t,explication in r['seuils']:
                    st.markdown(f"<div style='background:{BG[t]};border-left:4px solid {BORDER[t]};border-radius:0 7px 7px 0;padding:10px 14px;margin-bottom:8px'><div style='font-weight:700;color:{TX[t]};font-size:13px;margin-bottom:3px'>{label}</div><div style='font-size:12px;color:{TX[t]};opacity:.9'>{explication}</div></div>",unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SIMULATEUR
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown(f"""<div style='background:white;border-radius:12px;padding:18px 24px;margin-bottom:16px;border:1px solid #e5e7eb;display:flex;align-items:center;justify-content:space-between'>
      <div><h2 style='margin:0 0 4px;color:#1e3a5f;font-size:18px'>💡 Simulateur d'encours — Lignes de crédit</h2>
      <p style='margin:0;color:#6b7280;font-size:13px'>Exposition réelle · Rentabilité · Dépôt de garantie</p></div>
      <div>{LOGO_HTML}</div></div>""", unsafe_allow_html=True)

    # Inputs principaux
    st.markdown("**Paramètres de la ligne de crédit**")
    c1,c2,c3=st.columns(3)
    with c1: montant=st.number_input("💰 Montant de la ligne €",min_value=0.0,value=10_000.0,step=500.0,format="%0.0f",help="Montant total accordé sur la période.")
    with c2: duree=st.selectbox("📅 Durée",[15,30],format_func=lambda x:f"{x} jours")
    with c3: delai=st.selectbox("⏳ Délai de paiement",[0,7,15,30],format_func=lambda x:f"{x} jour{'s' if x>1 else ''}" if x>0 else "0 jour (immédiat)")

    st.markdown("**Paramètres optionnels — Rentabilité**")
    co1,co2=st.columns(2)
    with co1:
        taux=st.number_input("📈 Taux d'intérêt par ligne (%)",min_value=0.0,max_value=100.0,value=0.0,step=0.1,format="%0.2f",
            help="Taux annuel facturé au client. Permet de calculer la rentabilité et le délai de couverture du risque.")
    with co2:
        encours_max=st.number_input("🎯 Encours autorisé maximum € (optionnel)",min_value=0.0,value=0.0,step=500.0,format="%0.0f",
            help="Si défini, le simulateur indiquera si l'encours réel dépasse ce plafond et ajustera le dépôt de garantie.")

    # Calculs simulateur
    conso_j=montant/duree if duree>0 else 0
    conso_d=conso_j*delai
    enc=montant+conso_d
    dtot=duree+delai
    depasse_max=(encours_max>0 and enc>encours_max)

    # Timeline
    fig2=go.Figure()
    fig2.update_layout(paper_bgcolor="white",plot_bgcolor="white",height=240,
        margin=dict(l=20,r=30,t=20,b=30),
        xaxis=dict(visible=False,range=[-0.5,dtot+1.2]),
        yaxis=dict(visible=False,range=[0,1.1]),showlegend=False)
    fig2.add_shape(type="rect",x0=0,x1=duree,y0=0.25,y1=0.75,fillcolor="rgba(253,186,116,0.25)",line_color="rgba(217,119,6,0.4)",line_width=1.5)
    if delai>0:
        fig2.add_shape(type="rect",x0=duree,x1=dtot,y0=0.25,y1=0.75,fillcolor="rgba(134,239,172,0.25)",line_color="rgba(22,163,74,0.4)",line_width=1.5)
    fig2.add_shape(type="line",x0=0,x1=dtot+0.5,y0=0.5,y1=0.5,line=dict(color="#374151",width=2.5))
    def pt(x,col): fig2.add_scatter(x=[x],y=[0.5],mode="markers",showlegend=False,marker=dict(size=14,color=col,line=dict(color="white",width=2.5)))
    pt(0,"#1e3a5f"); pt(duree,"#dc2626")
    if delai>0: pt(dtot,"#16a34a")
    fig2.add_annotation(x=0,y=0.82,text=f"<b>J+0</b>",font=dict(size=11,color="#1e3a5f"),showarrow=False,bgcolor="white",bordercolor="#1e3a5f",borderwidth=1,borderpad=3)
    fig2.add_annotation(x=0,y=0.15,text="Début",font=dict(size=10,color="#6b7280"),showarrow=False)
    fig2.add_annotation(x=duree,y=0.82,text=f"<b>J+{duree}</b>",font=dict(size=11,color="#dc2626"),showarrow=False,bgcolor="white",bordercolor="#dc2626",borderwidth=1,borderpad=3)
    fig2.add_annotation(x=duree,y=0.15,text=f"Facture {montant:,.0f}€",font=dict(size=10,color="#dc2626"),showarrow=False)
    if delai>0:
        fig2.add_annotation(x=dtot,y=0.82,text=f"<b>J+{dtot}</b>",font=dict(size=11,color="#16a34a"),showarrow=False,bgcolor="white",bordercolor="#16a34a",borderwidth=1,borderpad=3)
        fig2.add_annotation(x=dtot,y=0.15,text="Prélèvement",font=dict(size=10,color="#16a34a"),showarrow=False)
    if duree>=4: fig2.add_annotation(x=duree/2,y=0.65,text=f"Crédit · {duree}j",font=dict(size=11,color="#92400e"),showarrow=False,bgcolor="rgba(255,255,255,.85)")
    if delai>=4: fig2.add_annotation(x=duree+delai/2,y=0.65,text=f"Délai · {delai}j",font=dict(size=11,color="#166534"),showarrow=False,bgcolor="rgba(255,255,255,.85)")
    enc_color="#dc2626" if depasse_max else "#1e3a5f"
    fig2.add_annotation(x=dtot/2,y=0.04,text=f"⚠️ Encours exposé : <b>{enc:,.0f} €</b> ({dtot}j d'exposition)" + (f" — ⛔ DÉPASSE le max de {encours_max:,.0f}€" if depasse_max else ""),
        font=dict(size=11,color=enc_color),showarrow=False,bgcolor="rgba(239,246,255,.95)",bordercolor="#93c5fd",borderwidth=1,borderpad=5)

    st.markdown("<div style='background:white;border-radius:12px;padding:14px;border:1px solid #e5e7eb;margin-bottom:14px'>",unsafe_allow_html=True)
    st.plotly_chart(fig2,use_container_width=True)
    st.markdown("</div>",unsafe_allow_html=True)

    # Métriques principales
    m1,m2,m3,m4=st.columns(4)
    def mcrd(num,title,formula,value,color="#1e3a5f"):
        return f"""<div style='background:white;border-radius:10px;padding:14px;text-align:center;
            border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,.05)'>
            <p style='font-size:18px;font-weight:700;color:#9ca3af;margin:0 0 3px'>{num}</p>
            <p style='font-size:11px;color:#6b7280;margin:0 0 1px;font-weight:600'>{title}</p>
            <p style='font-size:10px;color:#9ca3af;margin:0 0 6px'>{formula}</p>
            <p style='font-size:22px;font-weight:700;color:{color};margin:0'>{value}</p></div>"""
    with m1: st.markdown(mcrd("①","Conso/jour",f"{montant:,.0f}÷{duree}j",f"{conso_j:,.2f}€/j"),unsafe_allow_html=True)
    with m2: st.markdown(mcrd("②","Expo délai",f"{conso_j:,.2f}×{delai}j",f"{conso_d:,.0f}€","#d97706"),unsafe_allow_html=True)
    with m3: st.markdown(mcrd("③","Encours total",f"{montant:,.0f}+{conso_d:,.0f}",f"{enc:,.0f}€","#dc2626"),unsafe_allow_html=True)
    with m4: st.markdown(mcrd("④","Durée exposition",f"{duree}+{delai}j",f"{dtot}j","#16a34a"),unsafe_allow_html=True)

    st.markdown("---")

    # ── RENTABILITÉ ───────────────────────────────────────────────────────────
    if taux>0:
        st.markdown("#### 📈 Rentabilité sur le dossier")

        # Taux PÉRIODIQUE (par ligne émise), pas annuel
        # Ex: 10 000€ × 1% = 100€ par ligne de 15j
        renouvellements = 24 if duree == 15 else 12   # lignes émises par an
        rev_trans   = montant * taux / 100             # revenu par ligne
        rev_annuel  = rev_trans * renouvellements      # revenu annuel total
        rev_mensuel = rev_annuel / 12
        rendement_annuel = (rev_annuel / montant) * 100  # rendement sur capital déployé
        rendement_enc    = (rev_annuel / enc) * 100 if enc > 0 else 0

        pd_pct  = 3 if score>=65 else 10 if score>=40 else (25 if has_data else 10)
        cout_risque = pd_pct / 100 * enc
        profit_net  = rev_annuel - cout_risque

        if rev_trans > 0:
            trans_be = cout_risque / rev_trans
            jours_be = trans_be * duree
        else:
            trans_be = float('inf'); jours_be = float('inf')

        r1,r2,r3,r4=st.columns(4)
        with r1:
            st.markdown(mcrd("💶","Revenu par ligne",f"{montant:,.0f}€ × {taux:.2f}%",f"{rev_trans:,.2f}€","#1e3a5f"),unsafe_allow_html=True)
        with r2:
            st.markdown(mcrd("📅","Revenu mensuel",f"{rev_trans:,.2f}€ × {renouvellements}/12",f"{rev_mensuel:,.0f}€/mois","#1e3a5f"),unsafe_allow_html=True)
        with r3:
            st.markdown(mcrd("📆","Revenu annuel",f"{rev_trans:,.2f}€ × {renouvellements} lignes/an",f"{rev_annuel:,.0f}€/an","#16a34a"),unsafe_allow_html=True)
        with r4:
            r_col="#16a34a" if rendement_enc >= taux else "#d97706"
            st.markdown(mcrd("📊","Rendement/encours",f"Rev. annuel ÷ {enc:,.0f}€",f"{rendement_enc:.1f}%",r_col),unsafe_allow_html=True)

        # Info logique calcul
        st.markdown(f"""<div style='background:#eff6ff;border-radius:8px;padding:10px 16px;margin-bottom:12px;border-left:3px solid #3b82f6'>
        <p style='font-size:12px;color:#1e40af;margin:0'>
        <b>Logique de calcul :</b> {montant:,.0f}€ × {taux:.2f}% = <b>{rev_trans:,.2f}€</b> par ligne ×
        <b>{renouvellements} lignes/an</b> (ligne {duree}j → {renouvellements} renouvellements/an) =
        <b>{rev_annuel:,.0f}€/an</b>
        </p></div>""", unsafe_allow_html=True)

        rk1,rk2=st.columns(2)
        with rk1:
            prof_col="#16a34a" if profit_net>0 else "#dc2626"
            rk_html = (f"<div style='background:white;border-radius:10px;padding:16px;border-left:4px solid {prof_col};border:1px solid #e5e7eb'>"
                       f"<p style='font-size:12px;font-weight:600;color:#6b7280;margin:0 0 8px'>Analyse risque / rendement annuel</p>"
                       f"<div style='display:flex;justify-content:space-between;margin-bottom:6px'>"
                       f"<span style='font-size:12px;color:#374151'>Revenu annuel brut</span>"
                       f"<span style='font-size:12px;font-weight:600;color:#16a34a'>+{rev_annuel:,.0f} €</span></div>"
                       f"<div style='display:flex;justify-content:space-between;margin-bottom:6px'>"
                       f"<span style='font-size:12px;color:#374151'>Coût du risque (PD {pd_pct}% × {enc:,.0f}€)</span>"
                       f"<span style='font-size:12px;font-weight:600;color:#dc2626'>−{cout_risque:,.0f} €</span></div>"
                       f"<div style='border-top:1px solid #e5e7eb;padding-top:8px;display:flex;justify-content:space-between'>"
                       f"<span style='font-size:13px;font-weight:600;color:#374151'>Profit net estimé</span>"
                       f"<span style='font-size:16px;font-weight:700;color:{prof_col}'>{'+ ' if profit_net>=0 else ''}{profit_net:,.0f} €</span></div>"
                       f"</div>")
            st.markdown(rk_html, unsafe_allow_html=True)
        with rk2:
            if math.isfinite(jours_be):
                be_ans = jours_be / 365
                be_col = "#16a34a" if be_ans < 2 else "#d97706" if be_ans < 5 else "#dc2626"
                be_txt = f"{int(round(jours_be))} jours ({be_ans:.1f} ans)"
                be_sub = f"{int(round(trans_be))} renouvellements de {duree}j"
            else:
                be_col = "#dc2626"; be_txt = "∞"; be_sub = "Taux insuffisant"
            rk2_html = (f"<div style='background:white;border-radius:10px;padding:16px;border-left:4px solid {be_col};border:1px solid #e5e7eb'>"
                        f"<p style='font-size:12px;font-weight:600;color:#6b7280;margin:0 0 8px'>Délai de couverture du risque</p>"
                        f"<p style='font-size:11px;color:#9ca3af;margin:0 0 4px'>Nombre de renouvellements pour couvrir la perte potentielle</p>"
                        f"<p style='font-size:20px;font-weight:700;color:{be_col};margin:0 0 4px'>{be_txt}</p>"
                        f"<p style='font-size:11px;color:#9ca3af;margin:0'>{be_sub}</p>"
                        f"<p style='font-size:11px;color:#6b7280;margin-top:6px'>PD estimée : {pd_pct}% · Perte potentielle : {cout_risque:,.0f}€</p>"
                        f"</div>")
            st.markdown(rk2_html, unsafe_allow_html=True)
    else:
        st.info("💡 Renseignez le **taux d'intérêt par ligne** (ex: 1%) pour voir l'analyse de rentabilité.")

    st.markdown("---")

    # ── DÉPÔT DE GARANTIE ─────────────────────────────────────────────────────
    st.markdown("#### 🔐 Dépôt de garantie")

    # Calcul fourchette min / recommandé / max avec justification
    # Base selon score
    if score >= 65:
        base_min, base_rec, base_max = 0.0,  0.0,  0.05
        base_lbl = f"Score solide ({score}/100) → pas de dépôt requis en base"
    elif score >= 40:
        base_min, base_rec, base_max = 0.10, 0.15, 0.20
        base_lbl = f"Score modéré ({score}/100) → base 10 – 20% de l'encours"
    else:
        base_min, base_rec, base_max = 0.20, 0.25, 0.35
        base_lbl = f"Score risqué ({score}/100) → base 20 – 35% de l'encours"

    # Ajustements par facteur de risque
    adj_items = []   # (label, raison, +min, +rec, +max)
    if has_data:
        if li < 0.1:
            adj_items.append(("🔴 Liquidité immédiate critique",
                f"Trésorerie couvre seulement {li:.1%} des dettes CT", 0.05, 0.10, 0.15))
        elif li < 0.3:
            adj_items.append(("🟡 Liquidité immédiate faible",
                f"Trésorerie limitée ({li:.2f})", 0.02, 0.05, 0.08))

        if caf < 0:
            adj_items.append(("🔴 CAF négative",
                f"Perte de cash de {fmt_eur(abs(caf))}/an — risque de dégradation continue", 0.05, 0.10, 0.15))
        elif 0 <= caf < 50000:
            adj_items.append(("🟡 CAF quasi-nulle",
                f"Autofinancement insuffisant ({fmt_eur(caf)}/an)", 0.02, 0.05, 0.08))

        if math.isfinite(cov) and cov < 1.0:
            adj_items.append(("🔴 Couverture intérêts < 1",
                f"EBE insuffisant pour payer les intérêts (ratio : {fmt_x(cov)})", 0.03, 0.05, 0.08))

        if math.isfinite(dnc) and dnc > 7:
            adj_items.append(("🟡 Désendettement > 7 ans",
                f"Dettes = {fmt_x(dnc,1)}x la CAF — structure très lourde", 0.02, 0.05, 0.08))

    excedent = max(0, enc - encours_max) if encours_max > 0 else 0
    if excedent > 0:
        adj_items.append(("⛔ Dépassement encours autorisé",
            f"Encours {enc:,.0f}€ > max {encours_max:,.0f}€ (excédent {excedent:,.0f}€)", 0.0, excedent * 0.5 / enc, excedent * 0.8 / enc))

    # Totaux
    total_min = min(0.50, base_min + sum(a[2] for a in adj_items))
    total_rec = min(0.55, base_rec + sum(a[3] for a in adj_items))
    total_max = min(0.60, base_max + sum(a[4] for a in adj_items))

    dep_min = max(0, round(enc * total_min / 100) * 100)
    dep_rec = max(0, round(enc * total_rec / 100) * 100)
    dep_max = max(0, round(enc * total_max / 100) * 100)
    enc_net = enc - dep_rec
    dg_col = BORDER["good"] if total_rec == 0 else BORDER["warn"] if total_rec <= 0.20 else BORDER["danger"]

    # Save for PDF export
    st.session_state["_sim_montant"]    = montant
    st.session_state["_sim_duree"]      = duree
    st.session_state["_sim_delai"]      = delai
    st.session_state["_sim_taux"]       = taux
    st.session_state["_dep_min"]        = dep_min
    st.session_state["_dep_rec"]        = dep_rec
    st.session_state["_dep_max"]        = dep_max
    st.session_state["_sim_configured"] = True

    dg1, dg2 = st.columns([3, 2])

    with dg1:
        # Fourchette visuelle
        html = f"""<div style='background:white;border-radius:12px;padding:22px;border-left:5px solid {dg_col};box-shadow:0 1px 4px rgba(0,0,0,.07)'>
<p style='font-size:11px;font-weight:700;color:#6b7280;margin:0 0 14px;letter-spacing:.06em'>FOURCHETTE DE DÉPÔT RECOMMANDÉE</p>"""

        if total_rec == 0:
            html += f"<p style='font-size:28px;font-weight:700;color:{BORDER['good']};margin:0 0 6px'>Aucun dépôt requis</p>"
            html += f"<p style='font-size:12px;color:#6b7280;margin:0'>{base_lbl}</p>"
        else:
            def bar(pct, total_enc, color, label):
                amt = max(0, round(total_enc * pct / 100) * 100)
                bar_w = min(98, pct * 100 / max(total_max, 0.01) if total_max > 0 else 0)
                return (f"<div style='margin-bottom:12px'>"
                        f"<div style='display:flex;justify-content:space-between;margin-bottom:4px'>"
                        f"<span style='font-size:11px;color:#6b7280;font-weight:600'>{label}</span>"
                        f"<span style='font-size:13px;font-weight:700;color:{color}'>{pct*100:.0f}% → {amt:,.0f} €</span>"
                        f"</div>"
                        f"<div style='background:#f3f4f6;border-radius:4px;height:8px'>"
                        f"<div style='background:{color};border-radius:4px;height:8px;width:{bar_w:.0f}%;opacity:.7'></div>"
                        f"</div></div>")

            html += bar(total_min, enc, "#16a34a", "Minimum acceptable")
            html += bar(total_rec, enc, "#d97706", "▶ Recommandé")
            html += bar(total_max, enc, "#dc2626", "Maximum justifiable")
            html += f"<p style='font-size:11px;color:#9ca3af;margin:4px 0 14px'>{base_lbl}</p>"

        # Justification ligne par ligne
        if adj_items:
            html += "<div style='border-top:1px solid #f3f4f6;padding-top:12px;margin-top:4px'>"
            html += "<p style='font-size:11px;font-weight:700;color:#374151;margin:0 0 8px'>Facteurs de risque pris en compte :</p>"
            for label, raison, amin, arec, amax in adj_items:
                ac_str = f"+{arec*100:.0f}% recommandé"
                html += (f"<div style='margin-bottom:8px;padding:8px 12px;background:#fafafa;border-radius:6px;border-left:3px solid #e5e7eb'>"
                         f"<div style='display:flex;justify-content:space-between;align-items:flex-start'>"
                         f"<span style='font-size:12px;font-weight:600;color:#374151'>{label}</span>"
                         f"<span style='font-size:11px;color:#d97706;font-weight:600;white-space:nowrap;margin-left:8px'>{ac_str}</span>"
                         f"</div>"
                         f"<p style='font-size:11px;color:#6b7280;margin:3px 0 0'>{raison}</p>"
                         f"</div>")
            html += "</div>"

        if not has_data:
            html += "<p style='font-size:11px;color:#9ca3af;margin-top:10px'>💡 Saisissez les données financières pour affiner ce calcul.</p>"

        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    with dg2:
        rows_dg = [
            ("Encours total exposé", f"{enc:,.0f} €", "#374151"),
            ("Dépôt minimum", f"{dep_min:,.0f} €", BORDER["good"]),
            ("Dépôt recommandé", f"{dep_rec:,.0f} €", dg_col),
            ("Dépôt maximum", f"{dep_max:,.0f} €", BORDER["danger"]),
            ("Encours net (après dépôt rec.)", f"{enc_net:,.0f} €", "#1e3a5f"),
        ]
        if encours_max > 0:
            rows_dg.insert(1, ("Encours autorisé max", f"{encours_max:,.0f} €", "#6b7280"))

        tbl2 = "<div style='background:white;border-radius:12px;padding:20px;border:1px solid #e5e7eb;height:100%'>"
        tbl2 += "<p style='font-size:11px;font-weight:700;color:#6b7280;margin:0 0 12px;letter-spacing:.06em'>RÉSUMÉ DE L'EXPOSITION</p>"
        for i, (label, val, col) in enumerate(rows_dg):
            sep = "border-top:1px solid #f3f4f6;" if i > 0 else ""
            tbl2 += (f"<div style='display:flex;justify-content:space-between;padding:9px 0;{sep}'>"
                     f"<span style='font-size:12px;color:#6b7280'>{label}</span>"
                     f"<span style='font-size:13px;font-weight:700;color:{col}'>{val}</span>"
                     f"</div>")
        tbl2 += "</div>"
        st.markdown(tbl2, unsafe_allow_html=True)

    st.markdown("---")
    # Tableau comparatif 8 configs
    st.markdown("#### Comparaison des 8 configurations")
    configs=[(15,0,"Ligne 15j — immédiat"),(15,7,"Ligne 15j — délai 7j"),(15,15,"Ligne 15j — délai 15j"),
             (15,30,"Ligne 15j — délai 30j"),(30,0,"Ligne 30j — immédiat"),(30,7,"Ligne 30j — délai 7j"),
             (30,15,"Ligne 30j — délai 15j"),(30,30,"Ligne 30j — délai 30j")]
    col_cfg=st.columns(2)
    for ci,(d,p,lbl) in enumerate(configs):
        e=montant+(montant/d)*p; r_e=e/montant
        t_r="good" if r_e<1.3 else "warn" if r_e<1.6 else "danger"
        lbl_r={"good":"Faible","warn":"Modéré","danger":"Élevé"}[t_r]
        active=(d==duree and p==delai)
        bg2="white" if not active else BG[t_r]
        border2=f"2px solid {BORDER[t_r]}" if active else "1px solid #e5e7eb"
        with col_cfg[ci%2]:
            st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:center;padding:8px 14px;border-radius:8px;border:{border2};background:{bg2};margin-bottom:6px'><span style='font-size:12px;color:#374151;font-weight:{'700' if active else '400'}'>{'▶ ' if active else ''}{lbl}</span><span style='font-size:12px;font-weight:600;color:{BORDER[t_r]}'>{e:,.0f}€ — {lbl_r}</span></div>",unsafe_allow_html=True)

st.markdown("<p style='text-align:center;color:#d1d5db;font-size:11px;margin-top:20px'>Piana · Outil d'aide à la décision · Ne se substitue pas à une analyse approfondie</p>",unsafe_allow_html=True)
