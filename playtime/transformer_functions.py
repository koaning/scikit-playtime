import polars as pl
import narwhals as nw


def datetime_feats(dataf, column, kind="days"):
    nw_df = nw.from_native(dataf)
    if kind == "days":
        nw_out = nw_df.with_columns(
            day_of_year=nw.col(column).dt.ordinal_day()
        ).select("_dt_feat")
    if kind == "hours":
        nw_out = nw_df.with_columns(
            hour_of_day=nw.col(column).dt.hour()
        ).select("_dt_feat")
    if kind == "minutes":
        nw_out = nw_df.with_columns(
            minute_of_hour=nw.col(column).dt.hour()
        ).select("_dt_feat")

    return nw.to_native(nw_out)


def column_pluck(dataf, column):
    return pl.DataFrame(dataf)[column].to_list()
