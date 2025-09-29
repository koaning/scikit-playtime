from sklearn.base import clone
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, SplineTransformer
from sklearn.compose import make_column_transformer
from sklearn.feature_extraction.text import CountVectorizer
from .estimators import SelectCols
from .transformer_functions import datetime_feats
from .formula import PlaytimePipeline
from typing import Any


def seasonal(colname: str, n_knots: int = 12) -> PlaytimePipeline:
    """Calculate a yearly seasonal feature from a date column."""
    return PlaytimePipeline(
        pipeline=make_pipeline(
            FunctionTransformer(datetime_feats, kw_args={"column": colname}),
            SplineTransformer(
                extrapolation="periodic", knots="uniform", n_knots=n_knots
            ),
        )
    )

def spline(n_knots: int = 12, knots="quantile", extrapolation="continue") -> PlaytimePipeline:
    """Calculate a spline over the input features"""
    return PlaytimePipeline(
        pipeline=make_pipeline(
            SplineTransformer(
                extrapolation=extrapolation, knots=knots, n_knots=n_knots
            ),
        )
    )

def feats(*colnames: str) -> PlaytimePipeline:
    """Select features from a dataframe as-is. Meant for numeric features."""
    return select(*colnames)


def select(*colnames: str) -> PlaytimePipeline:
    """
    Select features from a dataframe as-is. Meant for numeric features.

    Arguments:
        colnames: names of columns to select

    **Usage**

    ```python
    from playtime import select

    pipeline = select("col_a", "col_b")
    ```
    """
    return PlaytimePipeline(pipeline=make_pipeline(SelectCols(colnames)))


def onehot(*colnames: str, **kwargs) -> PlaytimePipeline:
    """
    One-hot encode specified columns, resulting in a sparse set of features.
    This transformer will convert categorical variables into a format that can be provided to machine learning algorithms.

    Arguments:
        colnames: names of columns to encode
        **kwargs: additional keyword arguments passed to sklearn's OneHotEncoder

    **Usage**

    ```python
    from playtime import onehot

    pipeline = onehot("category_a", "category_b", sparse=True)
    ```
    """
    return select(*colnames) | OneHotEncoder(**kwargs)


def minhash(*colnames: str, **kwargs) -> PlaytimePipeline:
    """
    Create min-hash features for specified columns, resulting in a dense set of features.

    Arguments:
        colnames: names of columns to encode
        **kwargs: additional keyword arguments passed to skrub's MinHashEncoder

    **Usage**

    ```python
    from playtime import minhash

    pipeline = minhash("high_cardinality_col", n_components=32)
    ```
    """
    from skrub import MinHashEncoder

    return _estimator_for_all_columns(MinHashEncoder(**kwargs), *colnames)


def bag_of_words(*colnames: str, **kwargs) -> PlaytimePipeline:
    """
    Generate bag-of-words features from text columns. This transformer converts text data into a
    sparse matrix of token counts, where each column represents a word from the vocabulary and
    each row represents the frequency of words in the text.

    Arguments:
        colnames: names of text columns to encode
        **kwargs: additional keyword arguments passed to sklearn's CountVectorizer

    **Usage**

    ```python
    from playtime import bag_of_words

    pipeline = bag_of_words("text_column", max_features=1000, ngram_range=(1, 2))
    ```
    """
    return _estimator_for_all_columns(CountVectorizer(**kwargs), *colnames)


def embed_text(
    *colnames: str, name: str = "all-MiniLM-L6-v2", **kwargs
) -> PlaytimePipeline:
    """
    Generate text embedding features using sentence-transformers (via embetter).

    Arguments:
        colnames: names of text columns to encode
        name: name of the sentence transformer model to use (default: 'all-MiniLM-L6-v2')
        **kwargs: additional keyword arguments passed to embetter's SentenceEncoder

    **Usage**

    ```python
    from playtime import embed_text

    # Using default model
    pipeline = embed_text("description_column")

    # Using a different model
    pipeline = embed_text("description_column", name="paraphrase-multilingual-MiniLM-L12-v2")
    ```
    """
    from embetter.text import TextEncoder

    return _estimator_for_all_columns(TextEncoder(name, **kwargs), *colnames)


def embed_sent(
    *colnames: str, name: str = "all-MiniLM-L6-v2", **kwargs
) -> PlaytimePipeline:
    """
    Generate text embedding features using sentence-transformers (via embetter).

    Arguments:
        colnames: names of text columns to encode
        name: name of the sentence transformer model to use (default: 'all-MiniLM-L6-v2')
        **kwargs: additional keyword arguments passed to embetter's SentenceEncoder

    **Usage**

    ```python
    from playtime import embed_sent

    # Using default model
    pipeline = embed_sent("description_column")

    # Using a different model
    pipeline = embed_sent("description_column", name="paraphrase-multilingual-MiniLM-L12-v2")
    ```
    """
    from embetter.text import SentenceEncoder

    return _estimator_for_all_columns(SentenceEncoder(name, **kwargs), *colnames)


def embed_image(*colnames: str) -> PlaytimePipeline:
    """
    Generate image embedding features using CLIP (Contrastive Language-Image Pre-Training) with
    sentence-transformers (via embetter).

    Arguments:
        colnames: names of columns containing image file paths

    **Usage**

    ```python
    from playtime import embed_image

    pipeline = embed_image("image_path_column")
    ```

    Note: The columns should contain valid paths to image files that can be loaded by PIL/Pillow.
    """
    from embetter.vision import ImageLoader
    from embetter.multi import ClipEncoder

    est = make_pipeline(ImageLoader(convert="RGB"), ClipEncoder())
    return _estimator_for_all_columns(est, *colnames)


def _estimator_for_all_columns(estimator: Any, *columns: str) -> PlaytimePipeline:
    return PlaytimePipeline(
        make_column_transformer(*[(clone(estimator), col) for col in columns])
    )
