from sklearn.base import clone
from sklearn.pipeline import make_pipeline, make_union
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, SplineTransformer
from sklearn.compose import make_column_transformer
from sklearn.feature_extraction.text import CountVectorizer
from skrub import SelectCols
from .transformer_functions import column_pluck, datetime_feats
from .formula import PlaytimePipeline

def seasonal(colname, n_knots=12):
    """Calculate a yearly seasonal feature from a date column."""
    return PlaytimePipeline(
        pipeline=make_pipeline(
            FunctionTransformer(datetime_feats, kw_args={"column": colname}),
            SplineTransformer(
                extrapolation="periodic", knots="uniform", n_knots=n_knots
            ),
        )
    )

def feats(*colnames):
    """Select features from a dataframe as-is. Meant for numeric features."""
    # Still undecided if `select()` is a better name here
    return select(*colnames)

def select(*colnames):
    """
    **select**

    Select features from a dataframe as-is. Meant for numeric features.
    
    Arguments:
        colnames: names of columns to select
    
    **Usage**

    ```python
    from playtime import select 

    pipeline = select("col_a", "col_b")
    ```
    """
    return PlaytimePipeline(
        pipeline=make_pipeline(SelectCols([col for col in colnames]))
    )

def onehot(*colnames, **kwargs):
    """One-hot encode specified columns, resulting in a sparse set of features."""
    return select(*colnames) | OneHotEncoder(**kwargs)

def minhash(*colnames, **kwargs):
    """Create min-hash features for specified columns, resulting in a dense set of features."""
    from skrub import MinHashEncoder
    return estimator_for_all_columns(MinHashEncoder(**kwargs), *colnames)

def bag_of_words(*colnames, **kwargs):
    """Generate bag-of-words features on a set of column, assuming it refers to text."""
    return estimator_for_all_columns(CountVectorizer(**kwargs), *colnames)


def embed_text(*colnames, name='all-MiniLM-L6-v2', **kwargs):
    """Generate text embedding features on a set of columns, assuming it refers to text."""
    from embetter.text import SentenceEncoder

    return estimator_for_all_columns(SentenceEncoder(name, **kwargs), *colnames)

def embed_image(*colnames):
    """Generate image embedding features on a set of columns using CLIP, assuming it refers to an image path."""
    from embetter.grab import ColumnGrabber
    from embetter.vision import ImageLoader
    from embetter.multi import ClipEncoder

    est = make_pipeline(
        ImageLoader(convert="RGB"),
        ClipEncoder()
    )
    return estimator_for_all_columns(est, *colnames)

def estimator_for_all_columns(estimator, *columns):
    return PlaytimePipeline(make_column_transformer(*[(clone(estimator), col) for col in columns]))
