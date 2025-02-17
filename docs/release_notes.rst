Release Notes
=============

Some notes on new features in various releases

What's new in 0.6.0dev0
-----------------------

This is the current development version, these features are not yet available through PyPI.

^^^^^^^^^
Features:
^^^^^^^^^

* Added the :class:`~sklearn_genetic.callbacks.TimerStopping` callback to stop
  the iterations after a total (threshold) fitting time has been elapsed.
* Added new parallel coordinates plot in  :func:`~sklearn_genetic.plots.plot_parallel_coordinates`.
* Now if one or more callbacks decides to stop the algorithm, it will print
  its class name to know which callbacks were responsible of the stopping.
* Added support for extra methods coming from scikit-learn's BaseSearchCV, it is
  still partial support, missing properties like `cv_results_`, `best_index_` and `multimetric_`.

^^^^^^^^^^^^
API Changes:
^^^^^^^^^^^^

* The modules :mod:`~sklearn_genetic.plots` and :class:`~sklearn_genetic.mlflow.MLflowConfig`
  now requires an explicit installation of seaborn and mlflow, now those
  are optionally installed using ``pip install sklearn-genetic-opt[all].``

^^^^^
Docs:
^^^^^

* Edited all demos to be in the jupyter notebook format.
* Added embedded jupyter notebooks examples
* The modules of the package now have a summary of their classes/functions in the docs

What's new in 0.5.0
-------------------

^^^^^^^^^
Features:
^^^^^^^^^


* Build-in integration with MLflow using the :class:`~sklearn_genetic.mlflow.MLflowConfig`
  and the new parameter `log_config` from :class:`~sklearn_genetic.GASearchCV`

* Implemented the callback :class:`~sklearn_genetic.callbacks.LogbookSaver`
  which saves the estimator.logbook object with all the fitted hyperparameters
  and their cross-validation score

* Added the parameter `estimator` to all the functions on
  the module :mod:`~sklearn_genetic.callbacks`

^^^^^
Docs:
^^^^^

* Added user guide "Integrating with MLflow"
* Update the tutorial "Custom Callbacks" for new API inheritance behavior

^^^^^^^^^
Internal:
^^^^^^^^^

* Added a base class :class:`~sklearn_genetic.callbacks.base.BaseCallback` from
  which all Callbacks must inherit from
* Now coverage report doesn't take into account the lines with # pragma: no cover
  and # noqa

What's new in 0.4.1
-------------------

^^^^^
Docs:
^^^^^

* Added user guide on "Understanding the evaluation process"
* Several guides on contributing, code of conduct
* Added important links
* Docs requirement are now independent of package requirements

^^^^^^^^^
Internal:
^^^^^^^^^

* Changed test ci from travis to Github actions

What's new in 0.4
-----------------

^^^^^^^^^
Features:
^^^^^^^^^

* Implemented callbacks module to stop the optimization process based in the
  current iteration metrics, currently implemented:
  :class:`~sklearn_genetic.callbacks.ThresholdStopping` ,
  :class:`~sklearn_genetic.callbacks.ConsecutiveStopping`
  and :class:`~sklearn_genetic.callbacks.DeltaThreshold`.
* The algorithms 'eaSimple', 'eaMuPlusLambda', 'eaMuCommaLambda'
  are now implemented in the module :mod:`~sklearn_genetic.algorithms`
  for more control over their options, rather that taking the deap.algorithms module
* Implemented the :mod:`~sklearn_genetic.plots` module and added the function
  :func:`~sklearn_genetic.plots.plot_search_space`,
  this function plots a mixed counter, scatter and histogram plots
  over all the fitted hyperparameters and their cross-validation score
* Documentation based in rst with Sphinx to host in read the docs.
  It includes public classes and functions documentation as well
  as several tutorials on how to use the package
* Added `best_params_` and `best_estimator_` properties
  after fitting GASearchCV
* Added optional parameters `refit`, `pre_dispatch` and `error_score`


^^^^^^^^^^^^
API Changes:
^^^^^^^^^^^^

* Removed support for python 3.6, changed the libraries supported
  versions to be the same as scikit-learn current version
* Several internal changes on the documentation and variables naming
  style to be compatible with Sphinx
* Removed the parameters `continuous_parameters`, `categorical_parameters` and `integer_parameters`
  replacing them with `param_grid`

What's new in 0.3
-----------------

^^^^^^^^^
Features:
^^^^^^^^^

* Added the space module to control better the data
  types and ranges of each hyperparameter, their distribution to sample random values from,
  and merge all data types in one Space class that can work with the new param_grid parameter
* Changed the `continuous_parameters`, `categorical_parameters` and `integer_parameters`
  for the `param_grid`, the first ones still work but will be removed in a next version
* Added the option to use the eaMuCommaLambda algorithm from deap
* The `mu` and `lambda_` parameters of the internal eaMuPlusLambda and eaMuCommaLambda
  now are in terms of the initial population size and not the number of generations

What's new in 0.2
-----------------

^^^^^^^^^
Features:
^^^^^^^^^

* Enabled deap's eaMuPlusLambda algorithm for the optimization process, now is the default routine
* Added a logbook and history properties to the fitted GASearchCV  to make post-fit analysis
* ``Elitism=False`` now implements a roulette selection instead of ignoring the parameter
* Added the parameter keep_top_k to control the amount of solutions if the hall of fame (hof)

^^^^^^^^^^^^
API Changes:
^^^^^^^^^^^^

* Refactored the optimization algorithm to use DEAP package instead
  of a custom implementation, this causes the removal of several methods, properties and variables inside the GASearchCV class
* The parameter encoding_length has been removed, it's not longer required to the GASearchCV class
* Renamed the property of the fitted estimator from `best_params_` to `best_params`
* The verbosity now prints the deap log of the fitness function,
  it's standard deviation, max and min values from each generation
* The variable `GASearchCV._best_solutions` was removed and it's meant to be
  replaced with `GASearchCV.logbook` and `GASearchCV.history`
* Changed default parameters crossover_probability from 1 to 0.8 and generations from 50 to 40

What's new in 0.1
-----------------

^^^^^^^^^
Features:
^^^^^^^^^

* :class:`~sklearn_genetic.GASearchCV` for hyperparameters tuning
  using custom genetic algorithm for scikit-learn
  classification and regression models
* :func:`~sklearn_genetic.plots.plot_fitness_evolution` function to see the average
  fitness values over generations
