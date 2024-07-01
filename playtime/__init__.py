from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, SplineTransformer
from sklearn.feature_extraction.text import CountVectorizer
from skrub import SelectCols
from .transformer_functions import PlaytimePipeline, column_pluck, datetime_feats

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
    return PlaytimePipeline(
        pipeline=make_pipeline(SelectCols([col for col in colnames]))
    )


def onehot(*colnames):
    """One-hot encode specified columns, resulting in a sparse set of features."""
    return PlaytimePipeline(
        pipeline=make_pipeline(SelectCols(colnames), OneHotEncoder())
    )


def bag_of_words(colname, **kwargs):
    """Generate bag-of-words features on a column, assuming it refers to text."""
    return PlaytimePipeline(
        pipeline=make_pipeline(
            FunctionTransformer(column_pluck, kw_args={"column": colname}),
            CountVectorizer(**kwargs),
        )
    )
