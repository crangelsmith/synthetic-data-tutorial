'''
Takes the NHS A&E data generated from generate.py and runs it through a
set of de-identification steps. It then saves this as a new dataset.
'''
import random 

import pandas as pd
import numpy as np

import filepaths


def main():
    print('running de-identification steps...')

    # "df" is the usual way people refer to a pandas DataFrame object
    nhs_ae_df = load_nhs_london_ae_data()

    print('removing NHS numbers...')
    nhs_ae_df = remove_nhs_numbers(nhs_ae_df)

    print('converting postcodes to LSOA...')
    nhs_ae_df = convert_postcodes_to_lsoa(nhs_ae_df)

    nhs_ae_df = convert_lsoa_to_imd_decile(nhs_ae_df)
    nhs_ae_df = replace_hospital_with_random_number(nhs_ae_df)
    nhs_ae_df = put_time_in_4_hour_bins(nhs_ae_df)
    nhs_ae_df = remove_non_male_or_female(nhs_ae_df)
    nhs_ae_df = add_age_brackets(nhs_ae_df)

    nhs_ae_df.to_csv(filepaths.nhs_ae_data_deidentify, index=False)

    elapsed = round(time.time() - start, 2)
    print('done in ' + str(elapsed) + ' seconds.')


def load_nhs_london_ae_data() -> pd.DataFrame:
    """ Reads the NHS A&E dataset """
    nhs_ae_df = pd.read_csv(filepaths.nhs_ae_data)
    return nhs_ae_df


def remove_nhs_numbers(nhs_ae_df: pd.DataFrame) -> pd.DataFrame:
    """Drops the NHS numbers columns from the dataset

    Keyword arguments:
    nhs_ae_df -- NHS A&E records dataframe
    """
    nhs_ae_df = nhs_ae_df.drop('NHS number', 1)
    return nhs_ae_df


def convert_postcodes_to_lsoa(nhs_ae_df: pd.DataFrame) -> pd.DataFrame:
    """Adds corresponding Lower layer super output area for each row
    depending on their postcode. Uses London postcodes dataset from
    https://www.doogal.co.uk/PostcodeDownloads.php 

    Keyword arguments:
    nhs_ae_df -- NHS A&E records dataframe
    """
    postcodes_df = pd.read_csv(filepaths.postcodes_london)
    nhs_ae_df = pd.merge(
        nhs_ae_df, 
        postcodes_df[['Postcode', 'Lower layer super output area']], 
        on='Postcode'
    )
    nhs_ae_df = nhs_ae_df.drop('Postcode', 1)
    return nhs_ae_df


def convert_lsoa_to_imd_decile(nhs_ae_df: pd.DataFrame) -> pd.DataFrame:
    """Maps each row's Lower layer super output area to which 
    Index of Multiple Deprivation decile it's in. It calculates the decile 
    rates based on the IMD's over all of London. 
    Uses "London postcodes.csv" dataset from
    https://www.doogal.co.uk/PostcodeDownloads.php 

    Keyword arguments:
    nhs_ae_df -- NHS A&E records dataframe
    """

    postcodes_df = pd.read_csv(filepaths.postcodes_london)

    nhs_ae_df = pd.merge(
        nhs_ae_df, 
        postcodes_df[
            ['Lower layer super output area', 
             'Index of Multiple Deprivation']
        ].drop_duplicates(), 
        on='Lower layer super output area'
    )
    _, bins = pd.qcut(
        postcodes_df['Index of Multiple Deprivation'], 10, 
        retbins=True, labels=False
    )
    nhs_ae_df['Index of Multiple Deprivation Decile'] = pd.cut(
        nhs_ae_df['Index of Multiple Deprivation'], bins=bins, 
        labels=False, include_lowest=True) + 1

    nhs_ae_df = nhs_ae_df.drop('Index of Multiple Deprivation', 1)
    nhs_ae_df = nhs_ae_df.drop('Lower layer super output area', 1)

    return nhs_ae_df


def replace_hospital_with_random_number(
        nhs_ae_df: pd.DataFrame) -> pd.DataFrame:
    """ 
    Gives each hospital a random integer number and adds a new column
    with these numbers. Drops the hospital name column. 

    Keyword arguments:
    nhs_ae_df -- NHS A&E records dataframe
    """

    hospitals = list(set(nhs_ae_df['Hospital'].tolist()))
    random.shuffle(hospitals)
    hospital_ids = range(1, len(hospitals)+1)
    hospitals_map = {
        hospital : hospital_id
        for hospital, hospital_id in zip(hospitals, hospital_ids)
    }
    nhs_ae_df['Hospital ID'] = nhs_ae_df['Hospital'].map(hospitals_map)
    nhs_ae_df = nhs_ae_df.drop('Hospital', 1)

    return nhs_ae_df


def put_time_in_4_hour_bins(nhs_ae_df):
    arrival_times = pd.to_datetime(nhs_ae_df['Arrival Time'])
    nhs_ae_df['Arrival Date'] = arrival_times.dt.strftime('%Y-%m-%d')
    nhs_ae_df['Arrival Hour'] = arrival_times.dt.hour

    nhs_ae_df['Arrival hour range'] = pd.cut(
        nhs_ae_df['Arrival Hour'], 
        bins=[0, 4, 8, 12, 16, 20, 24], 
        labels=['00-03', '04-07', '08-11', '12-15', '16-19', '20-23'], 
        include_lowest=True
    )
    nhs_ae_df = nhs_ae_df.drop('Arrival Time', 1)
    nhs_ae_df = nhs_ae_df.drop('Arrival Hour', 1)
    return nhs_df


def remove_non_male_or_female(nhs_df):
    nhs_df = nhs_df[nhs_df['Gender'].isin(['Male', 'Female'])]
    return nhs_df


def add_age_brackets(nhs_df):
    nhs_df['Age bracket'] = pd.cut(
        nhs_df['Age'], 
        bins=[0, 18, 25, 45, 65, 85, 150], 
        labels=['0-17', '18-24', '25-44', '45-64', '65-84', '85-'], 
        include_lowest=True
    )
    nhs_df = nhs_df.drop('Age', 1)
    return nhs_df


if __name__ == "__main__":
    main()