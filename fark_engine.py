import re
import pandas as pd
import io
import zipfile

ELENEN_SEKTORLER = ['holding', 'gayrimenkul yat', 'portf\u00f6y', 'yat\u0131r\u0131m ortakl\u0131\u011f\u0131', 'menkul k\u0131ymet', 'giri\u015fim sermayesi']

MINIMAL_STYLES = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs></styleSheet>'


def fix_xlsx_styles(file_bytes):
    try:
        buf_in = io.BytesIO(file_bytes)
        buf_out = io.BytesIO()
        with zipfile.ZipFile(buf_in, 'r') as zin:
            with zipfile.ZipFile(buf_out, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename == 'xl/styles.xml':
                        data = MINIMAL_STYLES
                    zout.writestr(item, data)
        return buf_out.getvalue()
    except Exception:
        return file_bytes


def safe_float(val):
    try: return float(str(val).replace(',', '.'))
    except: return None

def fmt_milyon(val):
    if val is None: return '-'
    if abs(val) >= 1_000_000_000_000: return f'{val/1_000_000_000_000:.1f}T'
    if abs(val) >= 1_000_000_000: return f'{val/1_000_000_000:.1f}Mr'
    if abs(val) >= 1_000_000: return f'{val/1_000_000:.0f}M'
    return f'{val:.0f}'

def karar_label(puan):
    if puan >= 75: return '\u0047\u00dc\u00c7\u004c\u00dc ADAY'
    elif puan >= 55: return 'POTANS\u0130YEL'
    elif puan >= 35: return 'ZAYIF'
    else: return 'ELEND\u0130'

def karar_emoji(puan):
    if puan >= 75: return '\U0001f7e2'
    elif puan >= 55: return '\U0001f7e1'
    elif puan >= 35: return '\U0001f7e0'
    else: return '\U0001f534'

KARAR_RENK = {
    '\u0047\u00dc\u00c7\u004c\u00dc ADAY': '#1E7145',
    'POTANS\u0130YEL': '#B8860B',
    'ZAYIF': '#E65100',
    'ELEND\u0130': '#C00000',
}

KARAR_BG = {
    '\u0047\u00dc\u00c7\u004c\u00dc ADAY': '#C8E6C9',
    'POTANS\u0130YEL': '#FFFDE7',
    'ZAYIF': '#FFE0B2',
    'ELEND\u0130': '#FFCDD2',
}

def read_excel_bytes(file_bytes):
    file_bytes = fix_xlsx_styles(file_bytes)
    try:
        df = pd.read_excel(io.BytesIO(file_bytes), header=None, engine='openpyxl')
    except Exception:
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), header=None)
        except Exception:
            return {}
    data = {}
    header = None
    for _, row in df.iterrows():
        row_list = [str(v).strip() if pd.notna(v) else '' for v in row]
        if row_list and row_list[0] == 'Kod':
            header = row_list
            continue
        if header and len(row_list) >= 2 and row_list[0]:
            row_dict = {header[i]: row_list[i] if i < len(row_list) else '' for i in range(len(header))}
            kod = row_dict.get('Kod', '').strip()
            if kod and kod != 'nan': data[kod] = row_dict
    return data

def donem_from_filename(filename):
    name = (filename
            .replace('Puanlama_Analizi_Tu_mu__', '')
            .replace('.xlsx', '')
            .replace('__1_', '')
            .replace('_1_', '')
            .strip())
    if name.isdigit() and len(name) == 6:
        return name
    match = re.search(r'(\d{6})', filename)
    if match:
        return match.group(1)
    return None

class FARKEngine:
    def __init__(self, quarters_data):
        self.quarters = quarters_data
        self.sorted_donems = sorted(quarters_data.keys())
        self.son_donem = self.sorted_donems[-1] if self.sorted_donems else None
        self.son_data = quarters_data.get(self.son_donem, {}) if self.son_donem else {}

    def f1_check(self, sektor, fk_seri):
        s = sektor.lower()
        finansal = any(e in s for e in ELENEN_SEKTORLER)
        if not finansal: return True, 'Operasyonel OK'
        valid = [x for x in fk_seri if x is not None]
        if len(valid) >= 6 and sum(1 for x in valid[-8:] if x > 0) >= 6:
            return True, 'Operasyonel Holding (FK tutarli) OK'
        return False, 'Finansal Holding/GYO ELENDI'

    def f2_check(self, fk_seri):
        son8 = [x for x in fk_seri[-8:] if x is not None]
        if len(son8) < 4: return False, f'Yetersiz veri ({len(son8)}/8)'
        pozitif = sum(1 for x in son8 if x > 0)
        esik = max(4, int(len(son8) * 0.6))
        if pozitif >= esik: return True, f'{pozitif}/{len(son8)} ceyrek pozitif OK'
        return False, f'{pozitif}/{len(son8)} pozitif (min {esik}) ELENDI'

    def f3_check(self, fk_seri, fk_son, pddd, fkpd):
        if not fk_son or fk_son <= 0: return False, 'Guncel FK <= 0 ELENDI'
        eski_idx = max(0, len(fk_seri)-9)
        fk_eski = next((fk_seri[i] for i in range(eski_idx, min(eski_idx+3, len(fk_seri)))
                        if fk_seri[i] and fk_seri[i] > 0), None)
        if not fk_eski: return False, '2 yil oncesi FK verisi yok ELENDI'
        buyume = (fk_son - fk_eski) / abs(fk_eski) * 100
        esik = 5 if ((pddd and pddd < 1) or (fkpd and fkpd > 15)) else 20
        if buyume >= esik: return True, f'+{buyume:.0f}% buyume (esik %{esik}) OK'
        return False, f'{buyume:.0f}% buyume (min %{esik}) ELENDI'

    def f4_check(self, fk_seri, nk_seri):
        son4_nk = [x for x in nk_seri[-4:] if x is not None]
        son4_fk = [x for x in fk_seri[-4:] if x is not None]
        if len(son4_nk) < 4: return True, 'Yetersiz veri'
        if not all(x < 0 for x in son4_nk): return True, 'NK en az 1 ceyrekte pozitif OK'
        if len(son4_fk) >= 2 and all(x < 0 for x in son4_fk[-2:]):
            return False, 'FK+NK son 2 ceyrekte negatif ELENDI'
        return True, 'NK negatif ama FK pozitif (TMS 29) OK'

    def hesapla_puan(self, kod):
        son = self.son_data.get(kod, {})
        if not son: return None, {}

        FK_KEY = 'Esas Faaliyet Kar\u0131 /Zarar\u0131 Net (Y\u0131ll\u0131k)'
        NK_KEY = 'Net D\u00f6nem Kar\u0131 / Zarar\u0131 (Y\u0131ll\u0131k)'
        MARJ_KEY = 'Esas Faaliyet Kar Marj\u0131 (Y\u0131ll\u0131k)'
        PDDD_KEY = 'Piyasa De\u011feri / Defter De\u011feri'
        BODE_KEY = 'Toplam Bor\u00e7 / \u00d6zsermaye'
        NAKIT_KEY = '\u0130\u015fletme Faaliyetlerinden Nakit Ak\u0131\u015flar\u0131'
        PD_KEY = 'Piyasa De\u011feri'
        SEKTOR_KEY = 'Hisse Sekt\u00f6r'

        fk_son = safe_float(son.get(FK_KEY, ''))
        nk_son = safe_float(son.get(NK_KEY, ''))
        marj   = safe_float(son.get(MARJ_KEY, ''))
        pddd   = safe_float(son.get(PDDD_KEY, ''))
        bode   = safe_float(son.get(BODE_KEY, ''))
        nakit  = safe_float(son.get(NAKIT_KEY, ''))
        pd_val = safe_float(son.get(PD_KEY, ''))
        sektor = son.get(SEKTOR_KEY, '')
        fkpd   = (fk_son/pd_val*100) if fk_son and pd_val and pd_val>0 and fk_son>0 else None

        fk_seri, nk_seri, pd_seri = [], [], []
        for d in self.sorted_donems:
            row = self.quarters[d].get(kod, {})
            fk_seri.append(safe_float(row.get(FK_KEY, '')))
            nk_seri.append(safe_float(row.get(NK_KEY, '')))
            pd_seri.append(safe_float(row.get(PD_KEY, '')))

        f1_gec, f1_msg = self.f1_check(sektor, fk_seri)
        if not f1_gec: return 'F1', {'msg': f1_msg, 'sektor': sektor}

        f2_gec, f2_msg = self.f2_check(fk_seri)
        if not f2_gec: return 'F2', {'msg': f2_msg, 'sektor': sektor}

        f3_gec, f3_msg = self.f3_check(fk_seri, fk_son, pddd, fkpd)
        if not f3_gec: return 'F3', {'msg': f3_msg, 'sektor': sektor}

        f4_gec, f4_msg = self.f4_check(fk_seri, nk_seri)
        if not f4_gec: return 'F4', {'msg': f4_msg, 'sektor': sektor}

        eski_idx = max(0, len(fk_seri)-9)
        fk_eski = next((fk_seri[i] for i in range(eski_idx, min(eski_idx+3, len(fk_seri)))
                        if fk_seri[i] and fk_seri[i]>0), None)
        buyume_pct = ((fk_son-fk_eski)/abs(fk_eski)*100) if fk_eski and fk_son and fk_son>0 else 0

        buyuyen = sum(1 for i in range(1, len(fk_seri))
                      if fk_seri[i-1] and fk_seri[i] and fk_seri[i-1]>0 and fk_seri[i]>fk_seri[i-1])
        br = buyuyen / (len(fk_seri)-1 or 1)
        a = 30 if br>=0.8 else (20 if br>=0.6 else (10 if br>=0.4 else 0))
        if buyume_pct >= 200: a += 5
        elif buyume_pct >= 100: a += 3
        elif buyume_pct >= 50: a += 1
        a = min(a, 35)

        b = 0
        if pddd:
            if pddd<1: b+=12
            elif pddd<3: b+=9
            elif pddd<6: b+=5
        pd_eski = next((pd_seri[i] for i in range(eski_idx, min(eski_idx+3, len(pd_seri)))
                        if pd_seri[i] and pd_seri[i]>0), None)
        if pd_eski and pd_val and pd_val>0:
            pd_buy = (pd_val-pd_eski)/pd_eski*100
            if buyume_pct > pd_buy*2: b+=13
            elif buyume_pct > pd_buy: b+=8
        if pd_val and fk_son and fk_son>0:
            r = pd_val/fk_son
            if r<5: b+=10
            elif r<15: b+=3
        b = min(b, 48)

        c = 0
        if marj:
            if marj>20: c+=10
            elif marj>10: c+=7
            elif marj>5: c+=4
            else: c+=1
        if fk_son and fk_son>0 and nk_son is not None:
            rn = nk_son/fk_son*100
            if rn>60: c+=8
            elif rn>30: c+=5
            elif rn>0: c+=2
            else: c+=1
        elif fk_son and fk_son>0: c+=1
        if nakit and nakit>0: c+=7
        c = min(c, 25)

        d = 0
        s = sektor.lower()
        if any(x in s for x in ['finans', 'faktoring', 'tasarruf', 'sigorta', 'enerji',
                                  'sa\u011fl\u0131k', 'ila\u00e7', 'su', 'elektrik', 'savunma', 'ileti\u015fim']):
            d += 8
        elif any(x in s for x in ['sanayi', 'tekstil', 'g\u0131da', 'i\u00e7ecek', 'perakende',
                                    'ula\u015ft\u0131rma', 'kimya', 'mobilya', 'orman', '\u00e7imento']):
            d += 5
        else: d += 2
        if pd_val:
            if pd_val<2_000_000_000: d+=7
            elif pd_val<20_000_000_000: d+=4
            else: d+=1
        if bode:
            if bode<100: d+=5
            elif bode<300: d+=3
        d = min(d, 20)

        toplam = round(a+b+c+d, 1)

        return toplam, {
            'sektor': sektor, 'fk': fk_son, 'nk': nk_son, 'pd': pd_val,
            'pddd': pddd, 'marj': marj, 'fkpd': fkpd, 'nakit': nakit,
            'buyume_pct': buyume_pct, 'A': a, 'B': b, 'C': c, 'D': d,
            'f1_msg': f1_msg, 'f2_msg': f2_msg, 'f3_msg': f3_msg, 'f4_msg': f4_msg,
        }

    def tara(self):
        sonuclar, elendi = [], {'F1': [], 'F2': [], 'F3': [], 'F4': []}
        for kod in sorted(self.son_data.keys()):
            puan, detay = self.hesapla_puan(kod)
            if puan in ['F1', 'F2', 'F3', 'F4']:
                elendi[puan].append(kod)
            elif puan is not None:
                oran = (detay['fk']/detay['pd']*100) if detay.get('fk') and detay.get('pd') and detay['pd']>0 else None
                sonuclar.append({
                    'Kod': kod,
                    'Sekt\u00f6r': detay.get('sektor', ''),
                    'Puan': puan,
                    'Karar': karar_label(puan),
                    'A': detay['A'], 'B': detay['B'], 'C': detay['C'], 'D': detay['D'],
                    'Faal.Kar\u0131': fmt_milyon(detay.get('fk')),
                    'Piy.De\u011feri': fmt_milyon(detay.get('pd')),
                    'PD/DD': f"{detay['pddd']:.1f}" if detay.get('pddd') else '-',
                    'FK/PD%': f"{oran:.1f}" if oran else '-',
                    'Marj%': f"{detay['marj']:.1f}" if detay.get('marj') else '-',
                    'B\u00fcy\u00fcme%': f"+{detay['buyume_pct']:.0f}" if detay.get('buyume_pct', '') != '' else '-',
                    '_fk_raw': detay.get('fk'), '_pd_raw': detay.get('pd'),
                    '_oran_raw': oran,
                })
        sonuclar.sort(key=lambda x: x['Puan'], reverse=True)
        return sonuclar, elendi

    def bozulma_kontrol(self, kod, onceki_puan):
        puan, detay = self.hesapla_puan(kod)
        uyarilar = []
        if puan in ['F1', 'F2', 'F3', 'F4']:
            uyarilar.append(f'{puan} filtresinde elendi: {detay.get("msg", "")}')
            return uyarilar, None
        if puan is None:
            uyarilar.append('Veri bulunamadi')
            return uyarilar, None
        if onceki_puan and puan < onceki_puan - 10:
            uyarilar.append(f'Puan dustu: {onceki_puan:.0f} -> {puan:.0f}')
        if detay.get('fk') and detay['fk'] < 0:
            uyarilar.append('Faaliyet kari negatife dondu')
        if (detay.get('buyume_pct', '') != ''
                and isinstance(detay.get('buyume_pct'), (int, float))
                and detay['buyume_pct'] < 0):
            uyarilar.append(f'FK buyumesi negatif: {detay["buyume_pct"]:.0f}%')
        return uyarilar, puan
