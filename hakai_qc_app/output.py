
from pathlib import Path
from loguru import logger
from datetime import datetime
import shutil
import pandas as pd


from hakai_qc_app.variables import pages

MODULE_PATH = Path(__file__).parent

def generate_excel_output(df:pd.DataFrame, data_type:str, temp_dir:str="temp", file_name:str=None):


    logger.info("Retrieve excel file template for {}", data_type)
    excel_template = MODULE_PATH / f"assets/hakai-template-{data_type}-samples.xlsx"

    variable_output = pages.get(data_type)[0].get("upload_fields")
    logger.debug("Save excel file type:{}", data_type)
    if variable_output:
        logger.debug("Upload only subset-variables={}", variable_output)
        df = df[variable_output]

    temp_dir = Path(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file = (
        temp_dir
        / (file_name or f"hakai-qc-{data_type}-{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}.xlsx")
    )

    logger.info("Copy {} template/update excel file to: {}", data_type, temp_file)
    shutil.copy(
        excel_template,
        temp_file,
    )
    logger.debug("Add data to qc excel file")
    with pd.ExcelWriter(
        temp_file, engine="openpyxl", mode="a", if_sheet_exists="replace"
    ) as writer:
        df.to_excel(writer, sheet_name="Hakai Data", index=False)
    return temp_file