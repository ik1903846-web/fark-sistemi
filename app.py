import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime

from fark_engine import (FARKEngine, karar_label, karar_emoji, KARAR_RENK, KARAR_BG,
                          read_excel_bytes, donem_from_filename, fmt_milyon, safe_float)

st.set_page_config(page_title="FARK Sistemi", page_icon="📊", layout="wide")

st.markdown("""
<style>
.fark-header { background: linear-gradient(135deg, #1B3A5C, #2E75B6);
  color: white; padding: 16px 24px; border-radius: 10px; margin-bottom: 20px; }
.fark-header h1 { margin: 0; font-size: 28px; }
.fark-header p { margin: 4px 0 0 0; opacity: 0.85; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

for k, v in [('watchlist', {}), ('quarters', {}), ('results', None),
              ('elendi', None), ('son_donem', None), ('son_yukleme', None),
              ('engine', None)]:
    if k not in st.session_state: st.session_state[k] = v

with st.sidebar:
    st.markdown("## 📊 FARK Sistemi")
    st.markdown("*Fiyat Ardında Kalan Şirketler*")
    st.divider()
    page = st.radio("", ["🔍 Scanner", "⭐ Takip Listesi", "📚 Sistem (8 Bölüm)", "⚙️ Ayarlar"],
                    label_visibility="collapsed")
    st.divider()
    if st.session_state.son_yukleme:
        son = datetime.fromisoformat(st.session_state.son_yukleme)
        gun_fark = (datetime.now() - son).days
        if gun_fark > 85:
            st.warning(f"! **Veri güncelle**\nSon: {son.strftime('%Y/%m')}\n{gun_fark} gün önce")
        else:
            st.info(f"✓ Son veri: {son.strftime('%Y/%m/%d')}")
    else:
        st.info("📁 Henüz veri yüklenmedi")
    if st.session_state.watchlist:
        st.divider()
        st.markdown(f"⭐ **{len(st.session_state.watchlist)} hisse** takipte")
    st.divider()
    st.markdown("<small>v1.0 · GXSMODUJ</small>", unsafe_allow_html=True)
if page == "🔍 Scanner":
    st.markdown("""<div class='fark-header'>
    <h1>📊 FARK Scanner</h1>
    <p>Fastweb Excel dosyalarını yükle · Otomatik tara · ⭐ tek tıkla takip ekle</p>
    </div>""", unsafe_allow_html=True)

    with st.expander("📁 Veri Yükle", expanded=not bool(st.session_state.results)):
        uploaded = st.file_uploader("Puanlama_Analizi_Tu_mu__YYYYMM.xlsx",
                                     type=['xlsx'], accept_multiple_files=True)
        if uploaded:
            col1, col2 = st.columns([3,1])
            with col1:
                st.write(f"{len(uploaded)} dosya seçildi")
            with col2:
                if st.button("🚀 Taramayı Başlat", type="primary", use_container_width=True):
                    with st.spinner("İşleniyor..."):
                        quarters = {}
                        for f in uploaded:
                            donem = donem_from_filename(f.name)
                            if donem:
                                data = read_excel_bytes(f.read())
                                if data: quarters[donem] = data
                        if quarters:
                            engine = FARKEngine(quarters)
                            results, elendi = engine.tara()
                            st.session_state.quarters = quarters
                            st.session_state.engine = engine
                            st.session_state.results = results
                            st.session_state.elendi = elendi
                            st.session_state.son_donem = engine.son_donem
                            st.session_state.son_yukleme = datetime.now().isoformat()
                            st.success(f"✓ {len(quarters)} dönem · {len(results)} hisse geçti")
                            st.rerun()
                        else:
                            st.error("Dosya formatı tanınamadı.")
    if st.session_state.results is not None:
        results = st.session_state.results
        elendi = st.session_state.elendi or {}
        son_donem = st.session_state.son_donem

        guclu = [r for r in results if r['Puan'] >= 75]
        pot   = [r for r in results if 55 <= r['Puan'] < 75]
        zayif = [r for r in results if 35 <= r['Puan'] < 55]

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("🟢 Güçlü", len(guclu))
        c2.metric("🟡 Potansiyel", len(pot))
        c3.metric("🟠 Zayıf", len(zayif))
        c4.metric("📊 Toplam", len(results))
        c5.metric("❌ Elenen", sum(len(v) for v in elendi.values()))
        st.divider()

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            karar_filtre = st.multiselect("Karar", ["GÜÇLÜ ADAY","POTANSİYEL","ZAYIF","ELENDİ"],
                                           default=["GÜÇLÜ ADAY","POTANSİYEL"])
        with col_f2:
            sektor_listesi = sorted(list(set(r['Sektör'] for r in results if r['Sektör'])))
            sektor_filtre = st.multiselect("Sektör", sektor_listesi)
        with col_f3:
            siralama = st.selectbox("Sırala", ["FARK Puanı ↓", "FK/PD% ↓", "Büyüme% ↓"])

        goster = [r for r in results if r['Karar'] in karar_filtre]
        if sektor_filtre:
            goster = [r for r in goster if r['Sektör'] in sektor_filtre]
        if siralama == "FK/PD% ↓":
            goster.sort(key=lambda x: float(x.get('FK/PD%','0').replace('-','0') or 0), reverse=True)
        elif siralama == "Büyüme% ↓":
            goster.sort(key=lambda x: float(x.get('Büyüme%','0').replace('+','').replace('-','0') or 0), reverse=True)

        st.markdown(f"**{len(goster)} hisse** · Dönem: {son_donem}")
        st.divider()
        for r in goster:
            kod = r['Kod']
            puan = r['Puan']
            kd = r['Karar']
            emoji = karar_emoji(puan)
            in_wl = kod in st.session_state.watchlist
            renk = KARAR_RENK.get(kd, '#555')
            bg   = KARAR_BG.get(kd, '#eee')

            col_kod, col_sek, col_puan, col_abcd, col_fk, col_pd, col_oran, col_btn = st.columns([1.2,2.5,0.9,2,1.3,1.3,1.1,1])
            with col_kod: st.markdown(f"**{kod}**")
            with col_sek: st.markdown(f"<small>{r['Sektör']}</small>", unsafe_allow_html=True)
            with col_puan:
                st.markdown(f"<span style='background:{bg};color:{renk};padding:3px 8px;border-radius:10px;font-weight:bold'>{emoji} {puan}</span>", unsafe_allow_html=True)
            with col_abcd:
                st.markdown(f"<small>A:{r['A']} B:{r['B']} C:{r['C']} D:{r['D']}</small>", unsafe_allow_html=True)
            with col_fk:
                st.markdown(f"<small>FK:{r['Faal.Karı']}</small>", unsafe_allow_html=True)
            with col_pd:
                st.markdown(f"<small>PD:{r['Piy.Değeri']}</small>", unsafe_allow_html=True)
            with col_oran:
                oran_val = r.get('FK/PD%','-')
                try: oran_renk = '#1E7145' if float(oran_val) > 10 else '#555'
                except: oran_renk = '#555'
                st.markdown(f"<small style='color:{oran_renk}'><b>{oran_val}%</b></small>", unsafe_allow_html=True)
            with col_btn:
                if in_wl:
                    if st.button("⭐", key=f"wl_{kod}", help="Çıkar"):
                        del st.session_state.watchlist[kod]
                        st.rerun()
                else:
                    if st.button("☆", key=f"wl_{kod}", help="Takibe ekle"):
                        st.session_state.watchlist[kod] = {
                            'puan': puan, 'karar': kd, 'sektor': r['Sektör'],
                            'eklenme': datetime.now().strftime('%Y-%m-%d'),
                            'eklenme_donemi': son_donem,
                        }
                        st.toast(f"⭐ {kod} eklendi!", icon="✅")
                        st.rerun()

        st.divider()
        with st.expander("❌ Elenen Hisseler"):
            c1,c2,c3,c4 = st.columns(4)
            for col, (filtre, lst) in zip([c1,c2,c3,c4], elendi.items()):
                with col:
                    st.markdown(f"**{filtre}**: {len(lst)}")
                    st.caption(", ".join(lst[:15]) + ("..." if len(lst)>15 else ""))
elif page == "⭐ Takip Listesi":
    st.markdown("""<div class='fark-header'>
    <h1>⭐ Takip Listesi</h1>
    <p>Yıldızladığın hisseler · Yeni veri yüklenince otomatik bozulma kontrolü</p>
    </div>""", unsafe_allow_html=True)

    if not st.session_state.watchlist:
        st.info("Henüz hisse eklemedin. Scanner'dan ☆ butonuyla ekleyebilirsin.")
    else:
        col_exp, col_imp = st.columns(2)
        with col_exp:
            wl_json = json.dumps(st.session_state.watchlist, ensure_ascii=False, indent=2)
            st.download_button("💾 Listeyi İndir", wl_json,
                                file_name="fark_takip.json", mime="application/json")
        with col_imp:
            imp = st.file_uploader("📂 Liste Yükle", type=['json'], label_visibility="collapsed")
            if imp:
                try:
                    loaded = json.loads(imp.read())
                    st.session_state.watchlist.update(loaded)
                    st.success(f"✓ {len(loaded)} hisse yüklendi")
                    st.rerun()
                except: st.error("Hatalı dosya")

        st.divider()
        engine = st.session_state.engine
        has_engine = engine is not None
        if not has_engine:
            st.warning("⚠️ Bozulma kontrolü için Scanner'da veri yükle.")

        bozulan, temiz, veri_yok = [], [], []
        for kod, bilgi in st.session_state.watchlist.items():
            if has_engine:
                uyarilar, yeni_puan = engine.bozulma_kontrol(kod, bilgi.get('puan'))
                if uyarilar: bozulan.append((kod, bilgi, uyarilar, yeni_puan))
                else: temiz.append((kod, bilgi, yeni_puan))
            else:
                veri_yok.append((kod, bilgi))

        if bozulan:
            st.markdown(f"### 🚨 Bozulma Uyarısı — {len(bozulan)} Hisse")
            for kod, bilgi, uyarilar, yeni_puan in bozulan:
                st.error(f"**⚠️ {kod}** — {bilgi.get('sektor','')} | "
                         f"{bilgi.get('puan','?'):.0f}p → {yeni_puan:.0f}p\n\n" +
                         "\n".join(uyarilar))
                if yeni_puan: st.session_state.watchlist[kod]['puan'] = yeni_puan
                if st.button("🗑️ Çıkar", key=f"rm_{kod}"): 
                    del st.session_state.watchlist[kod]; st.rerun()
            st.divider()

        if temiz:
            st.markdown(f"### ✅ Takip Listesi — {len(temiz)} Hisse")
            for kod, bilgi, yeni_puan in temiz:
                puan = yeni_puan or bilgi.get('puan', 0)
                kd = karar_label(puan) if yeni_puan else bilgi.get('karar','')
                renk = KARAR_RENK.get(kd, '#555')
                bg = KARAR_BG.get(kd, '#eee')
                col_k,col_s,col_p,col_ek,col_rm = st.columns([1,2.5,1.2,2,0.8])
                with col_k: st.markdown(f"**{kod}**")
                with col_s: st.caption(bilgi.get('sektor',''))
                with col_p:
                    st.markdown(f"<span style='background:{bg};color:{renk};padding:3px 8px;border-radius:10px;font-weight:bold'>{karar_emoji(puan)} {puan:.0f}</span>", unsafe_allow_html=True)
                with col_ek: st.caption(f"{bilgi.get('eklenme_donemi','?')}")
                with col_rm:
                    if st.button("🗑️", key=f"rm_{kod}"):
                        del st.session_state.watchlist[kod]; st.rerun()

        if veri_yok:
            st.markdown(f"### 📋 {len(veri_yok)} hisse (veri bekleniyor)")
            for kod, bilgi in veri_yok:
                col_k,col_s,col_p,col_rm = st.columns([1,3,1.5,0.8])
                with col_k: st.markdown(f"**{kod}**")
                with col_s: st.caption(bilgi.get('sektor',''))
                with col_p: st.caption(f"{bilgi.get('puan','?'):.0f}p ({bilgi.get('eklenme_donemi','?')})")
                with col_rm:
                    if st.button("🗑️", key=f"rm_{kod}"):
                        del st.session_state.watchlist[kod]; st.rerun()
elif page == "📚 Sistem (8 Bölüm)":
    st.markdown("""<div class='fark-header'>
    <h1>📚 FARK Sistemi — 8 Bölüm</h1>
    <p>Fiyat Ardında Kalan Şirketler · GXSMODUJ Metodolojisi · v1.0</p>
    </div>""", unsafe_allow_html=True)

    bolum = st.selectbox("Bölüm:", [
        "B1 — Bilgi Sayfası","B2 — Sistem Mimarisi",
        "B3 — Filtreler","B4 — Puanlama",
        "B5 — Skor Tablosu","B6 — Geriye Dönük Test",
        "B7 — Uygulama Kılavuzu","B8 — Hızlı Başvuru Kartı"
    ])

    if "B1" in bolum:
        st.info('"Bir hissenin fiyatı yükselişe geçmeden önce hangi finansal sinyaller mevcuttu?"')
        st.markdown("### 3 Kritik Keşif")
        st.success("**Keşif 1:** Yüksek getiri tek tip profilden gelmiyor.")
        st.info("**Keşif 2:** Sürdürülebilir yükselişler YALNIZCA operasyonel büyümesi olan şirketlerden geliyor.")
        st.warning("**Keşif 3:** En erken sinyal: FK büyümesi + fiyatın XU100 gerisinde kalması.")
        st.markdown("### Kalibrasyon — 13 Hisse")
        df = pd.DataFrame([
            ("CRDFA","%11.329","F3 eşiği"),("RYSAS","%45.060","F4 TMS 29 — YENİ KURAL"),
            ("ASELS","%9.852","Orijinal kural ✓"),("BURVA","%67.436","F3 eşiği"),
            ("TMPOL","%23.842","F3 eşiği"),("AYES","%21.233","F2 eksik veri"),
            ("ORMA","%13.995","F4 TMS 29"),("IZFAS","%29.220","F3+F4"),
            ("UFUK","%158.972","F1 düzeltildi"),("IEYHO","%49.050","F1 düzeltildi"),
            ("TRHOL","%351.751","Doğru eleniyor ✓"),("TEHOL","%79.700","Doğru eleniyor ✓"),
            ("BSOKE","%19.256","Doğru kaçırıyor ✓"),
        ], columns=["Hisse","Getiri","FARK Kararı"])
        st.dataframe(df, hide_index=True, use_container_width=True)

    elif "B2" in bolum:
        col1,col2 = st.columns(2)
        col1.info("### AŞAMA 1 — FİLTRE\n4 kural — biri tutmazsa elenir")
        col2.success("### AŞAMA 2 — PUANLAMA\n4 kategori — toplam 100 puan")
        st.markdown("**FASTWEB VERİSİ → FİLTRE → PUANLAMA → KARAR (0-100)**")

    elif "B3" in bolum:
        tabs = st.tabs(["F1","F2","F3","F4"])
        with tabs[0]:
            st.error("**F1 — İş Modeli**")
            st.write("Operasyonel şirket mi?")
            st.info("🔧 Kalibrasyon: FK 8 çeyreğin 6+'ında pozitifse holding de geçer")
        with tabs[1]:
            st.error("**F2 — Faaliyet Karı Devamlılık**")
            st.write("Son 8 çeyreğin 6+'ında FK pozitif mi?")
        with tabs[2]:
            st.error("**F3 — Büyüme Varlığı**")
            st.write("FK 2 yıl öncesine göre %20+ büyümüş mü?")
            st.info("🔧 Kalibrasyon: PD/DD<1 veya FK/PD>%15 ise eşik %5'e düşer")
        with tabs[3]:
            st.error("**F4 — Ölümcül Zarar**")
            st.write("FK+NK son 2 çeyrekte hepsi negatif mi?")
            st.info("🔧 Kalibrasyon: NK negatif ama FK pozitifse TMS 29 etkisi → GEÇER")

    elif "B4" in bolum:
        tabs = st.tabs(["A(35p)","B(48p)","C(25p)","D(20p)"])
        with tabs[0]:
            st.dataframe(pd.DataFrame([("4+ yıl büyüme","30"),(("2-3 yıl","20")),("1 yıl","10"),("Tutarsız","0"),(">%100 bonus","+5"),(">%50","+3"),(">%20","+1")],columns=["Kriter","Puan"]),hide_index=True)
        with tabs[1]:
            st.dataframe(pd.DataFrame([("PD/DD<1","12"),("PD/DD 1-3","9"),("PD/DD 3-6","5"),("FK büyümesi>PD x2","+13"),("FK büyümesi>PD","+8"),("PD/FK<5","+10"),("PD/FK<15","+3")],columns=["Kriter","Puan"]),hide_index=True)
        with tabs[2]:
            st.dataframe(pd.DataFrame([("Marj>%20","10"),("Marj %10-20","7"),("NK/FK>%60","+8"),("NK/FK %30-60","+5"),("Nakit akışı pozitif","+7")],columns=["Kriter","Puan"]),hide_index=True)
        with tabs[3]:
            st.dataframe(pd.DataFrame([("Yapısal sektör","8"),("Döngüsel","5"),("Niş PD<2Mr","7"),("Orta PD 2-20Mr","4"),("Borç/Özk<1","5")],columns=["Kriter","Puan"]),hide_index=True)

    elif "B5" in bolum:
        st.dataframe(pd.DataFrame([("75-100","🟢 GÜÇLÜ ADAY","GXSMODUJ analizi uygula"),("55-74","🟡 POTANSİYEL","KAP takibi"),("35-54","🟠 ZAYIF","Katalizör bekle"),("0-34","🔴 ELENDİ","Alma")],columns=["Puan","Karar","Eylem"]),hide_index=True,use_container_width=True)

    elif "B6" in bolum:
        st.success("6/6 hisse doğru değerlendirildi")
        st.dataframe(pd.DataFrame([("DSTFK","94p","✓ %1362"),("KTLEV","95p","✓ %1250"),("TERA","77p","✓ %2100"),("GUNGD","55p","⚠ Bozuldu"),("HEDEF","F1 EL.","✓"),("PEKGY","F1 EL.","✓")],columns=["Hisse","Puan","Sonuç"]),hide_index=True,use_container_width=True)

    elif "B7" in bolum:
        st.markdown("""
1. Fastweb'den Excel indir (her çeyrek)
2. Scanner → Dosyaları yükle → Taramayı Başlat
3. Güçlü Aday / Potansiyel hisseleri incele
4. ⭐ ile takip listesine ekle
5. Yeni dönem çıkınca güncelle → bozulma otomatik uyarı verir

**⚠️ TMS 29:** Net kar yanıltıcı olabilir — faaliyet karını baz al
        """)

    elif "B8" in bolum:
        st.dataframe(pd.DataFrame([("F1","Operasyonel mi?","E/H"),("F2","6+ çeyrek FK pozitif?","E/H"),("F3","FK %20+ büyümüş?","E/H"),("F4","FK+NK negatif değil?","E/H")],columns=["Filtre","Kural","?"]),hide_index=True,use_container_width=True)
        st.dataframe(pd.DataFrame([("A","Büyüme","35","___"),("B","Değer","48","___"),("C","Karlılık","25","___"),("D","Model","20","___")],columns=["Kat.","Kategori","Maks.","Puanınız"]),hide_index=True,use_container_width=True)
elif page == "⚙️ Ayarlar":
    st.markdown("""<div class='fark-header'>
    <h1>⚙️ Ayarlar</h1>
    <p>Güncelleme hatırlatıcıları · Veri durumu · Sistem bilgisi</p>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📅 Güncelleme Takvimi")
        st.info("""
**Ne zaman güncellenmeli?**
- **Mart** → Aralık bilançoları
- **Haziran** → Mart bilançoları  
- **Eylül** → Haziran bilançoları
- **Aralık** → Eylül bilançoları
        """)
        if st.session_state.son_yukleme:
            son = datetime.fromisoformat(st.session_state.son_yukleme)
            gun = (datetime.now()-son).days
            if gun > 85:
                st.error(f"! Veri güncellenmeli! {gun} gün geçti.")
            elif gun > 60:
                st.warning(f"! Güncelleme yaklaşıyor. {gun} gün geçti.")
            else:
                st.success(f"✓ Veri güncel. {gun} gün önce yüklendi.")

    with col2:
        st.markdown("### 📊 Veri Durumu")
        if st.session_state.quarters:
            donems = sorted(st.session_state.quarters.keys())
            st.success(f"**{len(donems)} dönem yüklü**")
            st.write(f"İlk: {donems[0][:4]}/{donems[0][4:]}")
            st.write(f"Son: {donems[-1][:4]}/{donems[-1][4:]}")
            st.write(f"Hisse sayısı: {len(st.session_state.son_data or {})}")
        else:
            st.warning("Henüz veri yüklenmedi")
        st.divider()
        if st.button("🗑️ Veriyi Sıfırla"):
            for k in ['quarters','results','elendi','engine','son_donem','son_yukleme']:
                st.session_state[k] = None if k not in ['quarters','results','elendi'] else {} if k == 'quarters' else None
            st.success("Temizlendi")
            st.rerun()

    st.divider()
    st.code("""FARK Sistemi v1.0
Kalibrasyon: 13 hisse (2018-2025)
F1: Operasyonel holding geçiş kuralı
F3: PD/DD<1 veya FK/PD>%15 → eşik %5
F4: TMS 29 koruması""", language="text")
