-- Migration: Add kategori to notifikasi table

-- CATATAN: schema.sql terbaru sudah memuat kolom kategori. Jalankan migrasi ini HANYA untuk database lama
-- yang dibuat sebelum kolom tersebut ada (ALTER akan gagal jika kolom sudah ada).
ALTER TABLE notifikasi ADD COLUMN kategori VARCHAR(50) DEFAULT 'sistem' AFTER link;

-- Update kategori data yang sudah ada
UPDATE notifikasi SET kategori = 'verifikasi' WHERE judul LIKE '%Verifikasi%' OR judul LIKE '%Mendaftar%';
UPDATE notifikasi SET kategori = 'lamaran' WHERE judul LIKE '%Lamaran%' OR judul LIKE '%Pelamar%';
UPDATE notifikasi SET kategori = 'lowongan' WHERE judul LIKE '%Lowongan%';
