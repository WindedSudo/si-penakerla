# Panduan Fitur Tambahan SI-PENAKERLA

## Fitur yang ditambahkan

1. **Keahlian pekerja** — pencari kerja dapat menyimpan nama skill, kategori, tingkat penguasaan, dan lama pengalaman.
2. **Portofolio pekerja** — pencari kerja dapat menyimpan judul proyek/karya, deskripsi, tahun, dan tautan eksternal. Data tampil pada CV dan dapat dilihat perusahaan yang berhak membuka CV pelamar.
3. **Pencocokan lowongan** — skor sekarang mempertimbangkan pendidikan (30%), skill (45%), lokasi (15%), serta pengalaman relevan (10%). Skor adalah heuristik berbasis aturan, bukan model AI dan bukan jaminan diterima.
4. **Asisten Karier** — tersedia FAQ lokal tanpa API key. Integrasi AI dapat diaktifkan melalui endpoint yang kompatibel dengan OpenAI Chat Completions.
5. **Lowongan eksternal** — admin dapat mengimpor lowongan dari RSS/Atom publik. Lowongan eksternal ditampilkan di menu terpisah dan proses lamaran tetap dilakukan di situs sumber.

## Cara memasang pada database yang sudah ada

1. Buat backup database dan folder proyek terlebih dahulu.
2. Salin berkas proyek yang diperbarui ke folder aplikasi. Simpan file `.env` milik sendiri; file tersebut sengaja tidak disertakan pada paket.
3. Jalankan `database/migration_fitur_lanjutan.sql` satu kali pada database SI-PENAKERLA yang sedang digunakan melalui MySQL Workbench, phpMyAdmin, atau MySQL CLI.
4. Jangan menjalankan `database/schema.sql` pada database yang sudah berisi data, karena file tersebut melakukan `DROP TABLE` untuk proses instalasi database baru.
5. Install dependensi sesuai `requirements.txt`, kemudian jalankan aplikasi seperti biasa dengan `python run.py`.

Untuk instalasi database baru, tabel fitur tambahan sudah tercantum pada `database/schema.sql`.

## Mengaktifkan AI pada Asisten Karier (opsional)

Tambahkan konfigurasi berikut ke file `.env` yang sudah ada. Gunakan API key dari penyedia yang memang mendukung format OpenAI Chat Completions.

```env
AI_API_URL=https://api.openai.com/v1/chat/completions
AI_API_KEY=isi_api_key_milik_sendiri
AI_MODEL=gpt-4o-mini
```

Tanpa `AI_API_KEY`, asisten tetap berjalan menggunakan FAQ lokal. Konteks yang dikirim ke penyedia AI dibatasi pada pendidikan, kecamatan, keahlian, dan ringkasan posisi/tahun pengalaman. NIK, tanggal lahir, alamat lengkap, email, dan file CV tidak diambil dari profil. Namun, pesan yang diketik akan diteruskan ke penyedia AI saat integrasi aktif, jadi jangan masukkan data pribadi/sensitif ke dalam chat.

## Mengaktifkan impor lowongan eksternal (opsional)

Tambahkan URL feed RSS/Atom publik yang boleh digunakan menurut ketentuan situs sumber ke `.env`. Pisahkan beberapa feed dengan tanda titik koma.

```env
JOB_FEED_URLS=https://feed-pertama.example/jobs.xml;https://feed-kedua.example/atom.xml
```

Contoh URL di atas hanya menunjukkan format, bukan sumber feed yang sudah diverifikasi. Setelah konfigurasi disimpan, login sebagai admin lalu buka **Impor Lowongan** dan tekan **Sinkronisasi Feed**.

Pembaca feed membatasi ukuran respons, menolak DTD/entity XML, dan membatasi feed ke HTTP/HTTPS dengan host publik. Redirect lintas host ditolak. Implementasi ini membaca RSS/Atom; belum melakukan crawling HTML bebas. Bila portal tujuan tidak menyediakan feed atau API publik, perlu dibuat adapter khusus berdasarkan ketentuan akses dan struktur situs tersebut.

## Lokasi menu

- Pencari kerja: **Keahlian & Portofolio**, **Asisten Karier**, **Lowongan Eksternal**.
- Admin: **Impor Lowongan**.
- Perusahaan: portofolio dan skill terstruktur muncul di CV pelamar yang dapat diakses perusahaan.
