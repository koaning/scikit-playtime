import pytest

from skplay.estimators import SelectCols


@pytest.mark.parametrize("lib", ["pandas", "polars"])
def test_select_cols(lib):
    lib = pytest.importorskip(lib)

    df = lib.DataFrame({"a": [1, 2], "b": [10, 20], "c": ["x", "y"]})
    tfm = SelectCols(["a", "b"])
    # This should work w/o calling `fit`
    assert tfm.transform(df).columns == ["a", "b"]
    # This should also pass
    tfm.fit(df)

    # In reality it's either a KeyError or a pl.exceptions.ColumnNotFoundError
    with pytest.raises(Exception):
        SelectCols(["a", "b", "d"]).fit(df)
