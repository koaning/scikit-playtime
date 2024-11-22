import polars as pl
import narwhals as nw


def datetime_feats(dataf, column, format=None, kind="days"):
    nw_df = nw.from_native(dataf).with_columns(
        _dt_feat=nw.col(column).dt.datetime(format=format)
    )

    if kind == "days":
        nw_out = nw_df.with_columns(day_of_year=nw.col("_dt_feat").dt.ordinal_day()).select(
            "day_of_year"
        )
    if kind == "hours":
        nw_out = nw_df.with_columns(hour_of_day=nw.col("_dt_feat").dt.hour()).select(
            "hour_of_day"
        )
    if kind == "minutes":
        nw_out = nw_df.with_columns(minute_of_hour=nw.col("_dt_feat").dt.hour()).select(
            "minute_of_hour"
        )

    return nw.to_native(nw_out)


def column_pluck(dataf, column):
    return pl.DataFrame(dataf)[column].to_list()
