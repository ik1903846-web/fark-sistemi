import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime, date

from fark_engine import (FARKEngine, karar_label, karar_emoji, KARAR_RENK, KARAR_BG,
                          read_excel_bytes, donem_from_filename, fmt_milyon, safe_float)

st.set_page_config(page_title="FARK Sistemi", page_icon="📊", layout="wide")

# ── CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
.fark-header { background: linear-gradient(135deg, #1B3A5C, #2E75B6);
  color: white; padding: 16px 24px; border-radius: 10px; margin-bottom: 20px; }
.fark-header h1 { margin: 0; font-size: 28px; }
.fark-header p { margin: 4px 0 0 0; opacity: 0.85; font-size: 14px; }
.metric-box { background: #F8F9FA; border-left: 4px solid #2E75B6;
  padding: 12px 16px; border-radius: 6px; margin: 4px 0; }
.karar-guclu { background:#C8E6C9; color:#1E7145; padding:3px 10px;
  border-radius:12px; font-weight:bold; font-size:13px; }
.karar-pot { background:#FFFDE7; color:#B8860B; padding:3px 10px;
  border-radius:12px; font-weight:bold; font-size:13px; }
.karar-zayif { background:#FFE0B2; color:#E65100; padding:3px 10px;
  border-radius:12px; font-weight:bold; font-size:13px; }
.karar-elen { background:#FFCDD2; color:#C00000; padding:3px 10px;
  border-radius:12px; font-weight:bold; font-size:13px; }
.bozulma-box { background:#FFEBEE; border:2px solid #C00000;
  padding:10px 16px; border-radius:8px; margin:6px 0; }
.temiz-box { background:#E8F5E9; border:2px solid #1E7145;
  padding:10px 16px; border-radius:8px; margin:6px 0; }
.uyari-banner { background:#FFF3E0; border:1px solid #E65100;
  padding:12px 16px; border-radius:8px; margin-bottom:16px; }
div[data-testid="stDataFrame"] table { font-size: 13px !important; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ────────────────────────────────────────────────
for k, v in [('watchlist', {}), ('quarters', {}), ('results', None),
              ('elendi', None), ('son_donem', None), ('son_yukleme', None),
              ('engine', None)]:
    if k not in st.session_state: st.session_state[k] = v

# ── SİDEBAR ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 FARK Sistemi")
    st.markdown("*Fiyat Ardında Kalan Şirketler*")
    st.divider()

    page = st.radio("", ["🔍 Scanner", "⭐ Takip Listesi", "📚 Sistem (8 Bölüm)", "⚙️ Ayarlar"],
                    label_visibility="collapsed")
    st.divider()

    # Güncelleme uyarısı
    if st.session_state.son_yukleme:
        son = datetime.fromisoformat(st.session_state.son_yukleme)
        gun_fark = (datetime.now() - son).days
        ay = son.month
        # Sonraki çeyrek ayları: 3,6,9,12
        ceyrek_aylari = [3, 6, 9, 12]
        sonraki = next((m for m in ceyrek_aylari if m > ay), 3)
        if gun_fark > 85:
            st.warning(f"! **Veri güncelle**\nSon yükleme: {son.strftime('%Y/%m')}\n{gun_fark} gün önce")
        else:
            st.info(f"✓ Son veri: {son.strftime('%Y/%m/%d')}\nSonraki güncelleme: {sonraki}. ay")
    else:
        st.info("📁 Henüz veri yüklenmedi")

    # Takip listesi özeti
    if st.session_state.watchlist:
        st.divider()
        st.markdown(f"⭐ **{len(st.session_state.watchlist)} hisse** takip listesinde")

    st.divider()
    st.markdown("<small>v1.0 · GXSMODUJ Metodolojisi</small>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# SAYFA 1: SCANNER
# ════════════════════════════════════════════════════════════════
if page == "🔍 Scanner":
    st.markdown("""<div class='fark-header'>
    <h1>📊 FARK Scanner</h1>
    <p>Fastweb Excel dosyalarını yükle · FARK filtreleri otomatik uygulanır · Tek tıkla takip listesine ekle</p>
    </div>""", unsafe_allow_html=True)

    # Dosya yükleme
    with st.expander("📁 Veri Yükle (Fastweb Excel Dosyaları)", expanded=not bool(st.session_state.results)):
        st.markdown("**Puanlama_Analizi_Tu_mu__YYYYMM.xlsx** formatında dosyaları yükle")
        st.markdown("*Birden fazla dosya aynı anda seçilebilir*")

        uploaded = st.file_uploader("", type=['xlsx'], accept_multiple_files=True,
                                     label_visibility="collapsed")

        if uploaded:
            col1, col2 = st.columns([3,1])
            with col1:
                st.write(f"{len(uploaded)} dosya seçildi")
            with col2:
                if st.button("🚀 Taramayı Başlat", type="primary", use_container_width=True):
                    with st.spinner("Veriler işleniyor..."):
                        quarters = {}
                        hatalar = []
                        for f in uploaded:
                            donem = donem_from_filename(f.name)
                            if donem:
                                data = read_excel_bytes(f.read())
                                if data:
                                    quarters[donem] = data
                                else:
                                    hatalar.append(f"⚠️ `{f.name}` → dönem **{donem}** tanındı ama veri okunamadı")
                            else:
                                hatalar.append(f"⚠️ `{f.name}` → dosya adından dönem çıkarılamadı")

                        if quarters:
                            engine = FARKEngine(quarters)
                            results, elendi = engine.tara()
                            st.session_state.quarters = quarters
                            st.session_state.engine = engine
                            st.session_state.results = results
                            st.session_state.elendi = elendi
                            st.session_state.son_donem = engine.son_donem
                            st.session_state.son_yukleme = datetime.now().isoformat()
                            st.success(f"✓ {len(quarters)} dönem yüklendi · {engine.son_donem} ana dönem · {len(results)} hisse geçti")
                            st.rerun()
                        else:
                            st.error("Hiçbir dosya yüklenemedi.")
                            for h in hatalar:
                                st.warning(h)
                            st.info("💡 Beklenen format: `Puanlama_Analizi_Tu_mu__YYYYMM.xlsx`")

    # Sonuçlar
    if st.session_state.results is not None:
        results = st.session_state.results
        elendi = st.session_state.elendi or {}
        son_donem = st.session_state.son_donem

        # Özet metrikler
        guclu = [r for r in results if r['Puan'] >= 75]
        pot   = [r for r in results if 55 <= r['Puan'] < 75]
        zayif = [r for r in results if 35 <= r['Puan'] < 55]

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("🟢 Güçlü Aday", len(guclu))
        c2.metric("🟡 Potansiyel", len(pot))
        c3.metric("🟠 Zayıf", len(zayif))
        c4.metric("📊 Toplam Geçen", len(results))
        c5.metric("❌ Toplam Elenen", sum(len(v) for v in elendi.values()))

        st.divider()

        # Filtreler
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            karar_filtre = st.multiselect("Karar", ["GÜÇLÜ ADAY","POTANSİYEL","ZAYIF","ELENDİ"],
                                           default=["GÜÇLÜ ADAY","POTANSİYEL"])
        with col_f2:
            sektor_listesi = sorted(list(set(r['Sektör'] for r in results if r['Sektör'])))
            sektor_filtre = st.multiselect("Sektör", sektor_listesi)
        with col_f3:
            siralama = st.selectbox("Sırala", ["FARK Puanı ↓", "FK/PD% ↓", "Büyüme% ↓"])

        # Filtrele
        goster = [r for r in results if r['Karar'] in karar_filtre]
        if sektor_filtre:
            goster = [r for r in goster if r['Sektör'] in sektor_filtre]

        if siralama == "FK/PD% ↓":
            goster.sort(key=lambda x: float(x.get('FK/PD%','0').replace('-','0') or 0), reverse=True)
        elif siralama == "Büyüme% ↓":
            goster.sort(key=lambda x: float(x.get('Büyüme%','0').replace('+','').replace('-','0') or 0), reverse=True)

        st.markdown(f"**{len(goster)} hisse gösteriliyor** (Dönem: {son_donem})")
        st.divider()

        # Hisse satırları
        for r in goster:
            kod = r['Kod']
            puan = r['Puan']
            kd = r['Karar']
            emoji = karar_emoji(puan)
            in_wl = kod in st.session_state.watchlist

            col_kod, col_sek, col_puan, col_abcd, col_fk, col_pd, col_oran, col_btn = st.columns([1.2, 2.5, 0.9, 2, 1.3, 1.3, 1.1, 1])

            with col_kod:
                st.markdown(f"**{kod}**")
            with col_sek:
                st.markdown(f"<small>{r['Sektör']}</small>", unsafe_allow_html=True)
            with col_puan:
                renk = KARAR_RENK.get(kd, '#555')
                bg   = KARAR_BG.get(kd, '#eee')
                st.markdown(f"<span style='background:{bg};color:{renk};padding:3px 8px;border-radius:10px;font-weight:bold'>{emoji} {puan}</span>", unsafe_allow_html=True)
            with col_abcd:
                st.markdown(f"<small>A:{r['A']} B:{r['B']} C:{r['C']} D:{r['D']}</small>", unsafe_allow_html=True)
            with col_fk:
                st.markdown(f"<small>FK: {r['Faal.Karı']}</small>", unsafe_allow_html=True)
            with col_pd:
                st.markdown(f"<small>PD: {r['Piy.Değeri']}</small>", unsafe_allow_html=True)
            with col_oran:
                oran_val = r.get('FK/PD%','-')
                renk_oran = '#1E7145' if oran_val != '-' and float(oran_val.replace('-','0') or 0) > 10 else '#555'
                st.markdown(f"<small style='color:{renk_oran}'><b>{oran_val}%</b></small>", unsafe_allow_html=True)
            with col_btn:
                if in_wl:
                    if st.button("⭐", key=f"wl_{kod}", help="Takip listesinden çıkar"):
                        del st.session_state.watchlist[kod]
                        st.rerun()
                else:
                    if st.button("☆", key=f"wl_{kod}", help="Takip listesine ekle"):
                        st.session_state.watchlist[kod] = {
                            'puan': puan, 'karar': kd, 'sektor': r['Sektör'],
                            'eklenme': datetime.now().strftime('%Y-%m-%d'),
                            'eklenme_donemi': son_donem,
                        }
                        st.toast(f"⭐ {kod} takip listesine eklendi!", icon="✅")
                        st.rerun()

        st.divider()

        # Elendi özet
        with st.expander("❌ Elenen Hisseler"):
            c1,c2,c3,c4 = st.columns(4)
            for col, (filtre, lst) in zip([c1,c2,c3,c4], elendi.items()):
                with col:
                    st.markdown(f"**{filtre}**: {len(lst)} hisse")
                    st.caption(", ".join(lst[:15]) + ("..." if len(lst)>15 else ""))

# ════════════════════════════════════════════════════════════════
# SAYFA 2: TAKİP LİSTESİ
# ════════════════════════════════════════════════════════════════
elif page == "⭐ Takip Listesi":
    st.markdown("""<div class='fark-header'>
    <h1>⭐ Takip Listesi</h1>
    <p>Yıldızladığın hisseler · Yeni veri yüklenince otomatik bozulma kontrolü</p>
    </div>""", unsafe_allow_html=True)

    if not st.session_state.watchlist:
        st.info("Henüz takip listene hisse eklemedin. Scanner'dan ☆ butonuna tıklayarak ekleyebilirsin.")
    else:
        # Watchlist kaydet/yükle
        col_exp, col_imp = st.columns([1,1])
        with col_exp:
            wl_json = json.dumps(st.session_state.watchlist, ensure_ascii=False, indent=2)
            st.download_button("💾 Takip Listesini İndir", wl_json,
                                file_name="fark_takip.json", mime="application/json")
        with col_imp:
            imp = st.file_uploader("📂 Takip Listesi Yükle", type=['json'], label_visibility="collapsed")
            if imp:
                try:
                    loaded = json.loads(imp.read())
                    st.session_state.watchlist.update(loaded)
                    st.success(f"✓ {len(loaded)} hisse yüklendi")
                    st.rerun()
                except: st.error("Dosya formatı hatalı")

        st.divider()

        engine = st.session_state.engine
        has_engine = engine is not None

        # Bozulma kontrolü
        bozulan = []
        temiz = []
        veri_yok = []

        for kod, bilgi in st.session_state.watchlist.items():
            if has_engine:
                uyarilar, yeni_puan = engine.bozulma_kontrol(kod, bilgi.get('puan'))
                if uyarilar:
                    bozulan.append((kod, bilgi, uyarilar, yeni_puan))
                else:
                    temiz.append((kod, bilgi, yeni_puan))
            else:
                veri_yok.append((kod, bilgi))

        if not has_engine:
            st.warning("⚠️ Bozulma kontrolü için önce Scanner'da veri yükle.")

        if bozulan:
            st.markdown(f"### 🚨 Bozulma Uyarısı — {len(bozulan)} Hisse")
            for kod, bilgi, uyarilar, yeni_puan in bozulan:
                with st.container():
                    st.markdown(f"""<div class='bozulma-box'>
                    <b>⚠️ {kod}</b> — {bilgi.get('sektor','')} 
                    — Eklenme: {bilgi.get('eklenme_donemi','?')} 
                    ({bilgi.get('puan','?'):.0f}p → {yeni_puan:.0f}p {'📉' if yeni_puan else ''})<br>
                    {'<br>'.join(uyarilar)}
                    </div>""", unsafe_allow_html=True)
                    if yeni_puan:
                        st.session_state.watchlist[kod]['puan'] = yeni_puan
                    c1, c2 = st.columns([4,1])
                    with c2:
                        if st.button("🗑️ Çıkar", key=f"rm_{kod}"):
                            del st.session_state.watchlist[kod]
                            st.rerun()
            st.divider()

        if temiz:
            st.markdown(f"### ✅ Takip Listesi — {len(temiz)} Hisse")
            for kod, bilgi, yeni_puan in temiz:
                puan = yeni_puan or bilgi.get('puan', 0)
                kd = karar_label(puan) if yeni_puan else bilgi.get('karar','')
                emoji = karar_emoji(puan) if yeni_puan else ''
                renk = KARAR_RENK.get(kd, '#555')
                bg   = KARAR_BG.get(kd, '#eee')

                col_k, col_s, col_p, col_ek, col_rm = st.columns([1,2.5,1.2,2,0.8])
                with col_k: st.markdown(f"**{kod}**")
                with col_s: st.caption(bilgi.get('sektor',''))
                with col_p:
                    st.markdown(f"<span style='background:{bg};color:{renk};padding:3px 8px;border-radius:10px;font-weight:bold'>{emoji} {puan:.0f}</span>",
                                unsafe_allow_html=True)
                with col_ek:
                    st.caption(f"Eklendi: {bilgi.get('eklenme','?')} ({bilgi.get('eklenme_donemi','?')})")
                with col_rm:
                    if st.button("🗑️", key=f"rm_{kod}", help="Listeden çıkar"):
                        del st.session_state.watchlist[kod]
                        st.rerun()

        if veri_yok:
            st.markdown(f"### 📋 Takip Listesi ({len(veri_yok)} hisse, veri yüklenmemiş)")
            for kod, bilgi in veri_yok:
                col_k, col_s, col_p, col_rm = st.columns([1,3,1.5,0.8])
                with col_k: st.markdown(f"**{kod}**")
                with col_s: st.caption(bilgi.get('sektor',''))
                with col_p: st.caption(f"Son puan: {bilgi.get('puan','?'):.0f} ({bilgi.get('eklenme_donemi','?')})")
                with col_rm:
                    if st.button("🗑️", key=f"rm_{kod}"):
                        del st.session_state.watchlist[kod]
                        st.rerun()

# ════════════════════════════════════════════════════════════════
# SAYFA 3: SİSTEM 8 BÖLÜM
# ════════════════════════════════════════════════════════════════
elif page == "📚 Sistem (8 Bölüm)":
    st.markdown("""<div class='fark-header'>
    <h1>📚 FARK Sistemi — 8 Bölüm Metodoloji</h1>
    <p>Fiyat Ardında Kalan Şirketler · GXSMODUJ Metodolojisi Uzantısı · v1.0</p>
    </div>""", unsafe_allow_html=True)

    bolum = st.selectbox("Bölüm seç:", [
        "B1 — Bilgi Sayfası", "B2 — Sistem Mimarisi",
        "B3 — Filtreler (F1-F4)", "B4 — Puanlama (A-B-C-D)",
        "B5 — Skor Tablosu", "B6 — Geriye Dönük Test",
        "B7 — Uygulama Kılavuzu", "B8 — Hızlı Başvuru Kartı"
    ])

    if "B1" in bolum:
        st.markdown("## Neden Geliştirildi?")
        st.info('"Bir hissenin fiyatı yükselişe geçmeden önce hangi finansal sinyaller mevcuttu? Bu sinyaller önceden tespit edilebilir miydi?"')
        st.markdown("13 yüksek getirili BIST hissesi (%9.000–%351.000 getiri) analiz edildi.")
        st.markdown("### 3 Kritik Keşif")
        col1, col2, col3 = st.columns(3)
        col1.success("**Keşif 1:** Yüksek getiri tek tip profilden gelmiyor — değer, büyüme, spekülatif hepsi %1000+ yapabiliyor.")
        col2.info("**Keşif 2:** Sürdürülebilir yükselişler YALNIZCA operasyonel büyümesi olan şirketlerden geliyor.")
        col3.warning("**Keşif 3:** En erken sinyal: FK büyümesi + fiyatın XU100 gerisinde kalması. PD/DD değil!")
        st.markdown("### İncelenen 13 Hisse")
        df_hisse = pd.DataFrame([
            ("CRDFA","Faktoring","%11.329","Operasyonel","F3 eşiği"),
            ("RYSAS","Ulaştırma","%45.060","Operasyonel","F4 TMS 29 — YENİ KURAL YAKALADI"),
            ("ASELS","Savunma","%9.852","Operasyonel","Orijinal kural yakaladı ✓"),
            ("BURVA","Sanayi","%67.436","Operasyonel","F3 eşiği"),
            ("TMPOL","Kimya","%23.842","Operasyonel","F3 eşiği"),
            ("AYES","İnşaat Malz.","%21.233","Operasyonel","F2 eksik veri"),
            ("ORMA","Orman Ürünleri","%13.995","Operasyonel","F4 TMS 29"),
            ("IZFAS","Kimya","%29.220","Operasyonel","F3 + F4 TMS 29"),
            ("UFUK","Yatırım Yön.","%158.972","Op. Holding","F1 yanlış eleme — DÜZELTİLDİ"),
            ("IEYHO","Enerji Holding","%49.050","Op. Holding","F1 yanlış eleme — DÜZELTİLDİ"),
            ("TRHOL","Finansal Holding","%351.751","Spekülatif","Doğru eleniyor ✓"),
            ("TEHOL","Finansal Holding","%79.700","Spekülatif","Doğru eleniyor ✓"),
            ("BSOKE","Çimento","%19.256","Turnaround","Doğru kaçırıyor ✓"),
        ], columns=["Hisse","Sektör","Getiri","Tip","FARK Kararı"])
        st.dataframe(df_hisse, use_container_width=True, hide_index=True)

    elif "B2" in bolum:
        st.markdown("## Sistem Mimarisi")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""<div style='background:#D6E4F0;border:2px solid #2E75B6;padding:20px;border-radius:10px;text-align:center'>
            <h3 style='color:#1B3A5C'>AŞAMA 1 — FİLTRE</h3>
            <p style='color:#2E75B6;font-size:32px;font-weight:bold'>4 Kural</p>
            <p>Biri tutmazsa hisse elenir</p></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown("""<div style='background:#E8F5E9;border:2px solid #1E7145;padding:20px;border-radius:10px;text-align:center'>
            <h3 style='color:#1B3A5C'>AŞAMA 2 — PUANLAMA</h3>
            <p style='color:#1E7145;font-size:32px;font-weight:bold'>100 Puan</p>
            <p>4 kategori değerlendirilir</p></div>""", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("**FASTWEB BİLANÇO VERİSİ → FİLTRE → PUANLAMA → KARAR (0-100)**")

    elif "B3" in bolum:
        st.markdown("## Filtreler (Kalibre Edilmiş)")
        tabs = st.tabs(["F1 — İş Modeli","F2 — Faal. Karı Devam.","F3 — Büyüme","F4 — Zarar"])
        with tabs[0]:
            st.error("**F1 — İş Modeli Filtresi**")
            st.write("Operasyonel şirket mi? Holding/GYO/Portföy elenir.")
            st.info("🔧 **Kalibrasyon:** FK son 8 çeyreğin 6+'ında pozitifse finansal holding de geçer (UFUK, IEYHO tipi)")
            st.write("**Elen:** Holding, GYO, Portföy, Menkul Kıymet, Girişim Sermayesi")
            st.write("**Geçer:** Operasyonel şirketler + FK tutarlı operasyonel holdingleri")
        with tabs[1]:
            st.error("**F2 — Faaliyet Karı Devamlılık Filtresi**")
            st.write("Son 8 çeyreğin en az 6'sında faaliyet karı pozitif mi?")
            st.info("TMS 29 enflasyon muhasebesi net karı bozabilir — bu yüzden faaliyet karı baz alınır")
            st.write("**Not:** 6 aylık raporlayan şirketlerde (AYES, ORMA) mevcut veri sayısı baz alınır")
        with tabs[2]:
            st.error("**F3 — Büyüme Varlığı Filtresi**")
            st.write("Güncel faaliyet karı, 8 çeyrek öncesine göre %20+ büyümüş mü?")
            st.info("🔧 **Kalibrasyon:** PD/DD < 1 veya FK/PD > %15 ise eşik %5'e düşer (CRDFA, TMPOL, BURVA tipi)")
        with tabs[3]:
            st.error("**F4 — Ölümcül Zarar Filtresi**")
            st.write("Son 4 çeyrekte net ve faaliyet karı sürekli negatif mi?")
            st.info("🔧 **Kalibrasyon:** NK negatif ama FK pozitifse GEÇER (TMS 29 koruması — RYSAS, ORMA tipi)")
            st.write("**Eski kural:** NK hepsi negatif → ELEN *(yanlış)*")
            st.write("**Yeni kural:** FK de negatifse → ELEN *(doğru)*")

    elif "B4" in bolum:
        st.markdown("## Puanlama Kategorileri")
        tabs = st.tabs(["A — Büyüme (35p)","B — Değer (48p)","C — Karlılık (25p)","D — Model (20p)"])
        with tabs[0]:
            df_a = pd.DataFrame([("FK 4+ yıldır büyüyor","30"),("FK 2-3 yıldır büyüyor","20"),("FK 1 yıldır büyüyor","10"),("Tutarsız/durmuş","0"),("Büyüme >%100 bonus","+5"),(">%50 bonus","+3"),(">%20 bonus","+1")], columns=["Kriter","Puan"])
            st.dataframe(df_a, hide_index=True, use_container_width=True)
        with tabs[1]:
            df_b = pd.DataFrame([("PD/DD < 1","12"),("PD/DD 1-3","9"),("PD/DD 3-6","5"),("PD/DD > 6","0"),("FK büyümesi > PD büyümesi x2","+13"),("FK büyümesi > PD büyümesi","+8"),("PD/FK oranı < 5","+10"),("PD/FK oranı < 15","+3")], columns=["Kriter","Puan"])
            st.dataframe(df_b, hide_index=True, use_container_width=True)
        with tabs[2]:
            df_c = pd.DataFrame([("Marj > %20","10"),("Marj %10-20","7"),("Marj %5-10","4"),("Marj < %5","1"),("NK/FK > %60","+8"),("NK/FK %30-60","+5"),("NK/FK > 0","+2"),("İşletme nakit akışı pozitif","+7")], columns=["Kriter","Puan"])
            st.dataframe(df_c, hide_index=True, use_container_width=True)
        with tabs[3]:
            df_d = pd.DataFrame([("Yapısal sektör (finans,enerji,sağlık,savunma)","8"),("Döngüsel ama istikrarlı (sanayi,gıda,ulaştırma)","5"),("Volatil/proje bazlı","2"),("Niş sektör (PD < 2Mr)","7"),("Orta bilinirlik (PD 2-20Mr)","4"),("Herkesin bildiği (PD > 20Mr)","1"),("Borç/Özkaynak < 1","5"),("Borç/Özkaynak 1-3","3")], columns=["Kriter","Puan"])
            st.dataframe(df_d, hide_index=True, use_container_width=True)

    elif "B5" in bolum:
        st.markdown("## Skor Tablosu ve Karar")
        df_skor = pd.DataFrame([
            ("75-100","🟢 GÜÇLÜ ADAY","Derinlemesine incele","GXSMODUJ tam analizi uygula"),
            ("55-74","🟡 POTANSİYEL","Takibe al","KAP takibi, sonraki bilançoyu bekle"),
            ("35-54","🟠 ZAYIF","Geç / Bekle","Sektör katalizörü olmadan alma"),
            ("0-34","🔴 ELENDİ","Alma","Portföye dahil etme"),
        ], columns=["Puan","Karar","Eylem","Açıklama"])
        st.dataframe(df_skor, hide_index=True, use_container_width=True)

    elif "B6" in bolum:
        st.markdown("## Geriye Dönük Test — 6/6 Doğru")
        df_test = pd.DataFrame([
            ("DSTFK","2022/12","33","25","18","18","94","✓ %1362"),
            ("KTLEV","2023/12","25","25","25","20","95","✓ %1250"),
            ("TERA","2023/12","15","25","19","18","77","✓ %2100"),
            ("GUNGD","2023/12","23","17","3","12","55","⚠ Yükseldi, bozuldu"),
            ("HEDEF","—","—","—","—","—","F1 EL.","✓ Volatil kar"),
            ("PEKGY","—","—","—","—","—","F1 EL.","✓ Zarar ediyor"),
        ], columns=["Hisse","Snapshot","A","B","C","D","TOPLAM","SONUÇ"])
        st.dataframe(df_test, hide_index=True, use_container_width=True)
        st.success("6/6 hisse doğru değerlendirildi — sistem geçerliliği kanıtlandı")

    elif "B7" in bolum:
        st.markdown("## Uygulama Kılavuzu")
        st.markdown("""
**7 Adım:**
1. Fastweb'de Puanlama Analizi ekranını aç, ilgili metrikleri seç
2. Her çeyrek dönemini Excel olarak indir
3. Scanner sekmesine gel, tüm Excel dosyalarını yükle
4. "Taramayı Başlat" butonuna tıkla
5. Güçlü Aday ve Potansiyel hisseleri incele
6. Beğendiklerini ⭐ ile takip listesine ekle
7. Yeni dönem çıkınca güncelle — bozulma otomatik uyarı verir

**Önemli Notlar:**
- 🔴 TMS 29: Net kar yanıltıcı olabilir — faaliyet karını baz al
- 🔴 Finansal şirketlerde (faktoring) bilanço yapısı farklıdır
- 🔴 Her yeni bilanço döneminde güncelle (Mart, Haziran, Eylül, Aralık)
        """)

    elif "B8" in bolum:
        st.markdown("## Hızlı Başvuru Kartı")
        st.markdown("### Aşama 1 — Filtreler")
        df_f = pd.DataFrame([
            ("F1","İş Modeli","Operasyonel şirket mi?","Bilanço","E / H"),
            ("F2","Faal. Karı","Son 8 çeyreğin 6+ tanesi pozitif?","Gelir tablosu","E / H"),
            ("F3","Büyüme","FK 2 yıl öncesine göre %20+ büyümüş?","Gelir tablosu","E / H"),
            ("F4","Zarar","FK+NK son 2 çeyrekte hepsi negatif değil?","Gelir tablosu","E / H"),
        ], columns=["#","Filtre","Kural","Kaynak","?"])
        st.dataframe(df_f, hide_index=True, use_container_width=True)
        st.markdown("### Aşama 2 — Puanlama")
        df_p = pd.DataFrame([
            ("A","Büyüme Sürekliliği","Kaç yıldır büyüyor + hız bonusu","35","___"),
            ("B","Değer Ucuzluğu","PD/DD + FK/PD oranı + rölatif fiyat","48","___"),
            ("C","Karlılık Kalitesi","Marj + NK/FK + nakit akışı","25","___"),
            ("D","İş Modeli","Sektör + bilinirlik + borç","20","___"),
        ], columns=["Kat.","Kategori","Kriter","Maks.","Puanınız"])
        st.dataframe(df_p, hide_index=True, use_container_width=True)

# ════════════════════════════════════════════════════════════════
# SAYFA 4: AYARLAR
# ════════════════════════════════════════════════════════════════
elif page == "⚙️ Ayarlar":
    st.markdown("""<div class='fark-header'>
    <h1>⚙️ Ayarlar</h1>
    <p>Güncelleme hatırlatıcıları · Takip listesi yönetimi · Sistem bilgisi</p>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📅 Güncelleme Takvimi")
        st.info("""
**Fastweb verisi ne zaman güncellenmeli?**

- **Mart** → 2024/12 bilançoları açıklandı
- **Haziran** → 2025/03 bilançoları açıklandı
- **Eylül** → 2025/06 bilançoları açıklandı
- **Aralık** → 2025/09 bilançoları açıklandı

Her çeyrek sonunda yeni dönem Excel'ini indirip sisteme yükle.
        """)

        if st.session_state.son_yukleme:
            son = datetime.fromisoformat(st.session_state.son_yukleme)
            gun = (datetime.now()-son).days
            if gun > 85:
                st.error(f"! **Veri güncellenmeli!** Son yüklemeden {gun} gün geçti.")
            elif gun > 60:
                st.warning(f"! **Güncelleme zamanı yaklaşıyor.** Son yüklemeden {gun} gün geçti.")
            else:
                st.success(f"✓ Veri güncel. Son yükleme {gun} gün önce.")

    with col2:
        st.markdown("### 📊 Mevcut Veri Durumu")
        if st.session_state.quarters:
            donems = sorted(st.session_state.quarters.keys())
            st.success(f"**{len(donems)} dönem yüklü**")
            st.write(f"İlk dönem: {donems[0][:4]}/{donems[0][4:]}")
            st.write(f"Son dönem: {donems[-1][:4]}/{donems[-1][4:]}")
            engine = st.session_state.get('engine')
            son_data_count = len(engine.son_data) if engine else 0
            st.write(f"Toplam hisse (son d\u00f6nem): {son_data_count}")
        else:
            st.warning("Henüz veri yüklenmedi")

        st.divider()
        st.markdown("### 🗑️ Veriyi Temizle")
        if st.button("Tüm Veriyi Sıfırla", type="secondary"):
            st.session_state.quarters = {}
            st.session_state.results = None
            st.session_state.elendi = None
            st.session_state.engine = None
            st.session_state.son_donem = None
            st.session_state.son_yukleme = None
            st.success("Veri temizlendi")
            st.rerun()

    st.divider()
    st.markdown("### 📌 Sistem Bilgisi")
    st.code("""FARK Sistemi v1.0
Fiyat Ardında Kalan Şirketler
GXSMODUJ Metodolojisi Uzantısı

Kalibrasyon: 13 hisse analizi (2018-2025)
F1: Operasyonel holding geçiş kuralı
F3: PD/DD<1 veya FK/PD>%15 → eşik %5
F4: TMS 29 koruması (FK pozitifse geçer)
F2: 6 aylık raporlama toleransı""", language="text")
