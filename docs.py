import marimo

__generated_with = "0.16.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    from sklearn.pipeline import make_union, make_pipeline
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.model_selection import GridSearchCV
    from skrub import SelectCols
    return (
        GridSearchCV,
        HistGradientBoostingClassifier,
        OneHotEncoder,
        SelectCols,
        make_pipeline,
        make_union,
        mo,
        pd,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
    # scikit-play

    > Rethinking machine learning pipelines a bit.

    ## What does `scikit-play` do?

    I was wondering if there might be an easier way to construct scikit-learn pipelines. Don't get me wrong, scikit-learn is amazing when you want elaborate pipelines but maybe there is also a place for something more lightweight and playful. This library is all about exploring that.

    Imagine that you are dealing with the titanic dataset.
    """
    )
    return


@app.cell
def _(pd):
    df = pd.read_csv("https://calmcode.io/static/data/titanic.csv")
    df.head()
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
    Here's what the dataset looks like above.

    The goal of this dataset is to predict who survived, so **survived** is the target column for a classification task. But in order to make the right predictions you would need to encode the features in the right way. So to do that, you might construct a preprocessing pipeline like this:
    """
    )
    return


@app.cell
def _(OneHotEncoder, SelectCols, make_pipeline, make_union):
    pipe = make_union(
        SelectCols(["age", "fare", "sibsp", "parch"]),
        make_pipeline(
            SelectCols(["sex", "pclass"]),
            OneHotEncoder()
        )
    )
    pipe
    return (pipe,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
    This pipeline takes the **age**, **fare**, **sibsp** and **parch** features as-is. These features are already numeric so these do not need to be changed. But the **sex** and **pclass** features are candidates to one-hot encode first. These are categorical features, so it helps to encode them as such.

    You can use the pipeline defined above by passing a dataframe in and then getting a numpy array out on the other end. This allows you to use the pipeline as part of a bigger pipeline.
    """
    )
    return


@app.cell
def _(df, pipe):
    # Run the pipeline transformation
    transformed_data = pipe.fit_transform(df)
    print(f"Shape of transformed data: {transformed_data.shape}")
    transformed_data[:5]
    return


@app.cell
def _():
    from skplay import feats, onehot

    formula = feats("age", "fare", "sibsp", "parch") + onehot("sex", "pclass")
    formula
    return feats, onehot


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
    ## Let's also do text.

    Right now we're just exploring base features and one-hot encoding ... but why stop there? We can also encode the name of the passenger using a bag of words representation!
    """
    )
    return


@app.cell
def _(feats, onehot):
    from skplay import bag_of_words

    formula_with_text = feats("age", "fare", "sibsp", "parch") + onehot("sex", "pclass") + bag_of_words("name")
    formula_with_text
    return bag_of_words, formula_with_text


@app.cell
def _(df, formula_with_text):
    # Transform with the text formula
    transformed_with_text = formula_with_text.fit_transform(df)
    print(f"Shape with text features: {transformed_with_text.shape}")
    transformed_with_text[:5, :10]  # Show first 5 rows, first 10 columns
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
    ## Why is this better?

    It's a whole bunch fewer characters to type, sure, but it also enables us to work with syntax that feels more like a formula. We can add preprocessing steps together via `+` and with that we have an opportunity to really simplify how pipelines get made.

    The hope is that simpler pipelines make it easier to "play around" and to construct pipelines that you're actually more likely to understand. In particular, `playtime` should make the simple things easy while still allowing elaborate pipelines when the situation demands it.

    ## Pipelines still compose.

    You can keep adding components to a formula to extend it.
    """
    )
    return


@app.cell
def _(bag_of_words, feats, onehot):
    from skplay import minhash

    extended_formula = feats("age", "fare", "sibsp", "parch") + onehot("sex", "pclass") + bag_of_words("name")
    extended_formula + minhash("name")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
    ## Pipelines are still pipelines.

    The pipelines that come out of the `playtime` library are still just scikit-learn pipelines. That means that you can use them as part of a bigger pipeline if you want to add a machine learning model at the end.
    """
    )
    return


@app.cell
def _(HistGradientBoostingClassifier, df, feats, make_pipeline):
    # Create a full pipeline with a classifier
    X = df.drop(columns=["survived"])
    y = df["survived"]

    full_pipe = make_pipeline(
        feats("age", "fare", "sibsp", "parch"),
        HistGradientBoostingClassifier()
    )

    # Fit and score
    full_pipe.fit(X, y)
    score = full_pipe.score(X, y)
    print(f"Training score: {score:.3f}")

    full_pipe
    return X, y


@app.cell
def _(mo):
    mo.md("""But `playtime` also offers the `|` operator for some of this as well, just as an alternative.""")
    return


@app.cell
def _(bag_of_words, feats, onehot):
    from sklearn.linear_model import LogisticRegression

    model_formula = (
        feats("age", "fare", "sibsp", "parch") + 
        onehot("sex", "pclass") + 
        bag_of_words("name") |
        LogisticRegression()
    )
    model_formula
    return (model_formula,)


@app.cell
def _(X, model_formula, y):
    # Fit and evaluate
    model_formula.fit(X, y)
    model_formula.score(X, y)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
    ## Features

    The goal of the package is to have just a few functions that can aid with column selection and pre-processing. In particular we support a small set of functions to get you started:

    - `playtime.feats` just a selection of the features in the dataframe.
    - `playtime.onehot` is a selection of features that will be one-hot encoded.
    - `playtime.bag_of_words` is a selection of features that will be turned into a count vector.
    - `playtime.normalise` ensures that the features have a standard deviation of 1 and a mean of 0.
    - `playtime.scale` ensures that all the features are between 0 and 1.
    - `playtime.impute` adds an imputation step to the pipeline, not unlike the `SimpleImputer` in scikit-learn.

    On top of that there are also some models available as well that have a slightly different starting value:

    - `playtime.HistGradientBoostingRegressor`
    - `playtime.HistGradientBoostingClassifier`

    These are the exact same models as the ones in scikit-learn but we've gone ahead and set `enable_categorical=True` for you. The idea is that these models are ideal to get started with because they tend to work pretty well without a lot of preprocessing and tuning.

    ## GridSearch, but Fun

    It should also be pointed out that the pipelines defined by `playtime` are just pipelines. 

    That means that these pipelines are also compatible with gridsearch. If you're unfamiliar with the gridsearch feature in scikit-learn then you might appreciate the [video on the topic](https://calmcode.io/scikit-learn/gridsearch.html) but we could use it to iterate over many pipelines to help figure out which one is best. You could use many pipelines explicitly in a gridsearch or you could choose to play with the hyperparameters of a single one to figure out what settings are most appropriate.
    """
    )
    return


@app.cell
def _(GridSearchCV, mo, model_formula):
    # Example of using GridSearch with our pipeline
    param_grid = {
        'histgradientboostingclassifier__max_depth': [3, 5, 7],
        'histgradientboostingclassifier__learning_rate': [0.01, 0.1, 0.2]
    }

    grid_search = GridSearchCV(
        model_formula, 
        param_grid, 
        cv=3,
        scoring='accuracy'
    )

    # Note: In a real scenario, you'd fit this, but it takes time
    # grid_search.fit(X, y)
    # print(f"Best parameters: {grid_search.best_params_}")
    # print(f"Best score: {grid_search.best_score_:.3f}")

    mo.md("""
    The GridSearchCV would allow you to iterate over hyperparameters. In a real scenario, 
    you'd run the fit method to find the best parameters, but this can take some time.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
    ## Installation

    You can install this package via pip:

    ```bash
    python -m pip install scikit-playtime
    ```

    ## Frequently Asked Questions

    ### Can I depend on this library in production?

    This library is a wrapper around scikit-learn. To make the maintenance of this library easy we're being very deliberate in not adding too many features or responsibilities to this library. It's mainly meant as a library for demos and quick experiments so please consider directly using scikit-learn pipelines when you're moving to production.

    But to be absolutely clear, we're also not saying that you cannot use this library in production. Th main thing to remember is that the library only supports features that are general at the moment. It's definitely possible to support more bespoke pipelines, but it might be better to write those pipelines directly with scikit-learn.

    ### Should I use this or scikit-learn?

    The goal of `playtime` is to make it easy to construct preprocessing pipelines for 80% of the use-cases. That includes the usual one-hot-encoding, optional text features and common transformations. If you're doing more bespoke operations then you still may want to pick the more powerful tools available from scikit-learn directly.

    ### Is this dataframe-library agnostic?

    Yes! The library is built on top of narwhals, which means that you can use it with pandas, polars, or any other dataframe library supported by narwhals.

    ### What's up with the name?

    In some sense, this library is just yet-another-wrapper around scikit-learn. But at the same time we've been noticing that a lot of the code in production feels complex and we're wondering if we can make it more fun. After all, work can be play too. So we're being very deliberate in not calling this library "scikit-<something>".

    ## Resources

    - [GitHub Repository](https://github.com/koaning/scikit-playtime)
    - [PyPI Package](https://pypi.org/project/scikit-playtime/)
    - [Documentation](https://koaning.github.io/playtime/)

    ## Made with Care

    This library is developed with care and consideration for the data science community. If you have suggestions or find bugs, please feel free to open an issue on GitHub!

    ---

    <div style="text-align: center; margin-top: 50px;">
    <img src="docs/imgs/calmcode-logo.webp" alt="CalmCode" width="150">
    <img src="docs/imgs/probabl.png" alt="Probabl" width="150">
    </div>
    """
    )
    return


if __name__ == "__main__":
    app.run()
