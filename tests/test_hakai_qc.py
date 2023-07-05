from hakai_qc.ctd import generate_qc_flags
from hakai_api import Client
import pandas as pd
from pathlib import Path


def get_ctd_test_file():
    test_ctd_file = Path(__file__).parent / "test_ctd_qu39_Jan2022.parquet"
    return pd.read_parquet(test_ctd_file)


def test_get_ctd_test_file():
    df = get_ctd_test_file()
    assert not df.empty


class TestSugestedFlagCTD:
    def test_default_hakai_ctd_automated_qc(self):
        df = get_ctd_test_file()
        df_qced = generate_qc_flags(df, "temperature")

        assert not df_qced.empty
        assert "temperature_flag" in df_qced
        assert "comments" in df_qced

    def test_all_svc_hakai_ctd_automated_qc(self):
        df = get_ctd_test_file()
        df["temperature_flag_level_1"] = 3
        df_qced = generate_qc_flags(df, "temperature")

        assert not df_qced.empty
        assert (df_qced["temperature_flag"] == "SVC").all()
