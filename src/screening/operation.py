import pandas as pd


def add_lists(input_df1, input_df2):
    """Merges two stock lists into one

    Input lists are DataFrames must contain columns ['code', 'name', 'score']

    Merges by 'code'. Retains one 'name' (from the first occurrence)
    and sums the 'score'.

    Args:
        input_df1 (pd.DataFrame): First list of stocks
        input_df2 (pd.DataFrame): Second list of stocks

    Returns:
        pd.DataFrame: Result containing merged list

    Raises:
        ValueError: If either input DataFrame does not contain required columns
    """
    required_columns = {'code', 'name', 'score'}

    if not required_columns.issubset(input_df1.columns):
        raise ValueError(
            f'Error: Input1 is missing required columns: {required_columns - set(input_df1.columns)}'
        )
    if not required_columns.issubset(input_df2.columns):
        raise ValueError(
            f'Error: Input2 is missing required columns: {required_columns - set(input_df2.columns)}'
        )

    # concatenate the two DataFrames
    combined = pd.concat([input_df1, input_df2], ignore_index=True)

    # group by 'code', take the first 'name', and sum the 'score'
    result = combined.groupby('code', as_index=False).agg(
        {'name': 'first', 'score': 'sum'}
    )

    # ensure the column order matches the requirement
    return result[['code', 'name', 'score']]


def minus_lists(source_df, exclude_df):
    """Subtracts the second list of stocks from the first based on 'code'

    Input lists are DataFrames must contain columns ['code', 'name', 'score']

    Removes rows from the source where the 'code' exists in the exclude.

    Args:
        source_df (pd.DataFrame): Source list of stocks
        exclude_df (pd.DataFrame): List of stocks to exclude

    Returns:
        pd.DataFrame: Result containing stocks from source that are not in exclude

    Raises:
        ValueError: If either input DataFrame does not contain required columns.
    """
    required_columns = {'code', 'name', 'score'}

    if not required_columns.issubset(source_df.columns):
        raise ValueError(
            f'Error: Source is missing required columns: {required_columns - set(source_df.columns)}'
        )
    if not required_columns.issubset(exclude_df.columns):
        raise ValueError(
            f'Error: Exclude is missing required columns: {required_columns - set(exclude_df.columns)}'
        )

    # identify codes to exclude
    exclude_codes = set(exclude_df['code'])

    # filter the source DataFrame
    result = source_df[~source_df['code'].isin(exclude_codes)].copy()

    # ensure the column order matches the requirement
    return result[['code', 'name', 'score']]
