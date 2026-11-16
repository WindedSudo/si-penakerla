# SI-PENAKERLA

## Deskripsi
Sistem Informasi Pendataan dan Penempatan Tenaga Kerja Kabupaten Lamongan

## Fitur
- Registrasi dan login multi-role (Admin, Pencari Kerja, Perusahaan)
- Dashboard pencari kerja, perusahaan, admin
- Manajemen profil pencari kerja dan perusahaan
- CRUD lowongan pekerjaan (Buat, Baca, Ubah, Hapus)
- Sistem lamaran dan pencarian lowongan
- Verifikasi perusahaan oleh admin
- Penempatan tenaga kerja secara otomatis ketika lamaran diterima
- Laporan dan export data dalam format CSV
- Antarmuka responsif menggunakan Bootstrap 5
- Skill pekerja terstruktur (kategori, tingkat penguasaan, lama pengalaman)
- Portofolio proyek/karya pekerja yang ikut ditampilkan pada CV
- Pencocokan lowongan berbasis aturan dengan bobot pendidikan, skill, lokasi, dan pengalaman
- Asisten Karier (FAQ lokal; integrasi AI OpenAI-compatible opsional)
- Impor lowongan eksternal dari RSS/Atom publik yang dikonfigurasi admin

## Tech Stack
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript, Jinja2, Bootstrap 5
- **Database:** MySQL
- **Auth:** Flask-Login, bcrypt untuk hashing password

## Struktur Folder
```
si-penakerla/
├── app/
│   ├── __init__.py
│   ├── db.py
│   ├── decorators.py
│   ├── models/
│   ├── routes/
│   ├── static/
│   └── templates/
├── database/
│   ├── schema.sql                 # DDL saja
│   ├── seed.sql                   # akun demo + data dasar
│   ├── seed_dummy.sql             # data sintetis banyak (dibangkitkan generate_seed_dummy.py)
│   ├── generate_seed_dummy.py
│   ├── setup_db.py                # buat DB + muat skema/seed
│   ├── migration_pendidikan_csv.sql
│   └── migration_fitur_lanjutan.sql
├── tests/
│   ├── conftest.py                # memakai database si_penakerla_test
│   ├── eval/                      # data acuan + runner Uji 1 (paper)
│   ├── test_uji1_ketepatan_pencarian.py
│   ├── test_uji3_konsistensi_lamaran.py
│   └── test_*.py
├── .env.example
├── README.md
├── PANDUAN_FITUR_TAMBAHAN.md
├── requirements.txt
└── run.py
```

## Instalasi

### 1. Clone Repository
```bash
git clone <url-repository>
cd si-penakerla
```

### 2. Buat Virtual Environment
```bash
python -m venv venv
```

### 3. Aktivasi Virtual Environment
Windows:
```bash
venv\Scripts\activate
```
Linux/Mac:
```bash
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Konfigurasi Environment
```bash
copy .env.example .env
```
Edit file `.env` sesuai dengan konfigurasi database Anda.

### 6. Buat Database MySQL
```bash
python database/setup_db.py --dummy
```
Perintah ini membuat database (nama dari `DB_NAME`), memuat skema, data dasar, dan data dummy sintetis
(30 perusahaan, 140 pencari kerja, 260 lowongan, ~500 lamaran). Tanpa `--dummy` hanya data dasar yang dimuat.
Skema memakai `DROP TABLE`, jadi seluruh data pada database tujuan dihapus. Untuk database lama, jalankan migrasi yang diperlukan satu kali:
- `database/migration_pendidikan_csv.sql` bila database berasal dari skema pendidikan lama.
- `database/migration_fitur_lanjutan.sql` untuk menambah tabel skill, portofolio, dan lowongan eksternal.

Jangan menjalankan `schema.sql` pada database yang berisi data penting karena file tersebut melakukan DROP TABLE.

### 7. Jalankan Aplikasi
```bash
python run.py
```
Akses aplikasi melalui browser: http://localhost:5000

### 8. Jalankan Testing
Pengujian memakai database terpisah `si_penakerla_test` (dibuat ulang otomatis; bisa diganti lewat `TEST_DB_NAME`,
nama harus berakhiran `_test`).
```bash
python -m pytest tests/ -v                 # seluruh tes
python -m tests.eval.run_uji1              # Uji 1 saja (database si_penakerla_eval)
```
Log hasil ditulis ke folder `hasil_uji/` (`uji1_per_query.csv`, `uji1_ringkasan.txt`, `uji3_log.csv`).

## Aturan Pencarian dan Lamaran (acuan pengujian)
- Filter pencarian digabung dengan **AND**; filter kosong diabaikan.
- Hanya lowongan `aktif` dengan `deadline >=` hari ini (WIB, Asia/Jakarta) yang tampil. Tenggat = hari H berarti masih terbuka sampai akhir hari H.
- `posisi` dan `lokasi`: mengandung teks, tanpa beda huruf besar/kecil; `%` dan `_` dicocokkan secara harfiah.
- `pendidikan`: jenjang yang dipilih harus ada di daftar jenjang yang diterima lowongan (kolom berisi CSV, contoh `SMA/SMK,D3,D4/S1`).
- Skor kecocokan di `app/utils/matching.py` adalah heuristik berbasis aturan (bukan AI/ML): pendidikan 30%, skill 45%, lokasi 15%, pengalaman 10%.
- Asisten Karier memakai FAQ lokal secara default. Untuk AI sungguhan, isi `AI_API_URL`, `AI_API_KEY`, dan `AI_MODEL` pada `.env` dengan layanan yang kompatibel dengan OpenAI Chat Completions. Data identitas yang tersimpan pada profil (NIK, tanggal lahir, alamat lengkap, email, dan file CV) tidak diambil sebagai konteks API. Pesan yang diketik pengguna akan diteruskan ke penyedia AI ketika integrasi aktif, jadi jangan menuliskan data pribadi/sensitif di chat.
- Impor lowongan eksternal hanya membaca RSS/Atom publik yang URL-nya dimasukkan admin server ke `JOB_FEED_URLS` (pisahkan dengan titik koma). Admin kemudian menjalankan sinkronisasi lewat menu **Impor Lowongan**. Pastikan feed memang boleh digunakan dan sesuai ketentuan situs sumber. Aplikasi tidak meng-crawl halaman web sembarang.
- Lowongan eksternal ditampilkan terpisah dari lowongan resmi SI-PENAKERLA; pelamar diarahkan ke situs sumber dan tidak membuat data lamaran internal.
- Lamaran: satu pencari hanya bisa melamar satu kali per lowongan (UNIQUE KEY), dan pengecekan status/tenggat dilakukan atomik saat menyimpan.

## Akun Development

Berikut adalah akun yang dapat digunakan untuk pengembangan dan testing (setelah database di-seed):

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@penakerla.local | admin123 |
| Pencari Kerja | budi@example.com | password123 |
| Pencari Kerja | siti@example.com | password123 |
| Pencari Kerja | ahmad@example.com | password123 |
| Perusahaan | hr@lamongan-jaya.com | password123 |
| Perusahaan | hr@majubersama.com | password123 |

## Endpoint

### Auth
- `GET, POST /login`
- `GET, POST /register`
- `GET /logout`
- `GET /notifikasi`, `GET /notifikasi/baca/<id>`, `POST /notifikasi/baca-semua`
- `GET /api/notifikasi/status`

### Admin (`/admin`)
- `GET /admin/dashboard`
- `GET /admin/users`, `POST /admin/users/delete/<id>`
- `GET /admin/verifikasi`, `POST /admin/verifikasi/<id>/<terverifikasi|ditolak>`
- `GET /admin/lowongan`, `GET /admin/lamaran`, `GET /admin/penempatan`
- `GET /admin/laporan`, `GET /admin/laporan/export?type=<pengguna|pencari|perusahaan|lowongan|lamaran|penempatan>`
- `GET /admin/lowongan-eksternal`, `POST /admin/lowongan-eksternal/sinkronisasi`
- `GET /admin/cv/<pencari_id>`

### Pencari Kerja (`/pencari`)
- `GET /pencari/dashboard`
- `GET, POST /pencari/profile`
- `GET /pencari/lowongan`, `GET /pencari/lowongan/<id>`
- `POST /pencari/lamar/<lowongan_id>`
- `GET /pencari/lamaran`
- `GET /pencari/cv-builder`, `GET /pencari/cv-preview`
- `GET /pencari/pengembangan` (keahlian dan portofolio)
- `POST /pencari/skill/tambah`, `POST /pencari/skill/hapus/<id>`
- `POST /pencari/portofolio/tambah`, `POST /pencari/portofolio/hapus/<id>`
- `GET /pencari/asisten-karier`, `POST /pencari/api/asisten-karier`
- `GET /pencari/lowongan-eksternal`
- `POST /pencari/pengalaman/tambah`, `POST /pencari/pengalaman/hapus/<id>`

### Perusahaan (`/perusahaan`)
- `GET /perusahaan/dashboard`
- `GET, POST /perusahaan/profil`
- `GET /perusahaan/lowongan`, `GET, POST /perusahaan/lowongan/tambah`, `GET, POST /perusahaan/lowongan/edit/<id>`, `POST /perusahaan/lowongan/hapus/<id>`
- `GET /perusahaan/pelamar/<lowongan_id>`, `GET /perusahaan/pelamar/detail/<lamaran_id>`, `POST /perusahaan/pelamar/status/<lamaran_id>`
- `GET /perusahaan/cv/<pencari_id>` (hanya untuk pelamar ke perusahaan tersebut)

## Catatan Keamanan
- File CV yang diunggah disimpan di folder `uploads/` (di luar `static/`), sehingga tidak bisa diakses langsung lewat URL.
- Mode debug hanya aktif jika `APP_ENV=development`. Untuk produksi set `APP_ENV=production` dan `SECRET_KEY` yang kuat.
- Aplikasi berjalan di `127.0.0.1` secara default; set `APP_HOST=0.0.0.0` bila memang perlu diakses dari jaringan.

## Lisensi
Hak Cipta © 2026 - Dinas Tenaga Kerja Kabupaten Lamongan
