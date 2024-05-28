import pytest
from pathlib import Path
from playtime.formula import feats, onehot, bag_of_words
import pandas as pd
import polars as pl
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV

titanic_path = Path(__file__).parent / 'data' / 'titanic.csv'


@pytest.mark.parametrize('df', [pd.read_csv(titanic_path), pl.read_csv(titanic_path)])
def test_feats(df):
    assert feats('age').fit_transform(df).shape[1] == 1
    assert feats('age', 'fare').fit_transform(df).shape[1] == 2
    assert feats('age', 'fare', 'sibsp', 'parch').fit_transform(df).shape[1] == 4


@pytest.mark.parametrize('df', [pd.read_csv(titanic_path), pl.read_csv(titanic_path)])
def test_onehot(df):
    assert onehot('sex').fit_transform(df).shape[1] == 2
    assert onehot('pclass').fit_transform(df).shape[1] == 3
    assert onehot('sex', 'pclass').fit_transform(df).shape[1] == 5


@pytest.mark.parametrize('df', [pd.read_csv(titanic_path), pl.read_csv(titanic_path)])
def test_bow(df):
    assert bag_of_words('name').fit_transform(df).shape[1] > 10
    assert bag_of_words('name', analyzer='char', ngram_range=(2, 3)).fit_transform(df).shape[1] > 100


@pytest.mark.parametrize('df', [pd.read_csv(titanic_path), pl.read_csv(titanic_path)])
def test_pipeline(df):
    feat_pipe = feats("age", "fare", "sibsp", "parch") + onehot("sex", "pclass") + bag_of_words("name")
    # Confirm that we can fit just the features
    assert feat_pipe.fit_transform(df)
    print(feat_pipe).fit_transform(df)
    full_pipe = make_pipeline(feat_pipe, LogisticRegression(max_iter=1000))
    # Confirm that we can fit like normal
    assert full_pipe.fit(df, df['survived'])
    # Confirm that we can gridsearch too
    grid = GridSearchCV(full_pipe, {}, cv=2)
    print(df['survived'].to_list())
    assert grid.fit(df, df['survived'])