"""Functions for preprocessing data and performing AutoML.
"""

import pandas as pd
import streamlit as st

from typing import List
from typing import Union
from typing import Mapping
from tpot import TPOTClassifier
from tpot import TPOTRegressor

from sklearn.model_selection import train_test_split

from pandas.api.types import is_categorical_dtype


def _obj_wrangler(data: pd.DataFrame) -> pd.DataFrame:
    """Converts columns with `object` dtype to `StringDtype`.
    """
    obj_cols = (data.select_dtypes(include=['object'])
                    .columns)
    data.loc[:, obj_cols] = (data.loc[:, obj_cols]
                                 .astype('string'))
    return data


def _factor_wrangler(
    data: pd.DataFrame,
    cat_cols: Union[None, List[str]],
    ordered_cols: Union[None, List[str]],
    categories: Union[None, Mapping[str, List[Union[str, int, float]]]] = None,
    str_to_cat: bool = True,
) -> pd.DataFrame:
    """Converts columns in `is_factor` to `CategoricalDtype`.
    If `str_to_cat` is set to True, converts all `StringDtype` columns
    to `CategoricalDtype`.
    """
    all_cat_cols = []
    if str_to_cat:
        str_cols = (data.select_dtypes(include=['string'])
                        .columns
                        .tolist())
        cat_cols += str_cols
    if cat_cols:
        all_cat_cols += cat_cols
    if all_cat_cols:
        for col in all_cat_cols:
            data.loc[:, col] = (data.loc[:, col]
                                    .astype('category'))
    # Set categories
    if categories:
        for col, cats in categories.items():
            data.loc[:, col] = (data.loc[:, col]
                                    .cat
                                    .set_categories(cats))
    # Set is_ordered
    if ordered_cols:
        for col in ordered_cols:
            data.loc[:, col] = (data.loc[:, col]
                                    .cat
                                    .as_ordered())
    return data


def clean_data(
    data: pd.DataFrame,
    cat_cols: Union[None, List[str]] = None,
    ordered_cols: Union[None, List[str]] = None,
    categories: Union[None, Mapping[str, List[Union[str, int, float]]]] = None,
    str_to_cat: bool = True,
) -> pd.DataFrame:
    """Data preprocessing pipeline.
    Runs the following data wranglers on `data`:
    1. _obj_wrangler
    2. _factor_wrangler
    """
    data = (data.pipe(_obj_wrangler)
                .pipe(_factor_wrangler,
                      cat_cols,
                      ordered_cols,
                      categories,
                      str_to_cat))
    return data


def encode_data(data: pd.DataFrame) -> pd.DataFrame:
    """Transforms columns with `category` dtype using `series.cat.codes`.
    """
    unordered_mask = data.apply(lambda col: is_categorical_dtype(col) and
                                not(col.cat.ordered))
    ordered_mask = data.apply(lambda col: is_categorical_dtype(col) and
                              col.cat.ordered)
    unordered = (data.loc[:, unordered_mask]
                     .columns
                     .tolist())
    ordered = (data.loc[:, ordered_mask]
                   .columns
                   .tolist())
    data.loc[:, ordered + unordered] = (data.loc[:, ordered + unordered]
                                            .apply(lambda x: x.cat.codes))
    return data


def run_automl(data: pd.DataFrame,
               outcome_col: str,
               ml_task: str,
               train_size: float,
               test_size: float,
               *args, **kwargs) -> str:
    """Runs AutoML using TPOT. Returns best pipeline found by TPOT as a string
    of Python code.
    """
    # Outcome
    data = data.rename(columns={outcome_col: 'target'})  # Rename outcome col
    # Filter only valid columns
    # with potentially not-found cols (i.e. dummies)
    outcome = data.loc[:, 'target']
    # Features
    features = data.loc[:, ~data.columns.str.match('target')]
    if len(outcome) == 1:
        outcome = outcome[0]
    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(features,
                                                        outcome,
                                                        train_size=train_size,
                                                        test_size=test_size)
    # Optimise pipeline
    if ml_task == 'Classification':
        tpot = TPOTClassifier(**kwargs)
        tpot.fit(X_train, y_train)
    else:
        tpot = TPOTRegressor(**kwargs)
        tpot.fit(X_train, y_train)
    # Export Python code for best pipeline found
    pipeline_code = tpot.export()
    return pipeline_code


if __name__ == "__main__":
    pass
