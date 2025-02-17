from datetime import datetime
import random

import numpy as np
from deap import base, creator, tools
from sklearn.base import clone
from sklearn.model_selection import cross_val_score
from sklearn.base import is_classifier, is_regressor
from sklearn.utils.metaestimators import if_delegate_has_method
from sklearn.utils.validation import check_is_fitted
from sklearn.metrics import check_scoring
from sklearn.exceptions import NotFittedError
from sklearn.model_selection._search import BaseSearchCV

from .parameters import Algorithms, Criteria
from .space import Space
from .algorithms import eaSimple, eaMuPlusLambda, eaMuCommaLambda
from .callbacks.validations import check_callback


class GASearchCV(BaseSearchCV):
    """
    Evolutionary optimization over hyperparameters.

    GASearchCV implements a "fit" and a "score" method.
    It also implements "predict", "predict_proba", "decision_function",
    "predict_log_proba" if they are implemented in the
    estimator used.
    The parameters of the estimator used to apply these methods are optimized
    by cross-validated search over parameter settings.

    Parameters
    ----------
    estimator : estimator object, default=None
        estimator object implementing 'fit'
        The object to use to fit the data.

    cv : int, cross-validation generator or an iterable, default=None
        Determines the cross-validation splitting strategy.
        Possible inputs for cv are:
        - None, to use the default 5-fold cross validation,
        - int, to specify the number of folds in a `(Stratified)KFold`,
        - CV splitter,
        - An iterable yielding (train, test) splits as arrays of indices.
        For int/None inputs, if the estimator is a classifier and ``y`` is
        either binary or multiclass, :class:`StratifiedKFold` is used. In all
        other cases, :class:`KFold` is used. These splitters are instantiated
        with `shuffle=False` so the splits will be the same across calls.

    param_grid : dict, default=None
        Grid with the parameters to tune, expects keys a valid name
        of hyperparameter based on the estimator selected and as values
        one of :class:`~sklearn_genetic.space.Integer` ,
        :class:`~sklearn_genetic.space.Categorical`
        :class:`~sklearn_genetic.space.Continuous` classes

    population_size : int, default=10
        Size of the initial population to sample randomly generated individuals.

    generations : int, default=40
        Number of generations or iterations to run the evolutionary algorithm.

    crossover_probability : float, default=0.8
        Probability of crossover operation between two individuals.

    mutation_probability : float, default=0.1
        Probability of child mutation.

    tournament_size : int, default=3
        Number of individuals to perform tournament selection.

    elitism : bool, default=True
        If True takes the *tournament_size* best solution to the next generation.

    scoring : str or callable, default=None
        A str (see model evaluation documentation) or
        a scorer callable object / function with signature
        ``scorer(estimator, X, y)`` which should return only
        a single value.

    n_jobs : int, default=None
        Number of jobs to run in parallel. Training the estimator and computing
        the score are parallelized over the cross-validation splits.
        ``None`` means 1 unless in a :obj:`joblib.parallel_backend` context.
        ``-1`` means using all processors.

    verbose : bool, default=True
        If ``True``, shows the metrics on the optimization routine.

    keep_top_k : int, default=1
        Number of best solutions to keep in the hof object. If a callback stops the algorithm before k iterations,
        it will return only one set of parameters per iteration.

    criteria : {'max', 'min'} , default='max'
        ``max`` if a higher scoring metric is better, ``min`` otherwise.

    algorithm : {'eaMuPlusLambda', 'eaMuCommaLambda', 'eaSimple'}, default='eaMuPlusLambda'
        Evolutionary algorithm to use.
        See more details in the deap algorithms documentation.

    refit : bool, default=True
        Refit an estimator using the best found parameters on the whole dataset.
        If ``False``, it is not possible to make predictions
        using this GASearchCV instance after fitting.

    pre_dispatch : int or str, default='2*n_jobs'
        Controls the number of jobs that get dispatched during parallel
        execution. Reducing this number can be useful to avoid an
        explosion of memory consumption when more jobs get dispatched
        than CPUs can process. This parameter can be:
            - None, in which case all the jobs are immediately
              created and spawned. Use this for lightweight and
              fast-running jobs, to avoid delays due to on-demand
              spawning of the jobs
            - An int, giving the exact number of total jobs that are
              spawned
            - A str, giving an expression as a function of n_jobs,
              as in '2*n_jobs'

    error_score : 'raise' or numeric, default=np.nan
        Value to assign to the score if an error occurs in estimator fitting.
        If set to ``'raise'``, the error is raised.
        If a numeric value is given, FitFailedWarning is raised.

    log_config : :class:`~sklearn_genetic.mlflow.MLflowConfig`, default = None
        Configuration to log metrics and models to mlflow, of None,
        no mlflow logging will be performed

    Attributes
    ----------

    logbook : :class:`DEAP.tools.Logbook`
        Contains the logs of every set of hyperparameters fitted with its average scoring metric.
    history : dict
        Dictionary of the form:
        {"gen": [],
        "fitness": [],
        "fitness_std": [],
        "fitness_max": [],
        "fitness_min": []}

         *gen* returns the index of the evaluated generations.
         Each entry on the others lists, represent the average metric in each generation.

    best_estimator_ : estimator
        Estimator that was chosen by the search, i.e. estimator
        which gave highest score
        on the left out data. Not available if ``refit=False``.

    best_params_ : dict
        Parameter setting that gave the best results on the hold out data.

    """

    def __init__(
        self,
        estimator,
        cv=3,
        param_grid=None,
        scoring=None,
        population_size=10,
        generations=40,
        crossover_probability=0.8,
        mutation_probability=0.1,
        tournament_size=3,
        elitism=True,
        verbose=True,
        keep_top_k=1,
        criteria="max",
        algorithm="eaMuPlusLambda",
        refit=True,
        n_jobs=1,
        pre_dispatch="2*n_jobs",
        error_score=np.nan,
        log_config=None,
    ):

        self.estimator = clone(estimator)
        self.toolbox = base.Toolbox()
        self.cv = cv
        self.scoring = scoring
        self.population_size = population_size
        self.generations = generations
        self.crossover_probability = crossover_probability
        self.mutation_probability = mutation_probability
        self.tournament_size = tournament_size
        self.elitism = elitism
        self.verbose = verbose
        self.keep_top_k = keep_top_k
        self.criteria = criteria
        self.param_grid = param_grid
        self.algorithm = algorithm
        self.refit = refit
        self.n_jobs = n_jobs
        self.pre_dispatch = pre_dispatch
        self.error_score = error_score
        self.creator = creator
        self.logbook = None
        self.history = None
        self._n_iterations = self.generations + 1
        self.X_ = None
        self.y_ = None
        self.callbacks = None
        self.best_params_ = None
        self.best_estimator_ = None
        self._pop = None
        self._stats = None
        self._hof = None
        self.hof = None
        self.X_predict = None
        self.scorer_ = None
        self.cv_results_ = None
        self.best_index_ = None
        self.multimetric_ = False
        self.log_config = log_config
        self._initial_training_time = None

        # Check that the estimator is compatible with scikit-learn
        if not is_classifier(self.estimator) and not is_regressor(self.estimator):
            raise ValueError(
                f"{self.estimator} is not a valid Sklearn classifier or regressor"
            )

        if criteria not in Criteria.list():
            raise ValueError(
                f"Criteria must be one of {Criteria.list()}, got {criteria} instead"
            )
        # Minimization is handle like an optimization problem with a change in the score sign
        elif criteria == Criteria.max.value:
            self.criteria_sign = 1
        elif criteria == Criteria.min.value:
            self.criteria_sign = -1

        # Saves the param_grid and computes some extra properties in the same object
        self.space = Space(param_grid)

        super(GASearchCV, self).__init__(
            estimator=estimator,
            scoring=scoring,
            n_jobs=n_jobs,
            refit=refit,
            cv=cv,
            verbose=verbose,
            pre_dispatch=pre_dispatch,
            error_score=error_score,
        )

    def _register(self):
        """
        This function is the responsible for registering the DEAPs necessary methods
        and create other objects to hold the hof, logbook and stats.
        """

        self.creator.create("FitnessMax", base.Fitness, weights=[1.0])
        self.creator.create("Individual", list, fitness=creator.FitnessMax)

        attributes = []
        # Assign all the parameters defined in the param_grid
        # It uses the distribution parameter to set the sampling function
        for parameter, dimension in self.space.param_grid.items():
            self.toolbox.register(f"{parameter}", dimension.sample)
            attributes.append(getattr(self.toolbox, parameter))

        IND_SIZE = 1

        self.toolbox.register(
            "individual",
            tools.initCycle,
            creator.Individual,
            tuple(attributes),
            n=IND_SIZE,
        )

        self.toolbox.register(
            "population", tools.initRepeat, list, self.toolbox.individual
        )

        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", self.mutate)
        if self.elitism:
            self.toolbox.register(
                "select", tools.selTournament, tournsize=self.tournament_size
            )
        else:
            self.toolbox.register("select", tools.selRoulette)

        self.toolbox.register("evaluate", self.evaluate)

        self._pop = self.toolbox.population(n=self.population_size)
        self._hof = tools.HallOfFame(self.keep_top_k)

        self._stats = tools.Statistics(lambda ind: ind.fitness.values)
        self._stats.register("fitness", np.mean)
        self._stats.register("fitness_std", np.std)
        self._stats.register("fitness_max", np.max)
        self._stats.register("fitness_min", np.min)

        self.logbook = tools.Logbook()

    def mutate(self, individual):
        """
        This function is responsible of changed a randomly selected parameter from an individual
        Parameters
        ----------
        individual: Individual object
            The individual (set of hyperparameters) that is being generated

        Returns
        -------
            Mutated individual
        """

        # Randomly select one of the hyperparameters
        gen = random.randrange(0, len(self.space))
        parameter_idx = self.space.parameters[gen]
        parameter = self.space[parameter_idx]

        # Using the defined distribution from the para_grid value
        # Make a random sample of the parameter
        individual[gen] = parameter.sample()

        return [individual]

    def evaluate(self, individual):
        """
        Compute the cross-validation scores and record the logbook and mlflow (if specified)
        Parameters
        ----------
        individual: Individual object
            The individual (set of hyperparameters) that is being evaluated

        Returns
        -------
            The fitness value of the estimator candidate, corresponding to the cv-score with the criteria sing

        """

        # Dictionary representation of the individual with key-> hyperparameter name, value -> value
        current_generation_params = {
            key: individual[n] for n, key in enumerate(self.space.parameters)
        }

        local_estimator = clone(self.estimator)
        local_estimator.set_params(**current_generation_params)

        # Compute the cv-score
        cv_scores = cross_val_score(
            local_estimator,
            self.X_,
            self.y_,
            cv=self.cv,
            scoring=self.scoring,
            n_jobs=self.n_jobs,
            pre_dispatch=self.pre_dispatch,
            error_score=self.error_score,
        )

        score = np.mean(cv_scores)

        # Uses the log config to save in remote log server (e.g MLflow)
        if self.log_config is not None:
            self.log_config.create_run(
                parameters=current_generation_params,
                score=score,
                estimator=local_estimator,
            )

        current_generation_params["score"] = score

        # Log the hyperparameters and the cv-score
        self.logbook.record(parameters=current_generation_params)

        return [self.criteria_sign * score]

    @if_delegate_has_method(delegate="estimator")
    def fit(self, X, y, callbacks=None):
        """
        Main method of GASearchCV, starts the optimization
        procedure with the hyperparameters of the given estimator

        Parameters
        ----------

        X : array-like of shape (n_samples, n_features)
            The data to fit. Can be for example a list, or an array.
        y : array-like of shape (n_samples,) or (n_samples, n_outputs), \
            default=None
            The target variable to try to predict in the case of
            supervised learning.
        callbacks: list or callable
            One or a list of the callbacks methods available in
            :class:`~sklearn_genetic.callbacks`.
            The callback is evaluated after fitting the estimators from the generation 1.

        """

        self.X_ = X
        self.y_ = y

        # Make sure the callbacks are valid
        self.callbacks = check_callback(callbacks)
        self.scorer_ = check_scoring(self.estimator, scoring=self.scoring)

        # Set the DEAPs necessary methods
        self._register()

        self._initial_training_time = datetime.utcnow()

        # Optimization routine from the selected evolutionary algorithm
        pop, log, n_gen = self._select_algorithm(
            pop=self._pop, stats=self._stats, hof=self._hof
        )

        # Update the _n_iterations value as the algorithm could stop earlier due a callback
        self._n_iterations = n_gen

        # hof keeps the best params according to the fitness value
        # The best one is in the position 0
        self.best_params_ = {
            key: self._hof[0][n] for n, key in enumerate(self.space.parameters)
        }

        self.hof = {
            k: {key: self._hof[k][n] for n, key in enumerate(self.space.parameters)}
            for k in range(len(self._hof))
        }

        self.history = {
            "gen": log.select("gen"),
            "fitness": log.select("fitness"),
            "fitness_std": log.select("fitness_std"),
            "fitness_max": log.select("fitness_max"),
            "fitness_min": log.select("fitness_min"),
        }

        # Imitate the logic of scikit-learn refit parameter
        if self.refit:
            self.estimator.set_params(**self.best_params_)
            self.estimator.fit(self.X_, self.y_)
            self.best_estimator_ = self.estimator

        del self.creator.FitnessMax
        del self.creator.Individual

        return self

    def _select_algorithm(self, pop, stats, hof):
        """
        It selects the algorithm to run from the sklearn_genetic.algorithms module
        based in the parameter self.algorithm.

        Parameters
        ----------
        pop: pop object from DEAP
        stats: stats object from DEAP
        hof: hof object from DEAP

        Returns
        -------
        pop: pop object
            The last evaluated population
        log: Logbook object
            It contains the calculated metrics {'fitness', 'fitness_std', 'fitness_max', 'fitness_min'}
            the number of generations and the number of evaluated individuals per generation
        n_gen: int
            The number of generations that the evolutionary algorithm ran
        """

        if self.algorithm == Algorithms.eaSimple.value:

            pop, log, gen = eaSimple(
                pop,
                self.toolbox,
                cxpb=self.crossover_probability,
                stats=stats,
                mutpb=self.mutation_probability,
                ngen=self.generations,
                halloffame=hof,
                callbacks=self.callbacks,
                verbose=self.verbose,
                estimator=self,
            )

        elif self.algorithm == Algorithms.eaMuPlusLambda.value:

            pop, log, gen = eaMuPlusLambda(
                pop,
                self.toolbox,
                mu=self.population_size,
                lambda_=2 * self.population_size,
                cxpb=self.crossover_probability,
                stats=stats,
                mutpb=self.mutation_probability,
                ngen=self.generations,
                halloffame=hof,
                callbacks=self.callbacks,
                verbose=self.verbose,
                estimator=self,
            )

        elif self.algorithm == Algorithms.eaMuCommaLambda.value:
            pop, log, gen = eaMuCommaLambda(
                pop,
                self.toolbox,
                mu=self.population_size,
                lambda_=2 * self.population_size,
                cxpb=self.crossover_probability,
                stats=stats,
                mutpb=self.mutation_probability,
                ngen=self.generations,
                halloffame=hof,
                callbacks=self.callbacks,
                verbose=self.verbose,
                estimator=self,
            )

        else:
            raise ValueError(
                f"The algorithm {self.algorithm} is not supported, "
                f"please select one from {Algorithms.list()}"
            )

        return pop, log, gen

    def _run_search(self, evaluate_candidates):
        pass  # noqa

    @property
    def _fitted(self):
        try:
            check_is_fitted(self.estimator)
            is_fitted = True
        except Exception as e:
            is_fitted = False

        has_history = bool(self.history)
        return all([is_fitted, has_history, self.refit])

    def __getitem__(self, index):
        """

        Parameters
        ----------
        index: slice required to get

        Returns
        -------
        Best solution of the iteration corresponding to the index number
        """
        if not self._fitted:
            raise NotFittedError(
                f"This GASearchCV instance is not fitted yet "
                f"or used refit=False. Call 'fit' with appropriate "
                f"arguments before using this estimator."
            )

        return {
            "gen": self.history["gen"][index],
            "fitness": self.history["fitness"][index],
            "fitness_std": self.history["fitness_std"][index],
            "fitness_max": self.history["fitness_max"][index],
            "fitness_min": self.history["fitness_min"][index],
        }

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        """
        Returns
        -------
        Iteration over the statistics found in each generation
        """
        if self.n < self._n_iterations + 1:
            result = self.__getitem__(self.n)
            self.n += 1
            return result
        else:
            raise StopIteration  # pragma: no cover

    def __len__(self):
        """
        Returns
        -------
        Number of generations fitted if .fit method has been called,
        self.generations otherwise
        """
        return self._n_iterations
