import numpy as np 
from time import time as timer
import itertools as it 
from sklearn.base import clone, BaseEstimator, MetaEstimatorMixin
from sklearn.pipeline import make_pipeline, make_union, FeatureUnion
from sklearn.preprocessing import PolynomialFeatures, SplineTransformer, OneHotEncoder
from skrub import SelectCols
from scipy.sparse import hstack, coo_array, issparse, csc_array


# class UnionPolynomialFeaturizer(BaseEstimator, MetaEstimatorMixin):
#     def __init__(self, union_estimator):
#         """Like the normal polynomial featurizer, but in this case only consider the product from different transformers"""
#         self.union_estimator = union_estimator
        
#     def _combinations(self, n_features, min_degree, max_degree, interaction_only, include_bias):
#         for i in range(self.split_at_):
#             for j in range(self.split_at_, self.shape_out_):
#                 yield (i, j)
    
#     def _num_combinations(self, n_features, min_degree, max_degree, interaction_only, include_bias):
#         total = 0
#         for i in range(self.split_at_):
#             for j in range(self.split_at_, self.shape_out_):
#                 total += 1 
#         return total

#     def fit(self, X, y=None):
#         self.vendored_poly_ = PolynomialFeatures(interaction_only=True)
#         self.vendored_poly_._combinations = self._combinations
#         X_tfm = self.union_estimator.fit_transform(X)
#         total = X_tfm.shape[1]
#         self.vendored_poly_.fit(X_tfm)
#         # todo: kind of hacky. clean? 
#         self.split_at_ = self.union_estimator.transformer_list[0][1].transform(X).shape[1]
#         self.shape_out_ = self.split_at_ * (total - self.split_at_)
#         return self

#     def transform(self, X):
#         X_tfm = self.union_estimator.transform(X)
#         return self.vendored_poly_.transform(X_tfm)
    
    
class UnionPolynomialFeaturizer(BaseEstimator, MetaEstimatorMixin):
    def __init__(self, union_estimator):
        """Like the normal polynomial featurizer, but in this case only consider the product from different transformers"""
        self.union_estimator = union_estimator

    def fit(self, X, y=None):
        X_tfm = self.union_estimator.fit_transform(X)
        total = X_tfm.shape[1]
        # todo: kind of hacky. clean? 
        self.split_at_ = self.union_estimator.transformer_list[0][1].transform(X[:2]).shape[1]
        self.shape_out_ = self.split_at_ * (total - self.split_at_)
        return self

    def transform(self, X):
        columns = []
        X_tfm = self.union_estimator.transform(X)
        if issparse(X_tfm):
            X_tfm = csc_array(X_tfm)
        X1, X2 = X_tfm[:, :self.split_at_], X_tfm[:, self.split_at_:]
        for x in range(X2.shape[1]):
            columns.append(X1 * X2[:, [x]])
        if issparse(X_tfm):
            return hstack(columns, dtype=X_tfm.dtype).tocsc()
        return np.hstack(columns, dtype=X_tfm.dtype)


class Node:
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def __add__(self, other):
        if isinstance(self.pipeline, FeatureUnion):
            old_transformers = [_[1] for _ in self.pipeline.transformer_list]
            new_transformers = old_transformers + [clone(other.pipeline)]
            new_pipeline = make_union(*new_transformers)
        else:
            new_pipeline = make_union(self.pipeline, other.pipeline)
        return Node(pipeline=new_pipeline)

    def __mul__(self, other):
        combined = UnionPolynomialFeaturizer(make_union(clone(self.pipeline), clone(other.pipeline))) 
        return Node(pipeline=combined)


def seasonal(colname):
    return Node(pipeline=make_pipeline(
        SelectCols([colname]),
        SplineTransformer(extrapolation="periodic", knots="uniform", n_knots=5)
    ))

def feats(*colnames):
    return Node(pipeline=SelectCols([col for col in colnames]))

def dummy(*colnames):
    return Node(pipeline=make_union(
        *[make_pipeline(SelectCols(col), OneHotEncoder()) for col in colnames]
    ))

def time(colname):
    return Node(pipeline=SelectCols([colname]))
