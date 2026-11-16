"""Uji 1 sebagai pytest: tiap kombinasi pencarian harus identik dengan hasil acuan (database eval terpisah)."""
import pytest

from tests.eval import run_uji1


@pytest.fixture(scope='module')
def hasil_uji1():
    return {b['kode']: b for b in run_uji1.jalankan()}


@pytest.mark.parametrize('kode', [f'Q{i:02d}' for i in range(1, 21)])
def test_query_tepat(hasil_uji1, kode):
    b = hasil_uji1[kode]
    assert b['id_hilang'] == '' and b['id_salah_masuk'] == '', \
        f"{kode} {b['filter']}: hilang [{b['id_hilang']}] salah masuk [{b['id_salah_masuk']}]"
