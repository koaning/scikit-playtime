from sklearn.pipeline import make_pipeline, make_union
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, SplineTransformer
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
    """Select features from a dataframe as-is. Meant for numeric features."""
    return PlaytimePipeline(
        pipeline=make_pipeline(SelectCols([col for col in colnames]))
    )

def onehot(*colnames):
    """One-hot encode specified columns, resulting in a sparse set of features."""
    return select(*colnames) | OneHotEncoder()

def bag_of_words(*colnames, **kwargs):
    """Generate bag-of-words features on a set of column, assuming it refers to text."""

    # The CountVectorizer is a bit interesting here because it demands a single list of text
    # that goes goes in. This is impractical if you want to select multiple columns so we wrap
    # a bunch of things inside of a few `make_union` calls. 

    return PlaytimePipeline(
        pipeline=make_union(
            *[
                make_pipeline(
                    FunctionTransformer(column_pluck, kw_args={"column": col}),
                    CountVectorizer(**kwargs),
                )
                for col in colnames
            ]
        )
    )

def embed_text(*colnames, name='all-MiniLM-L6-v2', **kwargs):
    """Generate text embedding features on a set of columns, assuming it refers to text."""
    from embetter.text import SentenceEncoder

    return PlaytimePipeline(
        pipeline=make_union(
            *[
                make_pipeline(
                    FunctionTransformer(column_pluck, kw_args={"column": col}),
                    SentenceEncoder(name),
                )
                for col in colnames
            ]
        )
    )

def embed_image(*colnames):
    """Generate image embedding features on a set of columns using CLIP, assuming it refers to an image path."""
    from embetter.grab import ColumnGrabber
    from embetter.vision import ImageLoader
    from embetter.multi import ClipEncoder

    return PlaytimePipeline(
        pipeline=make_union(
            *[
                make_pipeline(
                    FunctionTransformer(column_pluck, kw_args={"column": col}),
                    ImageLoader(convert="RGB"),
                    ClipEncoder()
                )
                for col in colnames
            ]
        )
    )
