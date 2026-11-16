-- Migration: Add pengalaman_kerja table

CREATE TABLE IF NOT EXISTS pengalaman_kerja (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pencari_kerja_id INT NOT NULL,
    nama_perusahaan VARCHAR(200) NOT NULL,
    posisi VARCHAR(100) NOT NULL,
    tahun_mulai INT NOT NULL,
    tahun_selesai INT,
    deskripsi TEXT,
    FOREIGN KEY (pencari_kerja_id) REFERENCES pencari_kerja(id) ON DELETE CASCADE
);

-- Seed pengalaman kerja untuk demo
INSERT IGNORE INTO pengalaman_kerja (pencari_kerja_id, nama_perusahaan, posisi, tahun_mulai, tahun_selesai, deskripsi) VALUES
(1, 'PT Teknologi Nusantara', 'Junior Web Developer', 2020, 2022, 'Mengembangkan aplikasi web menggunakan PHP dan MySQL. Maintenance sistem internal.'),
(1, 'CV Digital Kreasi', 'Freelance Programmer', 2022, NULL, 'Membuat website company profile dan sistem informasi untuk UMKM.'),
(2, 'Toko Serba Ada', 'Staff Administrasi', 2021, 2023, 'Menangani pembukuan, surat-menyurat, dan pengelolaan data karyawan.');
