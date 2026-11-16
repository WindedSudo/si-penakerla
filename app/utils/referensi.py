"""Kamus atribut lowongan: nilai referensi yang dipakai bersama oleh form, filter, dan pencocokan."""

# Jenjang pendidikan kanonik. 'SMA/SMK' dan 'D4/S1' adalah SATU token (garis miring bagian dari nama).
PENDIDIKAN_VALID = ["SD", "SMP", "SMA/SMK", "D1", "D2", "D3", "D4/S1", "S2", "S3"]

PENDIDIKAN_LEVEL = {"SD": 1, "SMP": 2, "SMA/SMK": 3, "D1": 4, "D2": 5, "D3": 6, "D4/S1": 7, "S2": 8, "S3": 9}

# Bentuk lama yang mungkin masih tersimpan di data lama.
_ALIAS_PENDIDIKAN = {"SMA": "SMA/SMK", "SMK": "SMA/SMK", "D4": "D4/S1", "S1": "D4/S1"}

KECAMATAN_LAMONGAN = [
    "Babat", "Bluluk", "Brondong", "Deket", "Glagah", "Kalitengah", "Karanggeneng",
    "Karangbinangun", "Kedungpring", "Kembangbahu", "Lamongan", "Laren", "Maduran",
    "Mantup", "Modo", "Ngimbang", "Paciran", "Pucuk", "Sambeng", "Sarirejo", "Sekaran",
    "Solokuro", "Sugio", "Sukodadi", "Sukorame", "Tikung", "Turi",
]


def simpan_pendidikan(daftar):
    """Daftar jenjang -> string CSV kanonik tanpa spasi, urut naik. Nilai tidak dikenal dibuang."""
    dipilih = {p for p in (daftar or []) if p in PENDIDIKAN_LEVEL}
    return ",".join(sorted(dipilih, key=PENDIDIKAN_LEVEL.get))


def baca_pendidikan(teks):
    """String CSV (atau bentuk lama) -> daftar token kanonik. Contoh 'SMA/SMK,D3' -> ['SMA/SMK', 'D3']."""
    hasil = []
    for bagian in (teks or "").split(","):
        token = bagian.strip()
        token = _ALIAS_PENDIDIKAN.get(token, token)
        if token in PENDIDIKAN_LEVEL and token not in hasil:
            hasil.append(token)
    return hasil
