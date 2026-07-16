import random
import re
import streamlit as st
import pandas as pd

# ------------------------------------------------------------
# SAYFA AYARLARI
# ------------------------------------------------------------
st.set_page_config(
    page_title="Sorgu Paneli",
    page_icon="",
    layout="wide",
)

# ------------------------------------------------------------
# ÖZEL GÖRÜNÜM (CSS) — daha büyük yazılar, geniş dosya yükleme alanı
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    .baslik {
        text-align: center;
        font-size: 2.6rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .altbaslik {
        text-align: center;
        color: #6b7280;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    /* Dosya yükleme kutusu: büyük, mor, kesikli çerçeve */
    div[data-testid="stFileUploaderDropzone"] {
        border: 3px dashed #4f46e5;
        border-radius: 18px;
        padding: 2.5rem;
        background-color: #f5f6ff;
    }
    div[data-testid="stFileUploaderDropzone"] * {
        font-size: 1.15rem !important;
    }
    /* Arama kutusu: büyük yazı, büyük kutu */
    div[data-testid="stTextInput"] input {
        font-size: 1.4rem !important;
        padding: 0.9rem 1rem !important;
        border-radius: 12px !important;
        border: 2px solid #4f46e5 !important;
    }
    /* Sonuç tablosu başlığı (expander) büyük yazı */
    div[data-testid="stExpander"] summary {
        font-size: 1.3rem !important;
        font-weight: 700 !important;
    }
    /* Tablo hücrelerindeki yazı biraz büyüsün */
    div[data-testid="stDataFrame"] * {
        font-size: 1.02rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# TÜRKÇE BÜYÜK/KÜÇÜK HARF + BOŞLUK DUYARSIZ NORMALLEŞTİRME
# ------------------------------------------------------------
TR_DEGISIM = {"İ": "i", "I": "ı", "Ş": "ş", "Ğ": "ğ", "Ü": "ü", "Ö": "ö", "Ç": "ç"}


def normallestir(metin: str) -> str:
    """Türkçe karaktere duyarlı biçimde küçük harfe çevirir ve TÜM boşlukları siler.
    Böylece 'Model Teknoloji', 'MODEL  TEKNOLOJİ', 'modelteknoloji' hepsi eşleşir."""
    metin = str(metin)
    for buyuk, kucuk in TR_DEGISIM.items():
        metin = metin.replace(buyuk, kucuk)
    metin = metin.lower()
    metin = re.sub(r"\s+", "", metin)
    return metin


# ------------------------------------------------------------
# BAŞLIK
# ------------------------------------------------------------
st.markdown('<div class="baslik">📁 Sorgu Paneli</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="altbaslik">Bir Excel dosyası yükleyin, ardından aramak istediğiniz kaydı yazın</div>',
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# 1) BÜYÜK, ORTALANMIŞ DOSYA YÜKLEME ŞABLONU
# ------------------------------------------------------------
yuklenen_dosya = st.file_uploader(
    "Excel dosyanızı buraya sürükleyin ya da seçmek için tıklayın",
    type=["xlsx", "xls"],
)

# ------------------------------------------------------------
# 2) SABİT ARAMA ÇUBUĞU (form: sadece 'Ara'ya basınca ya da Enter'a
#    basınca çalışır, her tuş vuruşunda değil — bu sayede arama sayısını
#    doğru sayabiliyoruz)
# ------------------------------------------------------------
st.write("")

if "arama_sayaci" not in st.session_state:
    st.session_state.arama_sayaci = 0
if "captcha_dogrulandi" not in st.session_state:
    st.session_state.captcha_dogrulandi = True
if "arama_terimi" not in st.session_state:
    st.session_state.arama_terimi = ""

DOGRULAMA_ESIGI = 8  # her 8 aramada bir doğrulama sorusu çıkar

with st.form("arama_formu", clear_on_submit=False):
    girilen_terim = st.text_input(
        "🔍 Arama",
        value=st.session_state.arama_terimi,
        placeholder="Aramak istediğiniz firma / kişi / sicil no yazın... (büyük-küçük harf, boşluk önemli değil)",
        disabled=(yuklenen_dosya is None),
        label_visibility="collapsed",
    )
    ara_butonu = st.form_submit_button("Ara", disabled=(yuklenen_dosya is None))

if ara_butonu:
    st.session_state.arama_terimi = girilen_terim
    if girilen_terim:
        st.session_state.arama_sayaci += 1
        if st.session_state.arama_sayaci % DOGRULAMA_ESIGI == 0:
            st.session_state.captcha_dogrulandi = False
            # Yeni bir doğrulama sorusu üret
            st.session_state.captcha_a = random.randint(1, 20)
            st.session_state.captcha_b = random.randint(1, 20)

arama_terimi = st.session_state.arama_terimi

# ------------------------------------------------------------
# 2b) DOĞRULAMA (BASİT CAPTCHA) — belirli sayıda aramadan sonra çıkar
# ------------------------------------------------------------
if not st.session_state.captcha_dogrulandi:
    st.warning("Devam etmeden önce lütfen aşağıdaki kısa doğrulamayı tamamlayın.")
    with st.form("captcha_formu"):
        soru = f"Doğrulama: {st.session_state.captcha_a} + {st.session_state.captcha_b} = ?"
        cevap = st.number_input(soru, step=1, format="%d")
        dogrula_butonu = st.form_submit_button("Doğrula ve devam et")
    if dogrula_butonu:
        if cevap == st.session_state.captcha_a + st.session_state.captcha_b:
            st.session_state.captcha_dogrulandi = True
            st.rerun()
        else:
            st.error("Cevap yanlış, lütfen tekrar deneyin.")
    st.stop()

# ------------------------------------------------------------
# 3) DOSYA YOKSA BİLGİLENDİRME, VARSA OKU
# ------------------------------------------------------------
if yuklenen_dosya is None:
    st.info("Arama yapabilmek için önce yukarıdan bir Excel dosyası yükleyin.")
    st.stop()

try:
    df = pd.read_excel(yuklenen_dosya)
except Exception as hata:
    st.error(f"Dosya okunamadı, lütfen geçerli bir Excel dosyası yükleyin. Hata: {hata}")
    st.stop()

df = df.fillna("")


def hucreyi_metne_cevir(deger):
    """Sayıları (özellikle telefon/sicil no gibi tam sayı olması gerekenleri)
    '3244540600.0' yerine '3244540600' şeklinde, boş hücreleri de '' olarak
    düzgün metne çevirir. Bu sayede tablo hem hatasız görüntülenir hem de
    sayılar çirkin görünmez."""
    if deger == "" or pd.isna(deger):
        return ""
    if isinstance(deger, float) and deger.is_integer():
        return str(int(deger))
    return str(deger)


# Streamlit'in tabloyu ekranda gösterebilmesi için (Arrow formatı), tüm
# hücreleri metne çeviriyoruz. Aksi halde bir sütunda hem sayı hem boş
# hücre (örn. telefon numarası sütunu) karışık olduğunda uygulama çöküyor.
df = df.map(hucreyi_metne_cevir)

st.success(f"'{yuklenen_dosya.name}' yüklendi — {len(df):,} satır, {len(df.columns)} sütun bulundu.")

# ------------------------------------------------------------
# 4) ARAMA MANTIĞI (boşluk / büyük-küçük harf duyarsız)
# ------------------------------------------------------------
if arama_terimi:
    aranan = normallestir(arama_terimi)

    # Her satırın TÜM sütunlarını tek bir normalleştirilmiş metinde birleştiriyoruz,
    # sonra aranan kelime bu metnin içinde geçiyor mu diye bakıyoruz.
    satir_metinleri = df.astype(str).apply(
        lambda satir: normallestir(" ".join(satir.values)), axis=1
    )
    sonuclar = df[satir_metinleri.str.contains(re.escape(aranan), na=False)]
    baslik_metni = f"🔎 '{arama_terimi}' için {len(sonuclar):,} sonuç bulundu"
else:
    sonuclar = df
    baslik_metni = f"📋 Tüm kayıtlar ({len(sonuclar):,} satır)"

# ------------------------------------------------------------
# 5) SONUÇLAR — GENİŞ, KAYDIRMASIZ, TÜM SATIRLARIN SIĞDIĞI TABLO
# ------------------------------------------------------------
with st.expander(baslik_metni, expanded=True):
    # Tüm satırların kaydırma olmadan görünmesi için tablo yüksekliğini
    # satır sayısına göre otomatik hesaplıyoruz.
    satir_yuksekligi = 35
    tablo_yuksekligi = (len(sonuclar) + 1) * satir_yuksekligi + 3
    tablo_yuksekligi = min(tablo_yuksekligi, 2000)  # aşırı uzamasın diye üst sınır

    st.dataframe(
        sonuclar,
        use_container_width=True,
        hide_index=True,
        height=tablo_yuksekligi,
    )

    csv_veri = sonuclar.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Sonuçları CSV olarak indir",
        data=csv_veri,
        file_name="sorgu_sonuclari.csv",
        mime="text/csv",
    )

    # ----------------------------------------------------------
    # 6) DETAY GÖRÜNÜMÜ
    # ----------------------------------------------------------
    if len(sonuclar) > 0:
        st.divider()
        st.markdown("**Bir kaydın tüm ayrıntılarını görmek için seçin:**")

        onizleme_sutun_sayisi = min(3, len(sonuclar.columns))

        def satir_etiketi(satir):
            parcalar = [str(satir[sutun]) for sutun in sonuclar.columns[:onizleme_sutun_sayisi]]
            return " — ".join(p for p in parcalar if p)

        secenekler = {"— Kayıt seçin —": None}
        for orijinal_index, satir in sonuclar.iterrows():
            etiket = satir_etiketi(satir) or f"Kayıt #{orijinal_index}"
            secenekler[etiket] = orijinal_index

        secilen_etiket = st.selectbox("Kayıt", list(secenekler.keys()), label_visibility="collapsed")
        secilen_index = secenekler[secilen_etiket]

        if secilen_index is not None:
            secili_satir = sonuclar.loc[secilen_index]
            st.markdown("#### 📋 Kayıt Detayı")
            for sutun_adi in sonuclar.columns:
                deger = secili_satir[sutun_adi]
                st.markdown(f"**{sutun_adi}:** {deger if str(deger).strip() else '—'}")
