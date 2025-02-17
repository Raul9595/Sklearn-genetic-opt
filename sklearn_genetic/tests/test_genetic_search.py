import pytest
from sklearn.datasets import load_digits, load_boston
from sklearn.linear_model import SGDClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.utils.validation import check_is_fitted
from sklearn.tree import DecisionTreeRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score

from .. import GASearchCV
from ..space import Integer, Categorical, Continuous
from ..callbacks import (
    ThresholdStopping,
    DeltaThreshold,
    ConsecutiveStopping,
    TimerStopping,
)

data = load_digits()
label_names = data["target_names"]
y = data["target"]
X = data["data"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.33, random_state=42
)


def test_expected_ga_results():
    clf = SGDClassifier(loss="log", fit_intercept=True)
    generations = 8
    evolved_estimator = GASearchCV(
        clf,
        cv=3,
        scoring="accuracy",
        population_size=6,
        generations=generations,
        tournament_size=3,
        elitism=False,
        keep_top_k=4,
        param_grid={
            "l1_ratio": Continuous(0, 1),
            "alpha": Continuous(1e-4, 1, distribution="log-uniform"),
            "average": Categorical([True, False]),
            "max_iter": Integer(700, 1000),
        },
        verbose=False,
        algorithm="eaSimple",
        n_jobs=-1,
    )

    evolved_estimator.fit(X_train, y_train)

    assert check_is_fitted(evolved_estimator) is None
    assert "l1_ratio" in evolved_estimator.best_params_
    assert "alpha" in evolved_estimator.best_params_
    assert "average" in evolved_estimator.best_params_
    assert len(evolved_estimator) == generations + 1  # +1 random initial population
    assert len(evolved_estimator.predict(X_test)) == len(X_test)
    assert evolved_estimator.score(X_train, y_train) >= 0
    assert len(evolved_estimator.decision_function(X_test)) == len(X_test)
    assert len(evolved_estimator.predict_proba(X_test)) == len(X_test)
    assert len(evolved_estimator.predict_log_proba(X_test)) == len(X_test)
    assert evolved_estimator.score(X_test, y_test) == accuracy_score(
        y_test, evolved_estimator.predict(X_test)
    )
    assert bool(evolved_estimator.get_params())
    assert len(evolved_estimator.hof) == evolved_estimator.keep_top_k
    assert "gen" in evolved_estimator[0]
    assert "fitness_max" in evolved_estimator[0]
    assert "fitness" in evolved_estimator[0]
    assert "fitness_std" in evolved_estimator[0]
    assert "fitness_min" in evolved_estimator[0]


@pytest.mark.parametrize(
    "algorithm, callback",
    [
        ("eaSimple", ThresholdStopping(threshold=0.01)),
        ("eaMuPlusLambda", ThresholdStopping(threshold=0.01)),
        ("eaMuCommaLambda", ThresholdStopping(threshold=0.01)),
        ("eaSimple", TimerStopping(total_seconds=0.5)),
        ("eaMuPlusLambda", TimerStopping(total_seconds=2)),
        ("eaMuCommaLambda", TimerStopping(total_seconds=5)),
        ("eaSimple", ConsecutiveStopping(generations=5, metric="fitness")),
        ("eaMuPlusLambda", ConsecutiveStopping(generations=5, metric="fitness")),
        ("eaMuCommaLambda", ConsecutiveStopping(generations=5, metric="fitness")),
        ("eaSimple", DeltaThreshold(threshold=0.001, metric="fitness")),
        ("eaMuPlusLambda", DeltaThreshold(threshold=0.001, metric="fitness")),
        ("eaMuCommaLambda", DeltaThreshold(threshold=0.001, metric="fitness")),
        (
            "eaSimple",
            [
                ThresholdStopping(threshold=0.01),
                ConsecutiveStopping(generations=5, metric="fitness"),
                DeltaThreshold(threshold=0.001, metric="fitness"),
            ],
        ),
        (
            "eaMuPlusLambda",
            [
                ThresholdStopping(threshold=0.01),
                ConsecutiveStopping(generations=5, metric="fitness"),
                DeltaThreshold(threshold=0.001, metric="fitness"),
            ],
        ),
        (
            "eaMuCommaLambda",
            [
                ThresholdStopping(threshold=0.01),
                ConsecutiveStopping(generations=5, metric="fitness"),
                DeltaThreshold(threshold=0.001, metric="fitness"),
            ],
        ),
    ],
)
def test_expected_algorithms_callbacks(algorithm, callback):
    clf = SGDClassifier(loss="log", fit_intercept=True)
    generations = 8
    evolved_estimator = GASearchCV(
        clf,
        cv=2,
        scoring="accuracy",
        population_size=6,
        generations=generations,
        tournament_size=3,
        elitism=False,
        keep_top_k=4,
        param_grid={
            "l1_ratio": Continuous(0, 1),
            "alpha": Continuous(1e-4, 1, distribution="log-uniform"),
            "average": Categorical([True, False]),
            "max_iter": Integer(700, 1000),
        },
        verbose=True,
        algorithm=algorithm,
        n_jobs=-1,
    )

    evolved_estimator.fit(X_train, y_train, callbacks=callback)

    assert check_is_fitted(evolved_estimator) is None
    assert "l1_ratio" in evolved_estimator.best_params_
    assert "alpha" in evolved_estimator.best_params_
    assert "average" in evolved_estimator.best_params_
    assert len(evolved_estimator) <= generations + 1  # +1 random initial population
    assert len(evolved_estimator.predict(X_test)) == len(X_test)
    assert evolved_estimator.score(X_train, y_train) >= 0
    assert len(evolved_estimator.decision_function(X_test)) == len(X_test)
    assert len(evolved_estimator.predict_proba(X_test)) == len(X_test)
    assert len(evolved_estimator.predict_log_proba(X_test)) == len(X_test)
    assert evolved_estimator.score(X_test, y_test) == accuracy_score(
        y_test, evolved_estimator.predict(X_test)
    )
    assert bool(evolved_estimator.get_params())
    assert len(evolved_estimator.hof) <= evolved_estimator.keep_top_k
    assert "gen" in evolved_estimator[0]
    assert "fitness_max" in evolved_estimator[0]
    assert "fitness" in evolved_estimator[0]
    assert "fitness_std" in evolved_estimator[0]
    assert "fitness_min" in evolved_estimator[0]


@pytest.mark.parametrize(
    "param_grid",
    [
        (
            {
                "criterion": Categorical(["gini", "entropy"]),
                "max_depth": Integer(2, 20),
                "max_leaf_nodes": Integer(2, 30),
            }
        ),
        ({"ccp_alpha": Continuous(0.01, 0.5), "max_depth": Integer(2, 20)}),
        (
            {
                "ccp_alpha": Continuous(0.01, 0.5),
                "criterion": Categorical(["gini", "entropy"]),
            }
        ),
        (
            {
                "max_depth": Integer(2, 20),
                "max_leaf_nodes": Integer(2, 30),
            }
        ),
    ],
)
def test_missing_data_types(param_grid):
    clf = DecisionTreeClassifier()
    generations = 8
    evolved_estimator = GASearchCV(
        clf,
        cv=2,
        scoring="accuracy",
        population_size=5,
        generations=generations,
        tournament_size=3,
        elitism=True,
        param_grid=param_grid,
        verbose=False,
        n_jobs=-1,
    )

    evolved_estimator.fit(X_train, y_train)

    assert check_is_fitted(evolved_estimator) is None
    assert set(param_grid.keys()) == set(evolved_estimator.best_params_.keys())


def test_negative_criteria():
    data_boston = load_boston()

    y_boston = data_boston["target"]
    X_boston = data_boston["data"]

    X_train_b, X_test_b, y_train_b, y_test_b = train_test_split(
        X_boston, y_boston, test_size=0.33, random_state=42
    )

    clf = DecisionTreeRegressor()
    generations = 8
    evolved_estimator = GASearchCV(
        clf,
        cv=3,
        scoring="max_error",
        population_size=5,
        generations=generations,
        tournament_size=3,
        elitism=True,
        crossover_probability=0.9,
        mutation_probability=0.05,
        param_grid={
            "ccp_alpha": Continuous(0, 1),
            "criterion": Categorical(["mse", "mae"]),
            "max_depth": Integer(2, 20),
            "min_samples_split": Integer(2, 30),
        },
        criteria="min",
        n_jobs=-1,
    )

    evolved_estimator.fit(X_train_b, y_train_b)

    assert check_is_fitted(evolved_estimator) is None
    assert "ccp_alpha" in evolved_estimator.best_params_
    assert "criterion" in evolved_estimator.best_params_
    assert "max_depth" in evolved_estimator.best_params_
    assert "min_samples_split" in evolved_estimator.best_params_
    assert len(evolved_estimator.predict(X_test_b)) == len(X_test_b)
    assert evolved_estimator.score(X_train_b, y_train_b) <= 0


def test_wrong_criteria():
    clf = SGDClassifier(loss="log", fit_intercept=True)
    generations = 8
    with pytest.raises(Exception) as excinfo:
        evolved_estimator = GASearchCV(
            clf,
            cv=3,
            scoring="accuracy",
            population_size=5,
            generations=generations,
            tournament_size=3,
            elitism=False,
            param_grid={
                "l1_ratio": Continuous(0, 1),
                "alpha": Continuous(1e-4, 1),
                "average": Categorical([True, False]),
            },
            verbose=False,
            criteria="maximization",
        )
    assert (
        str(excinfo.value)
        == "Criteria must be one of ['max', 'min'], got maximization instead"
    )


def test_wrong_estimator():
    clf = KMeans()
    generations = 8
    with pytest.raises(Exception) as excinfo:
        evolved_estimator = GASearchCV(
            clf,
            cv=3,
            scoring="accuracy",
            population_size=5,
            generations=generations,
            tournament_size=3,
            elitism=False,
            param_grid={
                "l1_ratio": Continuous(0, 1),
                "alpha": Continuous(1e-4, 1),
                "average": Categorical([True, False]),
            },
            verbose=False,
            criteria="maximization",
        )
    assert (
        str(excinfo.value) == "KMeans() is not a valid Sklearn classifier or regressor"
    )


def test_wrong_get_item():
    clf = SGDClassifier(loss="log", fit_intercept=True)
    generations = 8
    evolved_estimator = GASearchCV(
        clf,
        cv=3,
        scoring="accuracy",
        population_size=5,
        generations=generations,
        tournament_size=3,
        elitism=False,
        param_grid={
            "l1_ratio": Continuous(0, 1),
            "alpha": Continuous(1e-4, 1),
            "average": Categorical([True, False]),
        },
        verbose=False,
        criteria="max",
    )
    with pytest.raises(Exception) as excinfo:
        value = evolved_estimator[0]
    assert (
        str(excinfo.value)
        == "This GASearchCV instance is not fitted yet or used refit=False. Call 'fit' with "
        "appropriate arguments before using this estimator."
    )


def test_iterator():
    clf = DecisionTreeClassifier()
    generations = 6
    evolved_estimator = GASearchCV(
        clf,
        cv=3,
        scoring="accuracy",
        population_size=5,
        generations=generations,
        tournament_size=3,
        elitism=True,
        param_grid={
            "min_weight_fraction_leaf": Continuous(0, 0.5),
            "max_depth": Integer(2, 20),
            "max_leaf_nodes": Integer(2, 30),
        },
        verbose=False,
        n_jobs=-1,
    )
    evolved_estimator.fit(X_train, y_train)

    i = iter(evolved_estimator)
    assert next(i) == evolved_estimator[0]
    assert next(i) == evolved_estimator[1]


def test_wrong_algorithm():
    clf = SGDClassifier(loss="log", fit_intercept=True)
    generations = 6
    evolved_estimator = GASearchCV(
        clf,
        cv=3,
        scoring="accuracy",
        population_size=5,
        generations=generations,
        tournament_size=3,
        elitism=False,
        param_grid={
            "l1_ratio": Continuous(0, 1),
            "alpha": Continuous(1e-4, 1),
            "average": Categorical([True, False]),
        },
        verbose=False,
        criteria="max",
        algorithm="genetic",
    )
    with pytest.raises(Exception) as excinfo:
        evolved_estimator.fit(X_train, y_train)
    assert (
        str(excinfo.value)
        == "The algorithm genetic is not supported, please select one from ['eaSimple', 'eaMuPlusLambda', 'eaMuCommaLambda']"
    )


def test_no_param_grid():
    clf = SGDClassifier(loss="log", fit_intercept=True)
    generations = 8
    with pytest.raises(Exception) as excinfo:
        evolved_estimator = GASearchCV(
            clf,
            cv=3,
            scoring="accuracy",
            population_size=12,
            generations=generations,
            tournament_size=3,
            elitism=False,
            verbose=False,
            criteria="max",
        )

    assert str(excinfo.value) == "param_grid can not be empty"
