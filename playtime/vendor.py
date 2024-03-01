"""
This file contains preprocessing tools based on polynomials.
"""
import collections
from sklearn.base import clone, BaseEstimator, MetaEstimatorMixin
from itertools import chain, combinations
from itertools import combinations_with_replacement as combinations_w_r
from numbers import Integral

import numpy as np
from scipy import sparse
from scipy.special import comb

from sklearn.base import BaseEstimator, TransformerMixin, _fit_context
from sklearn.utils._param_validation import Interval, StrOptions
from sklearn.utils.fixes import parse_version, sp_version
from sklearn.utils.validation import (
    FLOAT_DTYPES,
    _check_feature_names_in,
    check_is_fitted,
)
from sklearn.preprocessing._csr_polynomial_expansion import (
    _calc_expanded_nnz,
    _calc_total_nnz,
    _csr_polynomial_expansion,
)

__all__ = [
    "PolynomialFeatures",
]


def _create_expansion(X, interaction_only, deg, n_features, cumulative_size=0):
    """Helper function for creating and appending sparse expansion matrices"""

    total_nnz = _calc_total_nnz(X.indptr, interaction_only, deg)
    expanded_col = _calc_expanded_nnz(n_features, interaction_only, deg)

    if expanded_col == 0:
        return None
    # This only checks whether each block needs 64bit integers upon
    # expansion. We prefer to keep int32 indexing where we can,
    # since currently SciPy's CSR construction downcasts when possible,
    # so we prefer to avoid an unnecessary cast. The dtype may still
    # change in the concatenation process if needed.
    # See: https://github.com/scipy/scipy/issues/16569
    max_indices = expanded_col - 1
    max_indptr = total_nnz
    max_int32 = np.iinfo(np.int32).max
    needs_int64 = max(max_indices, max_indptr) > max_int32
    index_dtype = np.int64 if needs_int64 else np.int32

    # This is a pretty specific bug that is hard to work around by a user,
    # hence we do not detail the entire bug and all possible avoidance
    # mechnasisms. Instead we recommend upgrading scipy or shrinking their data.
    cumulative_size += expanded_col
    if (
        sp_version < parse_version("1.8.0")
        and cumulative_size - 1 > max_int32
        and not needs_int64
    ):
        raise ValueError(
            "In scipy versions `<1.8.0`, the function `scipy.sparse.hstack`"
            " sometimes produces negative columns when the output shape contains"
            " `n_cols` too large to be represented by a 32bit signed"
            " integer. To avoid this error, either use a version"
            " of scipy `>=1.8.0` or alter the `PolynomialFeatures`"
            " transformer to produce fewer than 2^31 output features."
        )

    # Result of the expansion, modified in place by the
    # `_csr_polynomial_expansion` routine.
    expanded_data = np.empty(shape=total_nnz, dtype=X.data.dtype)
    expanded_indices = np.empty(shape=total_nnz, dtype=index_dtype)
    expanded_indptr = np.empty(shape=X.indptr.shape[0], dtype=index_dtype)
    _csr_polynomial_expansion(
        X.data,
        X.indices,
        X.indptr,
        X.shape[1],
        expanded_data,
        expanded_indices,
        expanded_indptr,
        interaction_only,
        deg,
    )
    return sparse.csr_matrix(
        (expanded_data, expanded_indices, expanded_indptr),
        shape=(X.indptr.shape[0] - 1, expanded_col),
        dtype=X.dtype,
    )


class PolynomialFeatures(TransformerMixin, BaseEstimator):
    """Generate polynomial and interaction features.

    Generate a new feature matrix consisting of all polynomial combinations
    of the features with degree less than or equal to the specified degree.
    For example, if an input sample is two dimensional and of the form
    [a, b], the degree-2 polynomial features are [1, a, b, a^2, ab, b^2].

    Read more in the :ref:`User Guide <polynomial_features>`.

    Parameters
    ----------
    degree : int or tuple (min_degree, max_degree), default=2
        If a single int is given, it specifies the maximal degree of the
        polynomial features. If a tuple `(min_degree, max_degree)` is passed,
        then `min_degree` is the minimum and `max_degree` is the maximum
        polynomial degree of the generated features. Note that `min_degree=0`
        and `min_degree=1` are equivalent as outputting the degree zero term is
        determined by `include_bias`.

    interaction_only : bool, default=False
        If `True`, only interaction features are produced: features that are
        products of at most `degree` *distinct* input features, i.e. terms with
        power of 2 or higher of the same input feature are excluded:

            - included: `x[0]`, `x[1]`, `x[0] * x[1]`, etc.
            - excluded: `x[0] ** 2`, `x[0] ** 2 * x[1]`, etc.

    include_bias : bool, default=True
        If `True` (default), then include a bias column, the feature in which
        all polynomial powers are zero (i.e. a column of ones - acts as an
        intercept term in a linear model).

    order : {'C', 'F'}, default='C'
        Order of output array in the dense case. `'F'` order is faster to
        compute, but may slow down subsequent estimators.

        .. versionadded:: 0.21

    Attributes
    ----------
    powers_ : ndarray of shape (`n_output_features_`, `n_features_in_`)
        `powers_[i, j]` is the exponent of the jth input in the ith output.

    n_features_in_ : int
        Number of features seen during :term:`fit`.

        .. versionadded:: 0.24

    feature_names_in_ : ndarray of shape (`n_features_in_`,)
        Names of features seen during :term:`fit`. Defined only when `X`
        has feature names that are all strings.

        .. versionadded:: 1.0

    n_output_features_ : int
        The total number of polynomial output features. The number of output
        features is computed by iterating over all suitably sized combinations
        of input features.

    See Also
    --------
    SplineTransformer : Transformer that generates univariate B-spline bases
        for features.

    Notes
    -----
    Be aware that the number of features in the output array scales
    polynomially in the number of features of the input array, and
    exponentially in the degree. High degrees can cause overfitting.

    See :ref:`examples/linear_model/plot_polynomial_interpolation.py
    <sphx_glr_auto_examples_linear_model_plot_polynomial_interpolation.py>`

    Examples
    --------
    >>> import numpy as np
    >>> from sklearn.preprocessing import PolynomialFeatures
    >>> X = np.arange(6).reshape(3, 2)
    >>> X
    array([[0, 1],
           [2, 3],
           [4, 5]])
    >>> poly = PolynomialFeatures(2)
    >>> poly.fit_transform(X)
    array([[ 1.,  0.,  1.,  0.,  0.,  1.],
           [ 1.,  2.,  3.,  4.,  6.,  9.],
           [ 1.,  4.,  5., 16., 20., 25.]])
    >>> poly = PolynomialFeatures(interaction_only=True)
    >>> poly.fit_transform(X)
    array([[ 1.,  0.,  1.,  0.],
           [ 1.,  2.,  3.,  6.],
           [ 1.,  4.,  5., 20.]])
    """

    _parameter_constraints: dict = {
        "degree": [Interval(Integral, 0, None, closed="left"), "array-like"],
        "interaction_only": ["boolean"],
        "include_bias": ["boolean"],
        "order": [StrOptions({"C", "F"})],
    }

    def __init__(
        self, degree=2, *, interaction_only=False, include_bias=True, order="C"
    ):
        self.degree = degree
        self.interaction_only = interaction_only
        self.include_bias = include_bias
        self.order = order

    @staticmethod
    def _combinations(
        n_features, min_degree, max_degree, interaction_only, include_bias
    ):
        comb = combinations if interaction_only else combinations_w_r
        start = max(1, min_degree)
        iter = chain.from_iterable(
            comb(range(n_features), i) for i in range(start, max_degree + 1)
        )
        if include_bias:
            iter = chain(comb(range(n_features), 0), iter)
        return iter

    @staticmethod
    def _num_combinations(
        n_features, min_degree, max_degree, interaction_only, include_bias
    ):
        """Calculate number of terms in polynomial expansion

        This should be equivalent to counting the number of terms returned by
        _combinations(...) but much faster.
        """

        if interaction_only:
            combinations = sum(
                [
                    comb(n_features, i, exact=True)
                    for i in range(max(1, min_degree), min(max_degree, n_features) + 1)
                ]
            )
        else:
            combinations = comb(n_features + max_degree, max_degree, exact=True) - 1
            if min_degree > 0:
                d = min_degree - 1
                combinations -= comb(n_features + d, d, exact=True) - 1

        if include_bias:
            combinations += 1

        return combinations

    @property
    def powers_(self):
        """Exponent for each of the inputs in the output."""
        check_is_fitted(self)

        combinations = self._combinations(
            n_features=self.n_features_in_,
            min_degree=self._min_degree,
            max_degree=self._max_degree,
            interaction_only=self.interaction_only,
            include_bias=self.include_bias,
        )
        return np.vstack(
            [np.bincount(c, minlength=self.n_features_in_) for c in combinations]
        )

    def get_feature_names_out(self, input_features=None):
        """Get output feature names for transformation.

        Parameters
        ----------
        input_features : array-like of str or None, default=None
            Input features.

            - If `input_features is None`, then `feature_names_in_` is
              used as feature names in. If `feature_names_in_` is not defined,
              then the following input feature names are generated:
              `["x0", "x1", ..., "x(n_features_in_ - 1)"]`.
            - If `input_features` is an array-like, then `input_features` must
              match `feature_names_in_` if `feature_names_in_` is defined.

        Returns
        -------
        feature_names_out : ndarray of str objects
            Transformed feature names.
        """
        powers = self.powers_
        input_features = _check_feature_names_in(self, input_features)
        feature_names = []
        for row in powers:
            inds = np.where(row)[0]
            if len(inds):
                name = " ".join(
                    (
                        "%s^%d" % (input_features[ind], exp)
                        if exp != 1
                        else input_features[ind]
                    )
                    for ind, exp in zip(inds, row[inds])
                )
            else:
                name = "1"
            feature_names.append(name)
        return np.asarray(feature_names, dtype=object)

    @_fit_context(prefer_skip_nested_validation=True)
    def fit(self, X, y=None):
        """
        Compute number of output features.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            The data.

        y : Ignored
            Not used, present here for API consistency by convention.

        Returns
        -------
        self : object
            Fitted transformer.
        """
        _, n_features = self._validate_data(X, accept_sparse=True).shape

        if isinstance(self.degree, Integral):
            if self.degree == 0 and not self.include_bias:
                raise ValueError(
                    "Setting degree to zero and include_bias to False would result in"
                    " an empty output array."
                )

            self._min_degree = 0
            self._max_degree = self.degree
        elif (
            isinstance(self.degree, collections.abc.Iterable) and len(self.degree) == 2
        ):
            self._min_degree, self._max_degree = self.degree
            if not (
                isinstance(self._min_degree, Integral)
                and isinstance(self._max_degree, Integral)
                and self._min_degree >= 0
                and self._min_degree <= self._max_degree
            ):
                raise ValueError(
                    "degree=(min_degree, max_degree) must "
                    "be non-negative integers that fulfil "
                    "min_degree <= max_degree, got "
                    f"{self.degree}."
                )
            elif self._max_degree == 0 and not self.include_bias:
                raise ValueError(
                    "Setting both min_degree and max_degree to zero and include_bias to"
                    " False would result in an empty output array."
                )
        else:
            raise ValueError(
                "degree must be a non-negative int or tuple "
                "(min_degree, max_degree), got "
                f"{self.degree}."
            )

        self.n_output_features_ = self._num_combinations(
            n_features=n_features,
            min_degree=self._min_degree,
            max_degree=self._max_degree,
            interaction_only=self.interaction_only,
            include_bias=self.include_bias,
        )
        if self.n_output_features_ > np.iinfo(np.intp).max:
            msg = (
                "The output that would result from the current configuration would"
                f" have {self.n_output_features_} features which is too large to be"
                f" indexed by {np.intp().dtype.name}. Please change some or all of the"
                " following:\n- The number of features in the input, currently"
                f" {n_features=}\n- The range of degrees to calculate, currently"
                f" [{self._min_degree}, {self._max_degree}]\n- Whether to include only"
                f" interaction terms, currently {self.interaction_only}\n- Whether to"
                f" include a bias term, currently {self.include_bias}."
            )
            if (
                np.intp == np.int32
                and self.n_output_features_ <= np.iinfo(np.int64).max
            ):  # pragma: nocover
                msg += (
                    "\nNote that the current Python runtime has a limited 32 bit "
                    "address space and that this configuration would have been "
                    "admissible if run on a 64 bit Python runtime."
                )
            raise ValueError(msg)
        # We also record the number of output features for
        # _max_degree = 0
        self._n_out_full = self._num_combinations(
            n_features=n_features,
            min_degree=0,
            max_degree=self._max_degree,
            interaction_only=self.interaction_only,
            include_bias=self.include_bias,
        )

        return self

    def transform(self, X):
        """Transform data to polynomial features.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            The data to transform, row by row.

            Prefer CSR over CSC for sparse input (for speed), but CSC is
            required if the degree is 4 or higher. If the degree is less than
            4 and the input format is CSC, it will be converted to CSR, have
            its polynomial features generated, then converted back to CSC.

            If the degree is 2 or 3, the method described in "Leveraging
            Sparsity to Speed Up Polynomial Feature Expansions of CSR Matrices
            Using K-Simplex Numbers" by Andrew Nystrom and John Hughes is
            used, which is much faster than the method used on CSC input. For
            this reason, a CSC input will be converted to CSR, and the output
            will be converted back to CSC prior to being returned, hence the
            preference of CSR.

        Returns
        -------
        XP : {ndarray, sparse matrix} of shape (n_samples, NP)
            The matrix of features, where `NP` is the number of polynomial
            features generated from the combination of inputs. If a sparse
            matrix is provided, it will be converted into a sparse
            `csr_matrix`.
        """
        check_is_fitted(self)

        X = self._validate_data(
            X, order="F", dtype=FLOAT_DTYPES, reset=False, accept_sparse=("csr", "csc")
        )

        n_samples, n_features = X.shape
        max_int32 = np.iinfo(np.int32).max
        if sparse.issparse(X) and X.format == "csr":
            if self._max_degree > 3:
                return self.transform(X.tocsc()).tocsr()
            to_stack = []
            if self.include_bias:
                to_stack.append(
                    sparse.csr_matrix(np.ones(shape=(n_samples, 1), dtype=X.dtype))
                )
            if self._min_degree <= 1 and self._max_degree > 0:
                to_stack.append(X)

            cumulative_size = sum(mat.shape[1] for mat in to_stack)
            for deg in range(max(2, self._min_degree), self._max_degree + 1):
                expanded = _create_expansion(
                    X=X,
                    interaction_only=self.interaction_only,
                    deg=deg,
                    n_features=n_features,
                    cumulative_size=cumulative_size,
                )
                if expanded is not None:
                    to_stack.append(expanded)
                    cumulative_size += expanded.shape[1]
            if len(to_stack) == 0:
                # edge case: deal with empty matrix
                XP = sparse.csr_matrix((n_samples, 0), dtype=X.dtype)
            else:
                # `scipy.sparse.hstack` breaks in scipy<1.9.2
                # when `n_output_features_ > max_int32`
                all_int32 = all(mat.indices.dtype == np.int32 for mat in to_stack)
                if (
                    sp_version < parse_version("1.9.2")
                    and self.n_output_features_ > max_int32
                    and all_int32
                ):
                    raise ValueError(  # pragma: no cover
                        "In scipy versions `<1.9.2`, the function `scipy.sparse.hstack`"
                        " produces negative columns when:\n1. The output shape contains"
                        " `n_cols` too large to be represented by a 32bit signed"
                        " integer.\n2. All sub-matrices to be stacked have indices of"
                        " dtype `np.int32`.\nTo avoid this error, either use a version"
                        " of scipy `>=1.9.2` or alter the `PolynomialFeatures`"
                        " transformer to produce fewer than 2^31 output features"
                    )
                XP = sparse.hstack(to_stack, dtype=X.dtype, format="csr")
        elif sparse.issparse(X) and X.format == "csc" and self._max_degree < 4:
            return self.transform(X.tocsr()).tocsc()
        elif sparse.issparse(X):
            combinations = self._combinations(
                n_features=n_features,
                min_degree=self._min_degree,
                max_degree=self._max_degree,
                interaction_only=self.interaction_only,
                include_bias=self.include_bias,
            )
            columns = []
            for combi in combinations:
                if combi:
                    out_col = 1
                    for col_idx in combi:
                        out_col = X[:, [col_idx]].multiply(out_col)
                    columns.append(out_col)
                else:
                    bias = sparse.csc_matrix(np.ones((X.shape[0], 1)))
                    columns.append(bias)
            XP = sparse.hstack(columns, dtype=X.dtype).tocsc()
        else:
            # Do as if _min_degree = 0 and cut down array after the
            # computation, i.e. use _n_out_full instead of n_output_features_.
            XP = np.empty(
                shape=(n_samples, self._n_out_full), dtype=X.dtype, order=self.order
            )

            # What follows is a faster implementation of:
            # for i, comb in enumerate(combinations):
            #     XP[:, i] = X[:, comb].prod(1)
            # This implementation uses two optimisations.
            # First one is broadcasting,
            # multiply ([X1, ..., Xn], X1) -> [X1 X1, ..., Xn X1]
            # multiply ([X2, ..., Xn], X2) -> [X2 X2, ..., Xn X2]
            # ...
            # multiply ([X[:, start:end], X[:, start]) -> ...
            # Second optimisation happens for degrees >= 3.
            # Xi^3 is computed reusing previous computation:
            # Xi^3 = Xi^2 * Xi.

            # degree 0 term
            if self.include_bias:
                XP[:, 0] = 1
                current_col = 1
            else:
                current_col = 0

            if self._max_degree == 0:
                return XP

            # degree 1 term
            XP[:, current_col : current_col + n_features] = X
            index = list(range(current_col, current_col + n_features))
            current_col += n_features
            index.append(current_col)

            # loop over degree >= 2 terms
            for _ in range(2, self._max_degree + 1):
                new_index = []
                end = index[-1]
                for feature_idx in range(n_features):
                    start = index[feature_idx]
                    new_index.append(current_col)
                    if self.interaction_only:
                        start += index[feature_idx + 1] - index[feature_idx]
                    next_col = current_col + end - start
                    if next_col <= current_col:
                        break
                    # XP[:, start:end] are terms of degree d - 1
                    # that exclude feature #feature_idx.
                    np.multiply(
                        XP[:, start:end],
                        X[:, feature_idx : feature_idx + 1],
                        out=XP[:, current_col:next_col],
                        casting="no",
                    )
                    current_col = next_col

                new_index.append(current_col)
                index = new_index

            if self._min_degree > 1:
                n_XP, n_Xout = self._n_out_full, self.n_output_features_
                if self.include_bias:
                    Xout = np.empty(
                        shape=(n_samples, n_Xout), dtype=XP.dtype, order=self.order
                    )
                    Xout[:, 0] = 1
                    Xout[:, 1:] = XP[:, n_XP - n_Xout + 1 :]
                else:
                    Xout = XP[:, n_XP - n_Xout :].copy()
                XP = Xout
        return XP


class UnionPolynomialFeatures(PolynomialFeatures, MetaEstimatorMixin):
    def __init__(self, union_estimator):
        self.union_estimator = union_estimator
        super(self).__init__(degree=2, interaction_only=True, include_bias=False)