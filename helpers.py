import pandas as pd

def parse_excel(file):
    df = pd.read_excel(file)  # Assuming pandas is installed
    members = df.to_dict('records')
    return members
