import pytest
import numpy as np
from pathlib import Path
from playtime import feats, onehot, bag_of_words, minhash
import pandas as pd
import polars as pl
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV

titanic_path = Path(__file__).parent / "data" / "titanic.csv"


@pytest.mark.parametrize("df", [pd.read_csv(titanic_path), pl.read_csv(titanic_path)])
def test_feats(df):
    assert feats("age").fit_transform(df).shape[1] == 1
    assert feats("age", "fare").fit_transform(df).shape[1] == 2
    assert feats("age", "fare", "sibsp", "parch").fit_transform(df).shape[1] == 4


@pytest.mark.parametrize("df", [pd.read_csv(titanic_path), pl.read_csv(titanic_path)])
def test_onehot(df):
    assert onehot("sex").fit_transform(df).shape[1] == 2
    assert onehot("pclass").fit_transform(df).shape[1] == 3
    assert onehot("sex", "pclass").fit_transform(df).shape[1] == 5


@pytest.mark.parametrize("df", [pd.read_csv(titanic_path), pl.read_csv(titanic_path)])
def test_minhash(df):
    print(df)
    assert minhash("sex", n_components=10).fit_transform(df).shape[1] == 10
    assert minhash("name", n_components=10).fit_transform(df).shape[1] == 10
    assert minhash("sex", "name", n_components=10).fit_transform(df).shape[1] == 20


@pytest.mark.parametrize("df", [pd.read_csv(titanic_path), pl.read_csv(titanic_path)])
def test_bow(df):
    assert bag_of_words("name").fit_transform(df).shape[1] > 10
    assert (
        bag_of_words("name", analyzer="char", ngram_range=(2, 3))
        .fit_transform(df)
        .shape[1]
        > 100
    )


@pytest.mark.parametrize("df", [pd.read_csv(titanic_path), pl.read_csv(titanic_path)])
@pytest.mark.parametrize(
    "feat_pipe",
    [
        feats("age", "fare", "sibsp", "parch"),
        feats("age", "fare", "sibsp", "parch")
        + onehot("sex", "pclass")
        + bag_of_words("name"),
    ],
)
def test_pipeline(df, feat_pipe):
    y = np.array(df["survived"])
    # Confirm that we can fit just the features
    assert feat_pipe.fit_transform(df).shape

    # Confirm that we can fit like normal
    full_pipe = make_pipeline(feat_pipe, LogisticRegression(max_iter=1000))
    assert full_pipe.fit(df, y).predict(df).shape

    # Confirm that we can gridsearch too
    grid = GridSearchCV(full_pipe, {}, cv=2)
    assert grid.fit(df, y).predict(df).shape


