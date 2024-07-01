import polars as pl
import narwhals as nw


def datetime_feats(dataf, column):
    nw_df = nw.from_native(dataf)
    nw_out = nw_df.with_columns(
        day_of_year=nw.col(column).str.to_datetime(format="%Y-%m-%d").dt.ordinal_day()
    ).select("day_of_year")

    return nw.to_native(nw_out)


def column_pluck(dataf, column):
    return pl.DataFrame(dataf)[column].to_list()
