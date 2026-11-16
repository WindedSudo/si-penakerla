"""Satu sumber waktu untuk seluruh aplikasi.

Tenggat lowongan bertipe DATE dan berlaku sampai AKHIR hari tersebut menurut WIB
(Asia/Jakarta). Semua perbandingan tenggat memakai today_wib(), bukan date.today()
atau CURDATE(), supaya hasil tidak bergantung pada zona waktu server aplikasi/MySQL.
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo

ZONA_APLIKASI = ZoneInfo('Asia/Jakarta')
OFFSET_MYSQL = '+07:00'


def now_wib():
    """Waktu sekarang di WIB, tanpa tzinfo (cocok untuk kolom DATETIME)."""
    return datetime.now(ZONA_APLIKASI).replace(tzinfo=None, microsecond=0)


def today_wib() -> date:
    return datetime.now(ZONA_APLIKASI).date()


def tenggat_terlewati(deadline, hari_ini=None) -> bool:
    """True jika tenggat sudah lewat. Tenggat = hari H berarti MASIH terbuka sepanjang hari H."""
    if not deadline:
        return False
    return deadline < (hari_ini or today_wib())
