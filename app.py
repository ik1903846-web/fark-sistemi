import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime

from fark_engine import (FARKEngine, karar_label, karar_emoji, KARAR_RENK, KARAR_BG,
                          read_excel_bytes, donem_from_filename, fmt_milyon, safe_float)

st.set_page_config(page_title="FARK Sistemi", page_icon="\U0001f4ca", layout="wide",
                   initial_sidebar_state="expanded")

# ─── GLOBAL CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Genel ── */
[data-testid="stAppViewContainer"] { background: #0F1923; }
[data-testid="stSidebar"] { background: #111D2B; border-right: 1px solid #1E3448; }
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
section.main > div { padding-top: 1rem; }
h1,h2,h3 { color: #E2E8F0 !important; }
p, li, label { color: #CBD5E1 !important; }

/* ── Sidebar logo ── */
.sb-logo { font-size:20px; font-weight:800; color:#38BDF8 !important;
  letter-spacing:1px; padding:8px 0 4px 0; }
.sb-sub  { font-size:11px; color:#64748B !important; margin-bottom:12px; }
.sb-stat { background:#1A2D42; border-radius:8px; padding:10px 14px; margin:6px 0;
  border-left:3px solid #38BDF8; }
.sb-stat-label { font-size:10px; color:#64748B !important; text-transform:uppercase;
  letter-spacing:.5px; }
.sb-stat-val { font-size:16px; font-weight:700; color:#E2E8F0 !important; }

/* ── Page header ── */
.page-header { background: linear-gradient(135deg, #0F2942 0%, #1A3F6B 100%);
  border: 1px solid #1E4D7A; border-radius:12px; padding:20px 28px;
  margin-bottom:24px; }
.page-header h1 { margin:0; font-size:22px; color:#E2E8F0 !important; }
.page-header p  { margin:4px 0 0 0; color:#94A3B8 !important; font-size:13px; }

/* ── Metrik kartlar ── */
.metric-row { display:flex; gap:12px; margin-bottom:20px; }
.metric-card { flex:1; background:#131F2E; border:1px solid #1E3448;
  border-radius:10px; padding:14px 18px; text-align:center; }
.metric-card .mc-num { font-size:28px; font-weight:800; line-height:1; }
.metric-card .mc-lbl { font-size:11px; color:#64748B; margin-top:4px; text-transform:uppercase; letter-spacing:.5px; }
.mc-green { color:#4ADE80; border-top:3px solid #4ADE80; }
.mc-yellow { color:#FCD34D; border-top:3px solid #FCD34D; }
.mc-orange { color:#FB923C; border-top:3px solid #FB923C; }
.mc-blue   { color:#38BDF8; border-top:3px solid #38BDF8; }
.mc-red    { color:#F87171; border-top:3px solid #F87171; }

/* ── Hisse tablosu başlık satırı ── */
.tbl-header { display:grid; grid-template-columns:70px 1fr 90px 130px 100px 100px 80px 50px;
  gap:8px; padding:8px 14px; background:#0D1926;
  border-radius:8px 8px 0 0; border-bottom:1px solid #1E3448;
  font-size:10px; font-weight:700; text-transform:uppercase;
  letter-spacing:.5px; color:#475569; }

/* ── Hisse satırı ── */
.hisse-row { display:grid; grid-template-columns:70px 1fr 90px 130px 100px 100px 80px 50px;
  gap:8px; padding:10px 14px; background:#131F2E;
  border-bottom:1px solid #0F1923; transition: background .15s; }
.hisse-row:hover { background:#1A2D42; }
.hisse-row .kod { font-weight:800; font-size:14px; color:#38BDF8; }
.hisse-row .sek { font-size:11px; color:#64748B; line-height:1.4; }
.hisse-row .abcd{ font-size:11px; color:#94A3B8; }
.hisse-row .val  { font-size:12px; color:#CBD5E1; }
.hisse-row .oran-hi { font-size:12px; color:#4ADE80; font-weight:700; }
.hisse-row .oran-lo { font-size:12px; color:#94A3B8; }

/* ── Karar badge ── */
.badge-guclu  { background:#14532D; color:#4ADE80; padding:3px 10px;
  border-radius:20px; font-size:11px; font-weight:700; border:1px solid #166534; }
.badge-pot    { background:#422006; color:#FCD34D; padding:3px 10px;
  border-radius:20px; font-size:11px; font-weight:700; border:1px solid #92400E; }
.badge-zayif  { background:#431407; color:#FB923C; padding:3px 10px;
  border-radius:20px; font-size:11px; font-weight:700; border:1px solid #9A3412; }
.badge-elen   { background:#450A0A; color:#F87171; padding:3px 10px;
  border-radius:20px; font-size:11px; font-weight:700; border:1px solid #991B1B; }

/* ── Bozulma / temiz kutu ── */
.boz-card { background:#1C0A0A; border:1px solid #7F1D1D;
  border-left:4px solid #EF4444; border-radius:8px; padding:12px 16px; margin:6px 0; }
.tmz-card { background:#0A1C0F; border:1px solid #166534;
  border-left:4px solid #4ADE80; border-radius:8px; padding:10px 16px; margin:4px 0; }

/* ── Uploader ── */
[data-testid="stFileUploader"] { background:#131F2E; border-radius:8px;
  border:1px dashed #1E3448; padding:8px; }
[data-testid="stFileUploader"] * { color:#94A3B8 !important; }

/* ── Buton ── */
[data-testid="stButton"] button { background:#1A3F6B; color:#E2E8F0;
  border:1px solid #2563EB; border-radius:6px; font-size:13px; }
[data-testid="stButton"] button:hover { background:#2563EB; }
button[kind="primary"] { background:#2563EB !important; border:none !important; }

/* ── Multiselect / selectbox ── */
[data-testid="stMultiSelect"] > div,
[data-testid="stSelectbox"] > div > div { background:#131F2E !important;
  border:1px solid #1E3448 !important; color:#CBD5E1 !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { background:#131F2E; border-radius:8px; }
[data-testid="stDataFrame"] table { font-size:12px !important; background:#131F2E !important; }
[data-testid="stDataFrame"] th { background:#0D1926 !important; color:#64748B !important; }
[data-testid="stDataFrame"] td { color:#CBD5E1 !important; }

/* ── Expander ── */
[data-testid="stExpander"] { background:#131F2E; border:1px solid #1E3448;
  border-radius:8px; }
[data-testid="stExpander"] summary { color:#94A3B8 !important; }

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] { color:#64748B !important; font-size:13px; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color:#38BDF8 !important;
  border-bottom-color:#38BDF8 !important; }
[data-testid="stTabs"] [role="tabpanel"] { background:#131F2E;
  border:1px solid #1E3448; border-radius:0 8px 8px 8px; padding:16px; }

/* ── Success/Info/Warning ── */
[data-testid="stAlert"] { border-radius:8px; }

/* ── Divider ── */
hr { border-color: #1E3448 !important; }

/* ── Metric widget ── */
[data-testid="stMetric"] { background:#131F2E; border:1px solid #1E3448;
  border-radius:8px; padding:12px 16px; }
[data-testid="stMetric"] label { color:#64748B !important; font-size:11px !important; }
[data-testid="stMetric"] [data-testid="stMetricValue"] { color:#E2E8F0 !important; }

div[data-testid="stRadio"] label { color:#94A3B8 !important; }
div[data-testid="stRadio"] label:hover { color:#38BDF8 !important; }
</style>
""", unsafe_allow_html=True)

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def badge(kd):
    cls = {'G\u00dc\u00c7L\u00dc ADAY':'badge-guclu','POTANS\u0130YEL':'badge-pot',
           'ZAYIF':'badge-zayif','ELEND\u0130':'badge-elen'}.get(kd,'badge-elen')
    return f"<span class='{cls}'>{kd}</span>"

def donem_fmt(d):
    return f"{d[:4]}/{d[4:]}" if d and len(d)==6 else d

# ─── SESSION STATE ────────────────────────────────────────────────────────────
for k, v in [('watchlist',{}),('quarters',{}),('results',None),
              ('elendi',None),('son_donem',None),('son_yukleme',None),('engine',None)]:
    if k not in st.session_state: st.session_state[k] = v

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div class='sb-logo'>\U0001f4ca FARK</div>", unsafe_allow_html=True)
    st.markdown("<div class='sb-sub'>Fiyat Ard\u0131nda Kalan \u015eirketler · GXSMODUJ</div>",
                unsafe_allow_html=True)

    page = st.radio("", ["\U0001f50d Scanner", "\u2b50 Takip Listesi",
                         "\U0001f4da Sistem (8 B\u00f6l\u00fcm)", "\u2699\ufe0f Ayarlar"],
                    label_visibility="collapsed")

    st.markdown("<hr>", unsafe_allow_html=True)

    # Veri durumu
    if st.session_state.son_yukleme:
        son = datetime.fromisoformat(st.session_state.son_yukleme)
        gun = (datetime.now()-son).days
        donems = sorted(st.session_state.quarters.keys())
        durum_renk = "#EF4444" if gun>85 else "#4ADE80"
        durum_txt  = "G\u00fcncelle!" if gun>85 else "G\u00fcncel"
        st.markdown(f"""
        <div class='sb-stat'>
          <div class='sb-stat-label'>Veri Durumu</div>
          <div class='sb-stat-val' style='color:{durum_renk}'>{durum_txt}</div>
          <div style='font-size:11px;color:#475569;margin-top:4px'>
            {len(donems)} d\u00f6nem · Son: {donem_fmt(donems[-1]) if donems else '-'}<br>
            {gun} g\u00fcn \u00f6nce y\u00fcklendi
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class='sb-stat'>
          <div class='sb-stat-label'>Veri Durumu</div>
          <div class='sb-stat-val' style='color:#475569'>Y\u00fcklenmedi</div>
          <div style='font-size:11px;color:#475569;margin-top:4px'>
            Scanner'dan veri y\u00fckle
          </div></div>""", unsafe_allow_html=True)

    if st.session_state.watchlist:
        st.markdown(f"""<div class='sb-stat'>
          <div class='sb-stat-label'>Takip Listesi</div>
          <div class='sb-stat-val'>\u2b50 {len(st.session_state.watchlist)} hisse</div>
        </div>""", unsafe_allow_html=True)

    if st.session_state.results:
        results = st.session_state.results
        guclu_n = sum(1 for r in results if r['Puan']>=75)
        pot_n   = sum(1 for r in results if 55<=r['Puan']<75)
        st.markdown(f"""<div class='sb-stat'>
          <div class='sb-stat-label'>Son Tarama</div>
          <div style='margin-top:4px'>
            <span style='color:#4ADE80;font-weight:700'>{guclu_n} G\u00fc\u00e7l\u00fc</span>
            <span style='color:#475569'> · </span>
            <span style='color:#FCD34D;font-weight:700'>{pot_n} Potansiyel</span>
          </div>
          <div style='font-size:11px;color:#475569;margin-top:3px'>
            {donem_fmt(st.session_state.son_donem)} d\u00f6nemi
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:auto;padding-top:20px;font-size:10px;color:#1E3448'>v1.1 · 2025</div>",
                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SAYFA 1: SCANNER
# ══════════════════════════════════════════════════════════════════════════════
if page == "\U0001f50d Scanner":
    st.markdown("""<div class='page-header'>
    <h1>\U0001f50d FARK Scanner</h1>
    <p>Fastweb Excel dosyalar\u0131n\u0131 y\u00fckle · F1-F4 filtresi otomatik · Tek t\u0131kla takip listesine ekle</p>
    </div>""", unsafe_allow_html=True)

    with st.expander("\U0001f4c1 Veri Y\u00fckle", expanded=not bool(st.session_state.results)):
        c1, c2 = st.columns([2,1])
        with c1:
            st.markdown("<p style='font-size:12px;color:#64748B'>Fastweb → \u015eirket Puanlama → Model: <b>Uygulama</b> → Sekt\u00f6r: <b>T\u00fcm\u00fc</b> → D\u00f6nem: <b>Spesifik se\u00e7 (Cari D\u00f6nem değil)</b></p>", unsafe_allow_html=True)
            uploaded = st.file_uploader("", type=['xlsx'], accept_multiple_files=True,
                                         label_visibility="collapsed")
        with c2:
            if uploaded:
                st.markdown(f"<p style='color:#38BDF8;font-size:13px'>\U0001f4ce {len(uploaded)} dosya se\u00e7ildi</p>",
                             unsafe_allow_html=True)
                if st.button("\U0001f680 Taramay\u0131 Ba\u015flat", type="primary", use_container_width=True):
                    with st.spinner("Veriler i\u015fleniyor..."):
                        quarters, hatalar = {}, []
                        for f in uploaded:
                            donem = donem_from_filename(f.name)
                            if donem:
                                data = read_excel_bytes(f.read())
                                if data: quarters[donem] = data
                                else: hatalar.append(f"`{f.name}` → veri okunamad\u0131")
                            else:
                                hatalar.append(f"`{f.name}` → d\u00f6nem \u00e7\u0131kar\u0131lamad\u0131")
                        if quarters:
                            engine = FARKEngine(quarters)
                            results, elendi = engine.tara()
                            st.session_state.update({'quarters':quarters,'engine':engine,
                                'results':results,'elendi':elendi,'son_donem':engine.son_donem,
                                'son_yukleme':datetime.now().isoformat()})
                            st.success(f"\u2713 {len(quarters)} d\u00f6nem · {engine.son_donem} · {len(results)} hisse ge\u00e7ti")
                            st.rerun()
                        else:
                            st.error("Hi\u00e7bir dosya y\u00fcklenemedi.")
                            for h in hatalar: st.warning(h)

    if st.session_state.results is not None:
        results  = st.session_state.results
        elendi   = st.session_state.elendi or {}
        son_donem = st.session_state.son_donem

        guclu = [r for r in results if r['Puan']>=75]
        pot   = [r for r in results if 55<=r['Puan']<75]
        zayif = [r for r in results if 35<=r['Puan']<55]
        toplam_elen = sum(len(v) for v in elendi.values())

        # Metrik kartlar
        st.markdown(f"""<div class='metric-row'>
          <div class='metric-card mc-green'>
            <div class='mc-num'>{len(guclu)}</div>
            <div class='mc-lbl'>\U0001f7e2 G\u00fc\u00e7l\u00fc Aday</div>
          </div>
          <div class='metric-card mc-yellow'>
            <div class='mc-num'>{len(pot)}</div>
            <div class='mc-lbl'>\U0001f7e1 Potansiyel</div>
          </div>
          <div class='metric-card mc-orange'>
            <div class='mc-num'>{len(zayif)}</div>
            <div class='mc-lbl'>\U0001f7e0 Zay\u0131f</div>
          </div>
          <div class='metric-card mc-blue'>
            <div class='mc-num'>{len(results)}</div>
            <div class='mc-lbl'>\U0001f4ca Toplam Ge\u00e7en</div>
          </div>
          <div class='metric-card mc-red'>
            <div class='mc-num'>{toplam_elen}</div>
            <div class='mc-lbl'>\u274c Elenen</div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Filtreler
        col_f1, col_f2, col_f3, col_f4 = st.columns([1.5,2,1.5,1])
        with col_f1:
            karar_filtre = st.multiselect("Karar", ["G\u00dc\u00c7L\u00dc ADAY","POTANS\u0130YEL","ZAYIF","ELEND\u0130"],
                                           default=["G\u00dc\u00c7L\u00dc ADAY","POTANS\u0130YEL"])
        with col_f2:
            sektor_listesi = sorted(set(r['Sekt\u00f6r'] for r in results if r['Sekt\u00f6r']))
            sektor_filtre = st.multiselect("Sekt\u00f6r", sektor_listesi)
        with col_f3:
            siralama = st.selectbox("S\u0131rala", ["FARK Puan\u0131 \u2193","FK/PD% \u2193","B\u00fcy\u00fcme% \u2193"])
        with col_f4:
            min_puan = st.number_input("Min Puan", value=0, min_value=0, max_value=100, step=5)

        goster = [r for r in results if r['Karar'] in karar_filtre and r['Puan'] >= min_puan]
        if sektor_filtre:
            goster = [r for r in goster if r['Sekt\u00f6r'] in sektor_filtre]
        if siralama == "FK/PD% \u2193":
            goster.sort(key=lambda x: float(x.get('FK/PD%','0').replace('-','0') or 0), reverse=True)
        elif siralama == "B\u00fcy\u00fcme% \u2193":
            goster.sort(key=lambda x: float(x.get('B\u00fcy\u00fcme%','0').replace('+','').replace('-','0') or 0), reverse=True)

        st.markdown(f"<p style='font-size:12px;color:#475569;margin:8px 0'>{len(goster)} hisse g\u00f6steriliyor · D\u00f6nem: <b>{donem_fmt(son_donem)}</b></p>",
                     unsafe_allow_html=True)

        # Tablo başlığı
        st.markdown("""<div class='tbl-header'>
          <span>KOD</span><span>SEKT\u00d6R</span><span>PUAN</span>
          <span>A · B · C · D</span><span>FAAL.KARI</span>
          <span>PİY.DEĞERİ</span><span>FK/PD%</span><span>TAKİP</span>
        </div>""", unsafe_allow_html=True)

        # Hisse satırları
        for r in goster:
            kod  = r['Kod']
            puan = r['Puan']
            kd   = r['Karar']
            in_wl = kod in st.session_state.watchlist
            oran_val = r.get('FK/PD%','-')
            try: oran_hi = float(oran_val) > 10
            except: oran_hi = False

            badge_map = {'G\u00dc\u00c7L\u00dc ADAY':'badge-guclu','POTANS\u0130YEL':'badge-pot',
                         'ZAYIF':'badge-zayif','ELEND\u0130':'badge-elen'}
            badge_cls = badge_map.get(kd,'badge-elen')
            oran_cls  = 'oran-hi' if oran_hi else 'oran-lo'
            buyume    = r.get('B\u00fcy\u00fcme%','-')

            st.markdown(f"""<div class='hisse-row'>
              <span class='kod'>{kod}</span>
              <span class='sek'>{r['Sekt\u00f6r']}</span>
              <span><span class='{badge_cls}'>{puan:.0f}</span></span>
              <span class='abcd'>A:{r['A']} · B:{r['B']} · C:{r['C']} · D:{r['D']}</span>
              <span class='val'>{r['Faal.Kar\u0131']}</span>
              <span class='val'>{r['Piy.De\u011feri']}</span>
              <span class='{oran_cls}'>{oran_val}%</span>
              <span></span>
            </div>""", unsafe_allow_html=True)

            # Takip butonu (invisible column trick)
            col_sp, col_btn = st.columns([11.2, 0.8])
            with col_btn:
                lbl = "\u2b50" if in_wl else "\u2606"
                if st.button(lbl, key=f"wl_{kod}", help="Takip listesi"):
                    if in_wl:
                        del st.session_state.watchlist[kod]
                    else:
                        st.session_state.watchlist[kod] = {
                            'puan':puan,'karar':kd,'sektor':r['Sekt\u00f6r'],
                            'eklenme':datetime.now().strftime('%Y-%m-%d'),
                            'eklenme_donemi':son_donem,
                        }
                        st.toast(f"\u2b50 {kod} eklendi!", icon="\u2705")
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander(f"\u274c Elenen Hisseler ({toplam_elen})"):
            c1,c2,c3,c4 = st.columns(4)
            for col, (filtre, lst) in zip([c1,c2,c3,c4], elendi.items()):
                with col:
                    st.markdown(f"<b style='color:#F87171'>{filtre}</b> <span style='color:#475569'>({len(lst)})</span>", unsafe_allow_html=True)
                    st.caption(", ".join(lst[:20]) + ("..." if len(lst)>20 else ""))

# ══════════════════════════════════════════════════════════════════════════════
# SAYFA 2: TAKİP LİSTESİ
# ══════════════════════════════════════════════════════════════════════════════
elif page == "\u2b50 Takip Listesi":
    st.markdown("""<div class='page-header'>
    <h1>\u2b50 Takip Listesi</h1>
    <p>Y\u0131ld\u0131zlad\u0131\u011f\u0131n hisseler · Yeni veri y\u00fcklenince otomatik bozulma kontrol\u00fc</div>""",
    unsafe_allow_html=True)

    if not st.session_state.watchlist:
        st.markdown("""<div style='background:#131F2E;border:1px dashed #1E3448;border-radius:10px;
        padding:40px;text-align:center'>
        <div style='font-size:32px'>\u2b50</div>
        <p style='color:#475569'>Hen\u00fcz takip listene hisse eklemedin.<br>
        Scanner'dan \u2606 butonuna t\u0131klayarak ekleyebilirsin.</p>
        </div>""", unsafe_allow_html=True)
    else:
        col_exp, col_imp = st.columns(2)
        with col_exp:
            wl_json = json.dumps(st.session_state.watchlist, ensure_ascii=False, indent=2)
            st.download_button("\U0001f4be Takip Listesini \u0130ndir", wl_json,
                                file_name="fark_takip.json", mime="application/json")
        with col_imp:
            imp = st.file_uploader("\U0001f4c2 JSON Y\u00fckle", type=['json'], label_visibility="collapsed")
            if imp:
                try:
                    loaded = json.loads(imp.read())
                    st.session_state.watchlist.update(loaded)
                    st.success(f"\u2713 {len(loaded)} hisse y\u00fcklendi")
                    st.rerun()
                except: st.error("Dosya format\u0131 hatal\u0131")

        st.markdown("<hr>", unsafe_allow_html=True)
        engine = st.session_state.engine

        if not engine:
            st.markdown("""<div style='background:#1C1208;border:1px solid #92400E;
            border-radius:8px;padding:12px 16px;margin-bottom:16px'>
            \u26a0\ufe0f Bozulma kontrol\u00fc i\u00e7in \u00f6nce Scanner'dan veri y\u00fckle.
            </div>""", unsafe_allow_html=True)

        bozulan, temiz, veri_yok = [], [], []
        for kod, bilgi in st.session_state.watchlist.items():
            if engine:
                uyarilar, yeni_puan = engine.bozulma_kontrol(kod, bilgi.get('puan'))
                if uyarilar: bozulan.append((kod, bilgi, uyarilar, yeni_puan))
                else: temiz.append((kod, bilgi, yeni_puan))
            else:
                veri_yok.append((kod, bilgi))

        if bozulan:
            st.markdown(f"<h3 style='color:#EF4444'>\U0001f6a8 Bozulma Uyard\u0131 — {len(bozulan)} Hisse</h3>",
                         unsafe_allow_html=True)
            for kod, bilgi, uyarilar, yeni_puan in bozulan:
                puan_eski = bilgi.get('puan','?')
                puan_yeni = f"{yeni_puan:.0f}" if yeni_puan else "?"
                st.markdown(f"""<div class='boz-card'>
                  <div style='display:flex;justify-content:space-between;align-items:center'>
                    <b style='color:#F87171;font-size:15px'>{kod}</b>
                    <span style='color:#64748B;font-size:11px'>{bilgi.get('sektor','')} · {bilgi.get('eklenme_donemi','?')}</span>
                  </div>
                  <div style='color:#94A3B8;font-size:12px;margin-top:4px'>
                    Puan: <b>{puan_eski:.0f}p \u2192 {puan_yeni}p</b> · {'<br>'.join(uyarilar)}
                  </div>
                </div>""", unsafe_allow_html=True)
                if yeni_puan: st.session_state.watchlist[kod]['puan'] = yeni_puan
                _, c_rm = st.columns([5,1])
                with c_rm:
                    if st.button("\U0001f5d1\ufe0f \u00c7\u0131kar", key=f"rm_{kod}"): 
                        del st.session_state.watchlist[kod]; st.rerun()
            st.markdown("<hr>", unsafe_allow_html=True)

        if temiz or veri_yok:
            kaynak = temiz if engine else [(k,b,None) for k,b in veri_yok]
            st.markdown(f"<h3 style='color:#4ADE80'>\u2705 Takip Listesi — {len(kaynak)} Hisse</h3>",
                         unsafe_allow_html=True)
            for item in kaynak:
                kod, bilgi = item[0], item[1]
                yeni_puan  = item[2] if len(item)>2 else None
                puan = yeni_puan or bilgi.get('puan',0)
                kd   = karar_label(puan) if yeni_puan else bilgi.get('karar','')
                badge_map = {'G\u00dc\u00c7L\u00dc ADAY':'badge-guclu','POTANS\u0130YEL':'badge-pot',
                             'ZAYIF':'badge-zayif','ELEND\u0130':'badge-elen'}
                bc = badge_map.get(kd,'badge-elen')
                st.markdown(f"""<div class='tmz-card'>
                  <div style='display:flex;justify-content:space-between;align-items:center'>
                    <div>
                      <b style='color:#E2E8F0;font-size:14px'>{kod}</b>
                      <span style='color:#475569;font-size:11px;margin-left:10px'>{bilgi.get('sektor','')}</span>
                    </div>
                    <div style='display:flex;align-items:center;gap:12px'>
                      <span class='{bc}'>{puan:.0f}p</span>
                      <span style='color:#475569;font-size:11px'>{bilgi.get('eklenme_donemi','?')}</span>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)
                _, c_rm = st.columns([6,1])
                with c_rm:
                    if st.button("\U0001f5d1\ufe0f", key=f"rm_{kod}"):
                        del st.session_state.watchlist[kod]; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SAYFA 3: SİSTEM 8 BÖLÜM
# ══════════════════════════════════════════════════════════════════════════════
elif page == "\U0001f4da Sistem (8 B\u00f6l\u00fcm)":
    st.markdown("""<div class='page-header'>
    <h1>\U0001f4da FARK Sistemi — Metodoloji</h1>
    <p>Fiyat Ard\u0131nda Kalan \u015eirketler · GXSMODUJ Metodolojisi Uzant\u0131s\u0131 · v1.1</p>
    </div>""", unsafe_allow_html=True)

    bolum = st.selectbox("B\u00f6l\u00fcm:", [
        "B1 — Neden Geli\u015ftirildi?", "B2 — Sistem Mimarisi",
        "B3 — Filtreler (F1-F4)", "B4 — Puanlama (A-B-C-D)",
        "B5 — Skor Tablosu", "B6 — Geriye D\u00f6n\u00fck Test",
        "B7 — Uygulama K\u0131lavuzu", "B8 — H\u0131zl\u0131 Ba\u015fvuru Kart\u0131"
    ])

    if "B1" in bolum:
        st.markdown("<h2>Neden Geli\u015ftirildi?</h2>", unsafe_allow_html=True)
        st.markdown("""<div style='background:#131F2E;border-left:4px solid #38BDF8;
        border-radius:8px;padding:16px 20px;margin-bottom:20px;font-style:italic;color:#94A3B8'>
        "Bir hissenin fiyat\u0131 y\u00fckselişe ge\u00e7meden \u00f6nce hangi finansal sinyaller mevcuttu?
        Bu sinyaller \u00f6nceden tespit edilebilir miydi?"
        </div>""", unsafe_allow_html=True)

        c1,c2,c3 = st.columns(3)
        with c1:
            st.markdown("""<div style='background:#0A1C0F;border:1px solid #166534;
            border-radius:8px;padding:14px;'>
            <div style='color:#4ADE80;font-weight:700;margin-bottom:6px'>Ke\u015fif 1</div>
            <p style='font-size:12px'>Y\u00fcksek getiri tek tip profilden gelmiyor — de\u011fer, b\u00fcy\u00fcme, spek\u00fclatif hepsi %1000+ yapabiliyor.</p>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""<div style='background:#0A1420;border:1px solid #1E40AF;
            border-radius:8px;padding:14px;'>
            <div style='color:#38BDF8;font-weight:700;margin-bottom:6px'>Ke\u015fif 2</div>
            <p style='font-size:12px'>S\u00fcrd\u00fcr\u00fclebilir y\u00fckseli\u015fler YALNIZCA operasyonel b\u00fcy\u00fcmesi olan \u015firketlerden geliyor.</p>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown("""<div style='background:#1C1208;border:1px solid #92400E;
            border-radius:8px;padding:14px;'>
            <div style='color:#FCD34D;font-weight:700;margin-bottom:6px'>Ke\u015fif 3</div>
            <p style='font-size:12px'>En erken sinyal: FK b\u00fcy\u00fcmesi + fiyat\u0131n XU100 gerisinde kalmas\u0131. PD/DD de\u011fil!</p>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        df_hisse = pd.DataFrame([
            ("CRDFA","%11.329","Faktoring","F3 e\u015fi\u011fi"),
            ("RYSAS","%45.060","Ula\u015ft\u0131rma","F4 TMS 29 \u2014 YEN\u0130 KURAL"),
            ("ASELS","%9.852","Savunma","Orijinal kural \u2713"),
            ("BURVA","%67.436","Sanayi","F3 e\u015fi\u011fi"),
            ("TMPOL","%23.842","Kimya","F3 e\u015fi\u011fi"),
            ("AYES","%21.233","In\u015f.Malz.","F2 eksik veri"),
            ("ORMA","%13.995","Orman","F4 TMS 29"),
            ("IZFAS","%29.220","Kimya","F3 + F4 TMS 29"),
            ("UFUK","%158.972","Yat.Y\u00f6n.","F1 d\u00fczeltildi \u2713"),
            ("IEYHO","%49.050","Enerji Holding","F1 d\u00fczeltildi \u2713"),
            ("TRHOL","%351.751","Fin.Holding","Do\u011fru eleniyor \u2713"),
            ("TEHOL","%79.700","Fin.Holding","Do\u011fru eleniyor \u2713"),
            ("BSOKE","%19.256","\u00c7imento","Do\u011fru ka\u00e7\u0131r\u0131yor \u2713"),
        ], columns=["Hisse","Getiri","Sekt\u00f6r","FARK Karar\u0131"])
        st.dataframe(df_hisse, use_container_width=True, hide_index=True)

    elif "B2" in bolum:
        st.markdown("<h2>Sistem Mimarisi</h2>", unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            st.markdown("""<div style='background:#0A1420;border:2px solid #2563EB;
            border-radius:10px;padding:24px;text-align:center'>
            <div style='color:#38BDF8;font-size:13px;font-weight:700;letter-spacing:1px'>A\u015eAMA 1</div>
            <div style='color:#E2E8F0;font-size:22px;font-weight:800;margin:8px 0'>F\u0130LTRELEME</div>
            <div style='color:#38BDF8;font-size:36px;font-weight:900'>4</div>
            <div style='color:#64748B;font-size:12px'>Kural · Biri tutmazsa eler</div>
            <div style='margin-top:12px;font-size:11px;color:#475569'>
            F1: \u0130\u015f Modeli · F2: Faaliyet Kar\u0131<br>
            F3: B\u00fcy\u00fcme · F4: Zarar Kontrol\u00fc
            </div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""<div style='background:#0A1C0F;border:2px solid #16A34A;
            border-radius:10px;padding:24px;text-align:center'>
            <div style='color:#4ADE80;font-size:13px;font-weight:700;letter-spacing:1px'>A\u015eAMA 2</div>
            <div style='color:#E2E8F0;font-size:22px;font-weight:800;margin:8px 0'>PUANLAMA</div>
            <div style='color:#4ADE80;font-size:36px;font-weight:900'>128</div>
            <div style='color:#64748B;font-size:12px'>Maks Puan · 4 Kategori</div>
            <div style='margin-top:12px;font-size:11px;color:#475569'>
            A: B\u00fcy\u00fcme (35p) · B: De\u011fer (48p)<br>
            C: Karl\u0131l\u0131k (25p) · D: Model (20p)
            </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("""<div style='background:#131F2E;border:1px solid #1E3448;
        border-radius:8px;padding:14px;text-align:center;margin-top:16px;color:#64748B;font-size:12px'>
        FASTWEB B\u0130LAN\u00c7O VER\u0130S\u0130 → F\u0130LTRELEME → PUANLAMA → KARAR
        </div>""", unsafe_allow_html=True)

    elif "B3" in bolum:
        st.markdown("<h2>Filtreler (Kalibre Edilmi\u015f)</h2>", unsafe_allow_html=True)
        tabs = st.tabs(["F1 — \u0130\u015f Modeli","F2 — Faal. Kar\u0131","F3 — B\u00fcy\u00fcme","F4 — Zarar"])
        filtre_data = [
            ("F1","Ope\u00e7\u0131n \u015e'ir", "Operasyonel \u015firket mi? Holding/GYO/Portf\u00f6y elenir.",
             "\U0001f527 FK son 8 \u00e7eyre\u011fin 6+'unda pozitifse finansal holding de ge\u00e7er (UFUK, IEYHO tipi)",
             "Holding, GYO, Portf\u00f6y, Menkul K\u0131ymet, Giri\u015fim Sermayesi",
             "Operasyonel \u015firketler + FK tutarl\u0131 operasyonel holdingleri"),
            ("F2","Faal. Kar\u0131 S\u00fcrekli",
             "Son 8 \u00e7eyre\u011fin en az 6's\u0131nda faaliyet kar\u0131 pozitif mi?",
             "TMS 29 enflasyon muhasebesi net kar\u0131 bozabilir — bu y\u00fczden faaliyet kar\u0131 baz al\u0131n\u0131r",
             "Pozitif kriter tutmayan \u015firketler",
             "Son 8 \u00e7eyre\u011fin 6+'unda FK pozitif olanlar"),
            ("F3","B\u00fcy\u00fcme Varl\u0131\u011f\u0131",
             "G\u00fcncel faaliyet kar\u0131, 8 \u00e7eyrek \u00f6ncesine g\u00f6re %20+ b\u00fcy\u00fcm\u00fc\u015f m\u00fc?",
             "\U0001f527 PD/DD < 1 veya FK/PD > %15 ise e\u015fik %5'e d\u00fc\u015fer (CRDFA, TMPOL, BURVA tipi)",
             "FK 2 y\u0131lda %20+ b\u00fcy\u00fcmeyenler",
             "FK 2 y\u0131lda %20+ (ucuz hissede %5+) b\u00fcy\u00fcyenler"),
            ("F4","\u00d6l\u00fcmc\u00fcl Zarar",
             "Son 4 \u00e7eyrekte net ve faaliyet kar\u0131 s\u00fcrekli negatif mi?",
             "\U0001f527 NK negatif ama FK pozitifse GE\u00c7ER (TMS 29 korumas\u0131 — RYSAS, ORMA tipi)",
             "FK de negatifse ger\u00e7ek zarar \u2192 eler",
             "NK negatif ama FK pozitifse TMS 29 etkisi say\u0131l\u0131r"),
        ]
        for tab, (fno, _, kural, kalibrasyon, elen, gecer) in zip(tabs, filtre_data):
            with tab:
                st.markdown(f"<p style='color:#CBD5E1'>{kural}</p>", unsafe_allow_html=True)
                st.markdown(f"""<div style='background:#1C1208;border-left:3px solid #F59E0B;
                border-radius:6px;padding:10px 14px;margin:10px 0;font-size:12px;color:#FCD34D'>
                {kalibrasyon}</div>""", unsafe_allow_html=True)
                c1,c2 = st.columns(2)
                with c1:
                    st.markdown(f"""<div style='background:#1C0A0A;border:1px solid #7F1D1D;
                    border-radius:6px;padding:10px 14px;font-size:12px'>
                    <b style='color:#F87171'>ELER:</b><br>{elen}</div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""<div style='background:#0A1C0F;border:1px solid #166534;
                    border-radius:6px;padding:10px 14px;font-size:12px'>
                    <b style='color:#4ADE80'>GE\u00c7ER:</b><br>{gecer}</div>""", unsafe_allow_html=True)

    elif "B4" in bolum:
        st.markdown("<h2>Puanlama Kategorileri</h2>", unsafe_allow_html=True)
        tabs = st.tabs(["A — B\u00fcy\u00fcme (35p)","B — De\u011fer (48p)","C — Karl\u0131l\u0131k (25p)","D — Model (20p)"])
        with tabs[0]:
            df_a = pd.DataFrame([("FK 4+ y\u0131ld\u0131r b\u00fcy\u00fcyor","30"),("FK 2-3 y\u0131ld\u0131r b\u00fcy\u00fcyor","20"),
                ("FK 1 y\u0131ld\u0131r b\u00fcy\u00fcyor","10"),("Tutars\u0131z/durmu\u015f","0"),
                ("B\u00fcy\u00fcme >%100 bonus","+5"),(">%50 bonus","+3"),(">%20 bonus","+1")],
                columns=["Kriter","Puan"])
            st.dataframe(df_a, hide_index=True, use_container_width=True)
        with tabs[1]:
            df_b = pd.DataFrame([("PD/DD < 1","12"),("PD/DD 1-3","9"),("PD/DD 3-6","5"),("PD/DD > 6","0"),
                ("FK b\u00fcy\u00fcmesi > PD b\u00fcy\u00fcmesi x2","+13"),("FK b\u00fcy\u00fcmesi > PD b\u00fcy\u00fcmesi","+8"),
                ("PD/FK < 5","+10"),("PD/FK < 15","+3")], columns=["Kriter","Puan"])
            st.dataframe(df_b, hide_index=True, use_container_width=True)
        with tabs[2]:
            df_c = pd.DataFrame([("Marj > %20","10"),("Marj %10-20","7"),("Marj %5-10","4"),("Marj < %5","1"),
                ("NK/FK > %60","+8"),("NK/FK %30-60","+5"),("NK/FK > 0","+2"),
                ("\u0130\u015fletme nakit ak\u0131\u015f\u0131 pozitif","+7")], columns=["Kriter","Puan"])
            st.dataframe(df_c, hide_index=True, use_container_width=True)
        with tabs[3]:
            df_d = pd.DataFrame([
                ("Yap\u0131sal sekt\u00f6r (finans, enerji, sa\u011fl\u0131k, savunma)","8"),
                ("D\u00f6ng\u00fcsel istikrarl\u0131 (sanayi, g\u0131da, ula\u015ft\u0131rma)","5"),
                ("Volatil / proje bazl\u0131","2"),
                ("Ni\u015f sekt\u00f6r (PD < 2Mr)","7"),("Orta bilinirlik (PD 2-20Mr)","4"),
                ("Herkesin bildi\u011fi (PD > 20Mr)","1"),
                ("Bor\u00e7/\u00d6zkaynak < 1","5"),("Bor\u00e7/\u00d6zkaynak 1-3","3")],
                columns=["Kriter","Puan"])
            st.dataframe(df_d, hide_index=True, use_container_width=True)

    elif "B5" in bolum:
        st.markdown("<h2>Skor Tablosu ve Karar</h2>", unsafe_allow_html=True)
        skorlar = [
            ("75-100","\U0001f7e2 G\u00dc\u00c7L\u00dc ADAY","#14532D","#4ADE80","Derinlemesine incele","GXSMODUJ tam analizi uygula"),
            ("55-74","\U0001f7e1 POTANS\u0130YEL","#422006","#FCD34D","Takibe al","KAP takibi, sonraki bilan\u00e7oyu bekle"),
            ("35-54","\U0001f7e0 ZAYIF","#431407","#FB923C","Ge\u00e7 / Bekle","Sekt\u00f6r katalizör\u00fc olmadan alma"),
            ("0-34","\U0001f534 ELEND\u0130","#450A0A","#F87171","Alma","Portf\u00f6ye dahil etme"),
        ]
        for puan_r, karar, bg, clr, eylem, aciklama in skorlar:
            st.markdown(f"""<div style='background:{bg};border-left:4px solid {clr};
            border-radius:8px;padding:14px 18px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center'>
            <div>
              <b style='color:{clr};font-size:16px'>{karar}</b>
              <span style='color:#475569;font-size:12px;margin-left:12px'>Puan: {puan_r}</span>
            </div>
            <div style='text-align:right'>
              <div style='color:#E2E8F0;font-size:13px;font-weight:700'>{eylem}</div>
              <div style='color:#64748B;font-size:11px'>{aciklama}</div>
            </div>
            </div>""", unsafe_allow_html=True)

    elif "B6" in bolum:
        st.markdown("<h2>Geriye D\u00f6n\u00fck Test — 6/6 Do\u011fru</h2>", unsafe_allow_html=True)
        df_test = pd.DataFrame([
            ("DSTFK","2022/12","33","25","18","18","94","\u2713 %1362"),
            ("KTLEV","2023/12","25","25","25","20","95","\u2713 %1250"),
            ("TERA","2023/12","15","25","19","18","77","\u2713 %2100"),
            ("GUNGD","2023/12","23","17","3","12","55","\u26a0 Y\u00fckeldi, bozuldu"),
            ("HEDEF","\u2014","\u2014","\u2014","\u2014","\u2014","F1 EL.","\u2713 Volatil kar"),
            ("PEKGY","\u2014","\u2014","\u2014","\u2014","\u2014","F1 EL.","\u2713 Zarar ediyor"),
        ], columns=["Hisse","Snapshot","A","B","C","D","TOPLAM","SONU\u00c7"])
        st.dataframe(df_test, hide_index=True, use_container_width=True)
        st.markdown("""<div style='background:#0A1C0F;border:1px solid #166534;
        border-radius:8px;padding:14px;margin-top:12px;text-align:center;color:#4ADE80;font-weight:700'>
        6/6 hisse do\u011fru de\u011ferlendirildi — sistem ge\u00e7erlili\u011fi kan\u0131tland\u0131
        </div>""", unsafe_allow_html=True)

    elif "B7" in bolum:
        st.markdown("<h2>Uygulama K\u0131lavuzu</h2>", unsafe_allow_html=True)

        st.markdown("""<div style='background:#0A1420;border:1px solid #1E40AF;
        border-radius:10px;padding:18px 22px;margin-bottom:20px'>
        <b style='color:#38BDF8;font-size:14px'>\U0001f4e5 Ad\u0131m 1 — Fastweb'den Veri \u0130ndir</b>
        </div>""", unsafe_allow_html=True)

        c1,c2 = st.columns([1.2,1])
        with c1:
            st.markdown("""<div style='background:#131F2E;border:1px solid #1E3448;
            border-radius:8px;padding:14px 18px;font-size:13px'>
            <p><b style='color:#38BDF8'>Site:</b> <a href='https://fwmanaliz.com' style='color:#60A5FA'>fwmanaliz.com</a></p>
            <p><b style='color:#38BDF8'>Yol:</b> \u015eirket Puanlama</p>
            <p><b style='color:#38BDF8'>Model:</b> Uygulama</p>
            <p><b style='color:#38BDF8'>Sekt\u00f6r:</b> T\u00fcm\u00fc</p>
            <p><b style='color:#38BDF8'>D\u00f6nem:</b> Listeden spesifik se\u00e7 \u2714\ufe0f</p>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""<div style='background:#1C1208;border:1px solid #92400E;
            border-radius:8px;padding:14px 18px;font-size:13px'>
            <b style='color:#FCD34D'>\u26a0\ufe0f Cari D\u00f6nem Se\u00e7me!</b><br>
            <span style='color:#94A3B8;font-size:12px'>Dosya ad\u0131nda tarih gelmez,
            sistem tan\u0131yamaz. Listeden <b>2025/12</b> gibi spesifik d\u00f6nem se\u00e7.</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<b style='color:#E2E8F0'>Hangi d\u00f6nemleri indirmelisin?</b>", unsafe_allow_html=True)
        df_donem = pd.DataFrame([
            ("2018/03","201803","\u2713 \u0130lk referans noktas\u0131"),
            ("2019/03 \u2014 2024/12","201903...202412","\u2713 Tarihsel b\u00fcy\u00fcme serisi"),
            ("2025/03","202503","\u2713 Son 2 y\u0131l i\u00e7in zorunlu"),
            ("2025/06","202506","\u2713 Son 2 y\u0131l i\u00e7in zorunlu"),
            ("2025/09","202509","\u2713 Son 2 y\u0131l i\u00e7in zorunlu"),
            ("2025/12","202512","\u2b50 En son d\u00f6nem — ana analiz"),
        ], columns=["D\u00f6nem","Dosya Ad\u0131 \u0130\u00e7inde","Not"])
        st.dataframe(df_donem, hide_index=True, use_container_width=True)
        st.markdown("<p style='font-size:11px;color:#475569;margin-top:6px'>Minimum 8 d\u00f6nem \u00f6nerilir. Ne kadar \u00e7ok d\u00f6nem, o kadar sa\u011fl\u0131kl\u0131 b\u00fcy\u00fcme serisi.</p>", unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        adimlar = [
            ("2","\U0001f4c1","Dosyalar\u0131 Y\u00fckle","Scanner sekmesi → t\u00fcm Excel dosyalar\u0131n\u0131 se\u00e7 (ayn\u0131 anda birden fazla)"),
            ("3","\U0001f680","Taramay\u0131 Ba\u015flat","Butona t\u0131kla — F1-F4 filtreleri ve puanlama otomatik \u00e7al\u0131\u015f\u0131r"),
            ("4","\U0001f50e","Sonu\u00e7lar\u0131 \u0130ncele","G\u00fc\u00e7l\u00fc Aday (75+) ve Potansiyel (55-74) hisseleri \u00f6ncelikli incele"),
            ("5","\u2b50","Takip Listesi","Ilgin\u00e7 bulduklar\u0131n\u0131 y\u0131ld\u0131z ile takip listesine ekle"),
            ("6","\U0001f504","G\u00fcncelle","Yeni d\u00f6nem Excel'ini indirip sisteme ekle (Mart/Haziran/Eyl\u00fcl/Aral\u0131k)"),
            ("7","\u26a0\ufe0f","Bozulma Takibi","Takip listesindeki hisseler yeni veri y\u00fcklenince otomatik kontrol edilir"),
        ]
        for no, em, baslik, aciklama in adimlar:
            st.markdown(f"""<div style='display:flex;align-items:flex-start;gap:14px;
            background:#131F2E;border:1px solid #1E3448;border-radius:8px;
            padding:12px 16px;margin-bottom:8px'>
            <span style='background:#1E40AF;color:white;border-radius:50%;width:28px;height:28px;
            display:flex;align-items:center;justify-content:center;font-weight:800;
            font-size:13px;flex-shrink:0'>{no}</span>
            <div><b style='color:#E2E8F0'>{em} {baslik}</b><br>
            <span style='color:#64748B;font-size:12px'>{aciklama}</span></div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        notlar = [
            ("#EF4444","TMS 29","Net kar yan\u0131lt\u0131c\u0131 olabilir — sistem faaliyet kar\u0131n\u0131 baz al\u0131r"),
            ("#EF4444","Finansal \u015eirketler","Faktoring/banka bilan\u00e7o yap\u0131s\u0131 farkl\u0131d\u0131r — F1 filtresi korur"),
            ("#EF4444","Cari D\u00f6nem","Fastweb'de Cari D\u00f6nem se\u00e7me — spesifik d\u00f6nem se\u00e7"),
            ("#F59E0B","G\u00fcncelleme","Her yeni bilan\u00e7o d\u00f6neminde g\u00fcncelle: Mart, Haziran, Eyl\u00fcl, Aral\u0131k"),
        ]
        for renk, baslik, aciklama in notlar:
            st.markdown(f"""<div style='background:#131F2E;border-left:3px solid {renk};
            border-radius:4px;padding:8px 14px;margin-bottom:6px'>
            <b style='color:{renk}'>{baslik}:</b>
            <span style='color:#94A3B8;font-size:12px'> {aciklama}</span>
            </div>""", unsafe_allow_html=True)

    elif "B8" in bolum:
        st.markdown("<h2>H\u0131zl\u0131 Ba\u015fvuru Kart\u0131</h2>", unsafe_allow_html=True)
        st.markdown("<b style='color:#38BDF8'>A\u015fama 1 — Filtreler</b>", unsafe_allow_html=True)
        df_f = pd.DataFrame([
            ("F1","\u0130\u015f Modeli","Operasyonel \u015firket mi?","Bilan\u00e7o"),
            ("F2","Faal. Kar\u0131","Son 8 \u00e7eyre\u011fin 6+ tanesi pozitif?","Gelir tablosu"),
            ("F3","B\u00fcy\u00fcme","FK 2 y\u0131l \u00f6ncesine g\u00f6re %20+ b\u00fcy\u00fcm\u00fc\u015f?","Gelir tablosu"),
            ("F4","Zarar","FK+NK son 2 \u00e7eyrekte hepsi negatif de\u011fil?","Gelir tablosu"),
        ], columns=["#","Filtre","Kural","Kaynak"])
        st.dataframe(df_f, hide_index=True, use_container_width=True)
        st.markdown("<br><b style='color:#38BDF8'>A\u015fama 2 — Puanlama</b>", unsafe_allow_html=True)
        df_p = pd.DataFrame([
            ("A","B\u00fcy\u00fcme S\u00fcreklilik","Ka\u00e7 y\u0131ld\u0131r b\u00fcy\u00fcyor + h\u0131z bonusu","35"),
            ("B","De\u011fer Ucuzlu\u011fu","PD/DD + FK/PD oran\u0131 + r\u00f6latif fiyat","48"),
            ("C","Karl\u0131l\u0131k Kalitesi","Marj + NK/FK + nakit ak\u0131\u015f\u0131","25"),
            ("D","\u0130\u015f Modeli","Sekt\u00f6r + bilinirlik + bor\u00e7","20"),
        ], columns=["Kat.","Kategori","Kriter","Maks."])
        st.dataframe(df_p, hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# SAYFA 4: AYARLAR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "\u2699\ufe0f Ayarlar":
    st.markdown("""<div class='page-header'>
    <h1>\u2699\ufe0f Ayarlar</h1>
    <p>Veri durumu · G\u00fcncelleme takvimi · Sistem bilgisi</p>
    </div>""", unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        st.markdown("<b style='color:#E2E8F0'>\U0001f4c5 G\u00fcncelleme Takvimi</b>", unsafe_allow_html=True)
        takvim = [("Mart","2024/12 bilan\u00e7olar\u0131"),("Haziran","2025/03 bilan\u00e7olar\u0131"),
                  ("Eyl\u00fcl","2025/06 bilan\u00e7olar\u0131"),("Aral\u0131k","2025/09 bilan\u00e7olar\u0131")]
        for ay, aciklama in takvim:
            st.markdown(f"""<div style='background:#131F2E;border:1px solid #1E3448;
            border-radius:6px;padding:8px 14px;margin-bottom:6px;display:flex;justify-content:space-between'>
            <b style='color:#38BDF8'>{ay}</b>
            <span style='color:#64748B;font-size:12px'>{aciklama} a\u00e7\u0131kland\u0131</span>
            </div>""", unsafe_allow_html=True)

        if st.session_state.son_yukleme:
            son = datetime.fromisoformat(st.session_state.son_yukleme)
            gun = (datetime.now()-son).days
            if gun > 85: st.error(f"\u26a0\ufe0f Veri g\u00fcncellenmeli — {gun} g\u00fcn ge\u00e7ti")
            elif gun > 60: st.warning(f"G\u00fcncelleme zaman\u0131 yakla\u015f\u0131yor — {gun} g\u00fcn")
            else: st.success(f"\u2713 G\u00fcncel — {gun} g\u00fcn \u00f6nce y\u00fcklendi")

    with c2:
        st.markdown("<b style='color:#E2E8F0'>\U0001f4ca Mevcut Veri Durumu</b>", unsafe_allow_html=True)
        if st.session_state.quarters:
            donems = sorted(st.session_state.quarters.keys())
            engine = st.session_state.get('engine')
            son_data_count = len(engine.son_data) if engine else 0
            bilgiler = [
                ("Y\u00fcklenen D\u00f6nem", f"{len(donems)}"),
                ("\u0130lk D\u00f6nem", donem_fmt(donems[0])),
                ("Son D\u00f6nem", donem_fmt(donems[-1])),
                ("Toplam Hisse", str(son_data_count)),
            ]
            for lbl, val in bilgiler:
                st.markdown(f"""<div style='background:#131F2E;border:1px solid #1E3448;
                border-radius:6px;padding:8px 14px;margin-bottom:6px;display:flex;justify-content:space-between'>
                <span style='color:#64748B;font-size:12px'>{lbl}</span>
                <b style='color:#E2E8F0'>{val}</b>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style='background:#131F2E;border:1px dashed #1E3448;
            border-radius:8px;padding:20px;text-align:center;color:#475569'>
            Hen\u00fcz veri y\u00fcklenmedi</div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("\U0001f5d1\ufe0f T\u00fcm Veriyi S\u0131f\u0131rla", type="secondary"):
            for k in ['quarters','results','elendi','engine','son_donem','son_yukleme']:
                st.session_state[k] = {} if k=='quarters' else None
            st.success("Veri temizlendi"); st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<b style='color:#E2E8F0'>\U0001f4cc Sistem Bilgisi</b>", unsafe_allow_html=True)
    st.markdown("""<div style='background:#0D1926;border:1px solid #1E3448;
    border-radius:8px;padding:16px 20px;font-family:monospace;font-size:12px;color:#64748B'>
    <span style='color:#38BDF8'>FARK Sistemi</span> v1.1 · Fiyat Ard\u0131nda Kalan \u015eirketler<br>
    <span style='color:#4ADE80'>GXSMODUJ</span> Metodolojisi Uzant\u0131s\u0131<br><br>
    Kalibrasyon: 13 hisse analizi (2018-2025)<br>
    F1: Operasyonel holding ge\u00e7i\u015f kural\u0131<br>
    F3: PD/DD&lt;1 veya FK/PD&gt;%15 → e\u015fik %5<br>
    F4: TMS 29 korumas\u0131 (FK pozitifse ge\u00e7er)<br>
    F2: 6 ayl\u0131k raporlama tolerans\u0131
    </div>""", unsafe_allow_html=True)
