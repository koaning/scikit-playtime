from sklearn.base import clone
from sklearn.pipeline import make_pipeline, make_union, FeatureUnion
from sklearn.preprocessing import PolynomialFeatures, SplineTransformer, OneHotEncoder
from skrub import SelectCols

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
        combined = make_pipeline(
            make_union(clone(self.pipeline), clone(other.pipeline)), 
            PolynomialFeatures(degree=2, interaction_only=True)
        )
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
