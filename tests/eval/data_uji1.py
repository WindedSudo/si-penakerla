"""Uji 1 - data acuan: 50 lowongan sintetis + 20 kombinasi pencarian.

Hasil acuan DIHITUNG TERPISAH dengan aturan di bawah (himpunan Python biasa), tidak memakai SQL aplikasi.
HARI_UJI dikunci agar hasil acuan deterministik (deadline relatif terhadap tanggal ini).

Aturan (sama dengan docstring Lowongan.search):
  AND antar-filter | status aktif & deadline >= HARI_UJI | posisi/lokasi: mengandung teks, abaikan huruf besar/kecil
  | pendidikan: jenjang ada di daftar jenjang yang diterima lowongan.
"""
from datetime import date, timedelta

HARI_UJI = date(2026, 10, 28)

# (posisi, lokasi, pendidikan CSV, status, offset deadline dari HARI_UJI)
_L = [
    ("Operator Produksi", "Lamongan", "SMA/SMK", "aktif", 30),
    ("Operator Produksi", "Babat", "SMA/SMK", "aktif", 14),
    ("Operator Produksi Shift Malam", "Babat", "SMA/SMK", "aktif", 0),
    ("Helper Produksi", "Deket", "SD,SMP,SMA/SMK", "aktif", 20),
    ("Quality Control", "Lamongan", "SMA/SMK,D3,D4/S1", "aktif", 45),
    ("Quality Control Seafood", "Brondong", "D3,D4/S1", "aktif", 25),
    ("Staff Administrasi", "Lamongan", "SMA/SMK,D3,D4/S1", "aktif", 60),
    ("Staff Administrasi", "Paciran", "D3", "aktif", 10),
    ("Staff Administrasi", "Babat", "D4/S1", "ditutup", 40),
    ("Admin Gudang", "Sukodadi", "SMA/SMK,D3", "aktif", 33),
    ("Admin Gudang", "Lamongan", "SMA/SMK", "draft", 33),
    ("Staff Akuntansi", "Lamongan", "D3,D4/S1", "aktif", 18),
    ("Staff Akuntansi", "Lamongan, Kab. Lamongan", "D3,D4/S1", "aktif", 22),
    ("Teller", "Lamongan", "D3,D4/S1", "aktif", 5),
    ("Account Officer", "Lamongan", "D4/S1", "aktif", 50),
    ("Analis Kredit", "Lamongan", "D4/S1,S2", "aktif", 35),
    ("Guru Matematika", "Sukodadi", "D4/S1,S2", "aktif", 28),
    ("Guru Bahasa Inggris", "Babat", "D4/S1", "aktif", 28),
    ("Instruktur Ahli", "Lamongan", "S2,S3", "aktif", 90),
    ("Tutor Bimbingan Belajar", "Babat", "D3,D4/S1", "aktif", 12),
    ("Perawat", "Lamongan", "D3,D4/S1", "aktif", 16),
    ("Bidan", "Karanggeneng", "D3", "aktif", 16),
    ("Admin Klinik", "Lamongan", "SMA/SMK,D3", "aktif", 9),
    ("Web Developer", "Lamongan", "D3,D4/S1", "aktif", 70),
    ("IT Support", "Lamongan", "SMA/SMK,D3,D4/S1", "aktif", 1),
    ("Desainer Grafis", "Lamongan", "SMA/SMK,D3,D4/S1", "aktif", 44),
    ("Teknisi Jaringan", "Babat", "SMA/SMK,D3", "aktif", 8),
    ("Teknisi Maintenance", "Deket", "SMA/SMK,D3", "aktif", 27),
    ("Mekanik Otomotif", "Babat", "SMA/SMK,D3", "aktif", 31),
    ("Juru Las", "Kedungpring", "SMP,SMA/SMK", "aktif", 19),
    ("Drafter AutoCAD", "Lamongan", "D3,D4/S1", "aktif", 55),
    ("Driver Truk", "Babat", "SMA/SMK", "aktif", 21),
    ("Kurir", "Lamongan", "SMP,SMA/SMK", "aktif", 13),
    ("Kurir", "Paciran", "SMP", "aktif", 13),
    ("Helper Gudang", "Babat", "SD,SMP,SMA/SMK", "aktif", 6),
    ("Operator Forklift", "Babat", "SMA/SMK", "ditutup", 3),
    ("Sales Executive", "Lamongan", "SMA/SMK,D3,D4/S1", "aktif", 38),
    ("Marketing Executive", "Lamongan", "SMA/SMK,D3,D4/S1", "aktif", 38),
    ("Customer Service", "Lamongan", "SMA/SMK,D3,D4/S1", "aktif", 26),
    ("Kasir", "Lamongan", "SMA/SMK,D1", "aktif", 15),
    ("Staff Front Office", "Paciran", "SMA/SMK,D1,D3", "aktif", 17),
    ("Housekeeping", "Paciran", "SMP,SMA/SMK", "aktif", 17),
    ("Pemandu Wisata", "Paciran", "SMA/SMK,D3", "aktif", 29),
    ("Operator Komputer", "Lamongan", "D1,D2,SMA/SMK", "aktif", 11),
    ("Operator Mesin 100% Shift Malam", "Deket", "SMA/SMK", "aktif", 24),
    ("Operator Cold Storage", "Brondong", "SMA/SMK", "aktif", -1),
    ("Staff Pengolahan Ikan", "Brondong", "SMP,SMA/SMK", "aktif", -10),
    ("Staff Sortir Ikan", "Brondong", "SD,SMP,SMA/SMK", "aktif", 4),
    ("Surveyor", "Lamongan", "SMA/SMK,D3", "aktif", 36),
    ("Estimator RAB", "Lamongan", "D3,D4/S1", "draft", 36),
]
assert len(_L) == 50

LOWONGAN = [dict(id=i + 1, posisi=p, lokasi=lok, pendidikan=pend, status=st, deadline=HARI_UJI + timedelta(days=off))
            for i, (p, lok, pend, st, off) in enumerate(_L)]

# (kode, kategori, filter) - 20 kombinasi: nol hasil, satu hasil, banyak hasil; variasi lokasi, pendidikan, jenis pekerjaan
QUERY = [
    ("Q01", "banyak", dict(posisi="operator")),
    ("Q02", "banyak", dict(lokasi="Babat")),
    ("Q03", "banyak", dict(pendidikan="D3")),
    ("Q04", "banyak", dict(pendidikan="SMA/SMK")),
    ("Q05", "banyak", dict(posisi="staff", lokasi="Lamongan")),
    ("Q06", "banyak", dict(lokasi="Lamongan", pendidikan="D4/S1")),
    ("Q07", "banyak", dict(posisi="kurir", pendidikan="SMP")),
    ("Q08", "banyak", dict()),                                       # tanpa filter
    ("Q09", "satu", dict(posisi="Teller")),
    ("Q10", "satu", dict(posisi="Instruktur", pendidikan="S3")),
    ("Q11", "satu", dict(lokasi="Karanggeneng")),
    ("Q12", "satu", dict(posisi="100%")),                             # wildcard LIKE harus harfiah
    ("Q13", "satu", dict(posisi="Account", lokasi="lamongan", pendidikan="D4/S1")),  # huruf kecil
    ("Q14", "nol", dict(posisi="Dokter")),
    ("Q15", "nol", dict(posisi="Operator", pendidikan="S2")),
    ("Q16", "nol", dict(lokasi="Brondong", pendidikan="D1")),
    ("Q17", "nol", dict(posisi="Cold Storage")),                      # deadline kemarin -> tidak tampil
    ("Q18", "nol", dict(posisi="Operator Forklift")),                 # ditutup
    ("Q19", "nol", dict(posisi="Estimator")),                         # draft
    ("Q20", "nol", dict(posisi="_")),                                 # '_' bukan wildcard: tidak ada posisi yang memuat garis bawah
]


def acuan(filter_, hari_ini=HARI_UJI, data=LOWONGAN):
    """Himpunan ID yang SEHARUSNYA muncul, dihitung langsung dari definisi aturan."""
    hasil = set()
    for l in data:
        if l["status"] != "aktif" or l["deadline"] < hari_ini:
            continue
        if filter_.get("posisi") and filter_["posisi"].strip().lower() not in l["posisi"].lower():
            continue
        if filter_.get("lokasi") and filter_["lokasi"].strip().lower() not in l["lokasi"].lower():
            continue
        if filter_.get("pendidikan") and filter_["pendidikan"] not in l["pendidikan"].split(","):
            continue
        hasil.add(l["id"])
    return hasil


def _validasi():
    for kode, kategori, f in QUERY:
        n = len(acuan(f))
        ok = {"nol": n == 0, "satu": n == 1, "banyak": n >= 2}[kategori]
        assert ok, f"{kode} kategori {kategori} tetapi acuan memuat {n} lowongan"
    assert len(QUERY) == 20


_validasi()
