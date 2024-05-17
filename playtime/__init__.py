import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.utils.fixes import parse_version, sp_version

# This is line is to avoid incompatibility if older SciPy version.
# You should use `solver="highs"` with recent version of SciPy.
solver = "highs" if sp_version >= parse_version("1.6.0") else "interior-point"


def add_ts_features_pd(dataf, ts_col="timestamp"):
    result = (
        dataf.assign(**{ts_col: lambda d: pd.to_datetime(d[ts_col])})
        .assign(
            day_of_week=lambda d: d[ts_col].dt.day_of_week,
            day_of_year=lambda d: d[ts_col].dt.day_of_year,
            minute=lambda d: d[ts_col].dt.minute,
            hour=lambda d: d[ts_col].dt.hour,
        )
        .drop(columns=[ts_col])
    )
    return result


class PlaytimeModel:
    def __init__(
        self, formula, decay=0.999, quantiles=[0.1, 0.5, 0.9], target_col="y", model_by=None, ts_col="timestamp"
    ):
        self.formula = formula
        self.decay = decay
        self.quantiles = quantiles
        self.target_col = target_col
        self.model_by = model_by
        self.ts_col = ts_col

    @property
    def featurizer(self):
        return FunctionTransformer(add_ts_features_pd, kw_args={"ts_col": self.ts_col})

    @property
    def sklearn_pipeline(self):
        # First we apply our own function that generates tons of features
        # then we have sklearn pick up the stuff that we care about
        return make_pipeline(self.featurizer, self.formula.pipeline)

    def learn(self, dataf):
        X = self.transform(dataf)
        print(f"Transformed data has shape={X.shape}.")
        self.models_ = {q: Ridge(positive=True, fit_intercept=False) for q in self.quantiles}
        for k, model in self.models_.items():
            print(f"Fitting model for quantile {k}.")
            model.fit(X, dataf[self.target_col])
        return self

    def transform(self, dataf):
        if not hasattr(self, "transformer_"):
            self.transformer_ = self.sklearn_pipeline
            self.transformer_.fit(dataf)
        return self.transformer_.transform(dataf)

    def featurize(self, dataf):
        return self.featurizer.transform(dataf)

    def predict(self, dataf):
        dataf_out = dataf.copy()
        X = self.transformer_.transform(dataf)
        for k, model in self.models_.items():
            dataf_out[f"quantile-{k}"] = model.predict(X)
        return dataf_out
