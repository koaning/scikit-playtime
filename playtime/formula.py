import itertools as it
import narwhals as nw
import numpy as np
import polars as pl
from scipy.sparse import csc_array, hstack, issparse
from sklearn.base import MetaEstimatorMixin, clone, BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import FeatureUnion, make_pipeline, make_union, Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, SplineTransformer
from skrub import SelectCols


class UnionPolynomialFeaturizer(BaseEstimator, MetaEstimatorMixin):
    def __init__(self, union_estimator):
        """Like the normal polynomial featurizer, but in this case only consider the product from different transformers"""
        self.union_estimator = union_estimator

    def fit(self, X, y=None):
        X_tfm = self.union_estimator.fit_transform(X)
        total = X_tfm.shape[1]
        # todo: kind of hacky. clean?
        self.split_at_ = (
            self.union_estimator.transformer_list[0][1].transform(X[:2]).shape[1]
        )
        self.shape_out_ = self.split_at_ * (total - self.split_at_)
        return self

    def transform(self, X):
        columns = []
        X_tfm = self.union_estimator.transform(X)
        if issparse(X_tfm):
            X_tfm = csc_array(X_tfm)
        X1, X2 = X_tfm[:, : self.split_at_], X_tfm[:, self.split_at_ :]
        for x in range(X2.shape[1]):
            columns.append(X1 * X2[:, [x]])
        if issparse(X_tfm):
            return hstack(columns, dtype=X_tfm.dtype).tocsc()
        return np.hstack(columns, dtype=X_tfm.dtype)


class CrossPolyPipeline(BaseEstimator, TransformerMixin):
    def __init__(self, union_estimator):
        self.union_estimator = union_estimator
        self.transformer_list = union_estimator.transformer_list

    def fit(self, X, y=None):
        self.split_marks_ = {}
        start = 0
        self.union_estimator.fit(X)
        for name, tfm in self.union_estimator.transformer_list:
            width = tfm.transform(X[:2]).shape[1]
            self.split_marks_[name] = slice(start, start + width)
            start = width + start

        self.shape_out_ = start
        return self

    def transform(self, X):
        columns = []
        X_tfm = self.union_estimator.transform(X)
        if issparse(X_tfm):
            X_tfm = csc_array(X_tfm)
        for name1, name2 in it.combinations(self.split_marks_.keys(), 2):
            X1, X2 = (
                X_tfm[:, self.split_marks_[name1]],
                X_tfm[:, self.split_marks_[name2]],
            )
        for x in range(X2.shape[1]):
            columns.append(X1 * X2[:, [x]])
        if issparse(X_tfm):
            return hstack(columns, dtype=X_tfm.dtype).tocsc()
        return np.hstack(columns, dtype=X_tfm.dtype)


class PlaytimePipeline(BaseEstimator):
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def __add__(self, other):
        if isinstance(self.pipeline, FeatureUnion):
            old_transformers = [_[1] for _ in self.pipeline.transformer_list]
            new_transformers = old_transformers + [clone(other.pipeline)]
            new_pipeline = make_union(*new_transformers)
        else:
            new_pipeline = make_union(self.pipeline, other.pipeline)
        return PlaytimePipeline(pipeline=new_pipeline)

    def __mul__(self, other):
        if not isinstance(self, CrossPolyPipeline) and not isinstance(
            other, CrossPolyPipeline
        ):
            # This is a special case, it is rare, but they could both be cross prod already
            unioned_feats = (self + other).pipeline
        elif isinstance(other.pipeline, FeatureUnion):
            # We know that the self is the CrossPolyPipeline in this case
            old_transformers = [_[1] for _ in self.pipeline.transformer_list]
            unioned_feats = old_transformers + [clone(other.pipeline)]
        elif isinstance(self.pipeline, (Pipeline, FeatureUnion)):
            # We know that the other is the CrossPolyPipeline in this case
            old_transformers = [_[1] for _ in other.pipeline.transformer_list]
            unioned_feats = old_transformers + [clone(self.pipeline)]
        return PlaytimePipeline(pipeline=CrossPolyPipeline(unioned_feats))

    def fit(self, X, y=None, **kwargs):
        self.pipeline.fit(X, y, **kwargs)
        return self

    def transform(self, X, **kwargs):
        return self.pipeline.transform(X, **kwargs)

    def fit_transform(self, X, y=None, **kwargs):
        return self.pipeline.fit_transform(X, y, **kwargs)


def datetime_feats(dataf, column):
    nw_df = nw.from_native(dataf)

    nw_out = nw_df.with_columns(
        day_of_year=nw.col(column).str.to_datetime(format="%Y-%m-%d").dt.ordinal_day()
    ).select("day_of_year")

    return nw.to_native(nw_out)


def column_pluck(dataf, column):
    return pl.DataFrame(dataf)[column].to_list()


def seasonal(colname, n_knots=12):
    return PlaytimePipeline(
        pipeline=make_pipeline(
            FunctionTransformer(datetime_feats, kw_args={"column": colname}),
            SplineTransformer(
                extrapolation="periodic", knots="uniform", n_knots=n_knots
            ),
        )
    )


def feats(*colnames):
    return PlaytimePipeline(
        pipeline=make_pipeline(SelectCols([col for col in colnames]))
    )


def onehot(*colnames):
    return PlaytimePipeline(
        pipeline=make_pipeline(SelectCols(colnames), OneHotEncoder())
    )


def time(colname):
    return PlaytimePipeline(pipeline=SelectCols([colname]))


def bag_of_words(colname, **kwargs):
    return PlaytimePipeline(
        pipeline=make_pipeline(
            FunctionTransformer(column_pluck, kw_args={"column": colname}),
            CountVectorizer(**kwargs),
        )
    )
