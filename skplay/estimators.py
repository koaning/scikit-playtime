import narwhals as nw
from sklearn.base import BaseEstimator, TransformerMixin


class SelectCols(TransformerMixin, BaseEstimator):
    """Select a subset of a DataFrame's columns.

    A ``ValueError`` is raised if any of the provided column names are not in
    the dataframe.

    Accepts anything accepted by :func:`narwhals.from_native(..., eager_only=True)`.

    Arguments
        cols : list of str or str
            The columns to select. A single column name can be passed as a ``str``:
            ``"col_name"`` is the same as ``["col_name"]``.

    **Usage**
    ```python
    >>> import polars as pl
    >>> from skplay.estimators import SelectCols
    >>> df = pl.DataFrame({"A": [1, 2], "B": [10, 20], "C": ["x", "y"]})
    >>> df
       A   B  C
    0  1  10  x
    1  2  20  y
    >>> SelectCols(["C", "A"]).fit_transform(df)
       C  A
    0  x  1
    1  y  2
    >>> SelectCols(["X", "A"]).fit_transform(df)
    Traceback (most recent call last):
        ...
    ValueError: The following columns are requested for selection but missing from dataframe: ['X']
    ```
    """

    def __init__(self, cols=None):
        self.cols = cols

    def fit(self, X, y=None):
        """Fit the transformer.

        Arguments
            X : DataFrame or None
                If `X` is a DataFrame, the transformer checks that all the column
                names provided in ``self.cols`` can be found in `X`.

            y : None
                Unused.

        Returns
        -------
        SelectCols
            The transformer itself.
        """
        nw.from_native(X, eager_only=True).select(self.cols)
        return self

    def transform(self, X):
        """Transform a dataframe by selecting columns.

        Parameters
        ----------
        X : DataFrame
            The DataFrame on which to apply the selection.

        Returns
        -------
        DataFrame
            The input DataFrame ``X`` after selecting only the columns listed
            in ``self.cols`` (in the provided order).
        """
        return nw.from_native(X, eager_only=True).select(self.cols)
