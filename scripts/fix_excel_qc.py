from pathlib import Path
import pandas as pd 
considered_columns = ['hakai_id','comments']
import click
import shutil
from loguru import logger

def fix_excel_qc(path, output):
    # Make a copy of the original file
    logger.info(f'Copy {path} to otput {output}')
    shutil.copy(path,output)

    # Read in the copy
    df = pd.read_excel(output, sheet_name='Hakai Data')
    df = df[[col for col in df.columns if (col in considered_columns or col.endswith('_flag'))]]

    # Write out the copy
    with pd.ExcelWriter(output, mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name="Hakai Data", index=False)

@click.command()
@click.argument('path', type=click.Path(exists=True))
def fix_excel_files(path):
    path = Path(path)

    for file in Path(path).glob('*.xlsx'):
        output = file.parent/ 'fixed' / (file.stem + '.xlsx')
        fix_excel_qc(file, output)

if __name__ == '__main__':
    fix_excel_files()